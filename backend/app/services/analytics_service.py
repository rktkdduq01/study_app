from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import pandas as pd
import numpy as np
from collections import defaultdict

from ..models.analytics import (
    UserActivity, LearningProgress, PerformanceMetric,
    GameplayAnalytics, ContentEffectiveness, UserEngagement,
    AggregatedMetrics, AnalyticsEvent
)
from ..models.user import User
from ..models.quest import Quest
from ..models.content import Content
from ..models.subject import Subject
from ..core.redis_client import redis_client
import json

class AnalyticsService:
    def __init__(self):
        self.redis_client = redis_client
        
    async def track_event(
        self,
        event_name: str,
        event_category: str,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        properties: Optional[Dict] = None,
        db: Session = None
    ) -> AnalyticsEvent:
        """Track a custom analytics event"""
        event = AnalyticsEvent(
            event_name=event_name,
            event_category=event_category,
            user_id=user_id,
            session_id=session_id,
            properties=properties or {}
        )
        
        db.add(event)
        db.commit()
        
        # Also push to Redis for real-time processing
        event_data = {
            "event_name": event_name,
            "event_category": event_category,
            "user_id": user_id,
            "session_id": session_id,
            "properties": properties,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.redis_client.lpush(
            "analytics:events",
            json.dumps(event_data)
        )
        
        return event
    
    async def track_user_activity(
        self,
        user_id: int,
        activity_type: str,
        activity_data: Dict = None,
        duration_seconds: int = 0,
        ip_address: str = None,
        user_agent: str = None,
        db: Session = None
    ) -> UserActivity:
        """Track user activity"""
        activity = UserActivity(
            user_id=user_id,
            activity_type=activity_type,
            activity_data=activity_data or {},
            duration_seconds=duration_seconds,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.add(activity)
        db.commit()
        
        # Update real-time metrics
        await self._update_real_time_metrics(user_id, activity_type)
        
        return activity
    
    async def update_learning_progress(
        self,
        user_id: int,
        subject_id: int,
        content_id: Optional[int] = None,
        quest_id: Optional[int] = None,
        progress_percentage: float = 0.0,
        time_spent: int = 0,
        score: Optional[float] = None,
        completed: bool = False,
        db: Session = None
    ) -> LearningProgress:
        """Update or create learning progress"""
        # Try to find existing progress
        progress = db.query(LearningProgress).filter(
            and_(
                LearningProgress.user_id == user_id,
                LearningProgress.subject_id == subject_id,
                LearningProgress.content_id == content_id,
                LearningProgress.quest_id == quest_id
            )
        ).first()
        
        if progress:
            progress.progress_percentage = max(progress.progress_percentage, progress_percentage)
            progress.time_spent_seconds += time_spent
            progress.attempts += 1
            if score is not None:
                progress.score = score
            if completed:
                progress.completed = True
                progress.completed_at = datetime.utcnow()
        else:
            progress = LearningProgress(
                user_id=user_id,
                subject_id=subject_id,
                content_id=content_id,
                quest_id=quest_id,
                progress_percentage=progress_percentage,
                time_spent_seconds=time_spent,
                attempts=1,
                score=score,
                completed=completed,
                completed_at=datetime.utcnow() if completed else None
            )
            db.add(progress)
        
        db.commit()
        return progress
    
    async def calculate_performance_metrics(
        self,
        user_id: int,
        period_type: str = "daily",
        db: Session = None
    ) -> List[PerformanceMetric]:
        """Calculate and store performance metrics"""
        metrics = []
        period_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Calculate accuracy
        recent_progress = db.query(LearningProgress).filter(
            LearningProgress.user_id == user_id,
            LearningProgress.updated_at >= period_date
        ).all()
        
        if recent_progress:
            scores = [p.score for p in recent_progress if p.score is not None]
            if scores:
                accuracy = np.mean(scores)
                metrics.append(PerformanceMetric(
                    user_id=user_id,
                    metric_type="accuracy",
                    metric_value=accuracy,
                    period_type=period_type,
                    period_date=period_date
                ))
        
        # Calculate engagement
        activities = db.query(UserActivity).filter(
            UserActivity.user_id == user_id,
            UserActivity.created_at >= period_date
        ).count()
        
        metrics.append(PerformanceMetric(
            user_id=user_id,
            metric_type="engagement",
            metric_value=activities,
            period_type=period_type,
            period_date=period_date
        ))
        
        # Calculate speed (average time per content)
        if recent_progress:
            times = [p.time_spent_seconds for p in recent_progress if p.time_spent_seconds > 0]
            if times:
                avg_time = np.mean(times)
                metrics.append(PerformanceMetric(
                    user_id=user_id,
                    metric_type="speed",
                    metric_value=avg_time,
                    period_type=period_type,
                    period_date=period_date
                ))
        
        # Save all metrics
        for metric in metrics:
            db.add(metric)
        db.commit()
        
        return metrics
    
    async def get_user_analytics(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        db: Session
    ) -> Dict[str, Any]:
        """Get comprehensive analytics for a user"""
        analytics = {
            "user_id": user_id,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }
        
        # Learning progress
        progress = db.query(LearningProgress).filter(
            LearningProgress.user_id == user_id,
            LearningProgress.updated_at.between(start_date, end_date)
        ).all()
        
        analytics["learning_progress"] = {
            "total_items": len(progress),
            "completed_items": len([p for p in progress if p.completed]),
            "average_score": np.mean([p.score for p in progress if p.score]) if progress else 0,
            "total_time_spent": sum(p.time_spent_seconds for p in progress),
            "subjects": defaultdict(dict)
        }
        
        # Group by subject
        for p in progress:
            subject_id = p.subject_id
            if subject_id not in analytics["learning_progress"]["subjects"]:
                analytics["learning_progress"]["subjects"][subject_id] = {
                    "completed": 0,
                    "in_progress": 0,
                    "total_time": 0,
                    "average_score": []
                }
            
            subject_stats = analytics["learning_progress"]["subjects"][subject_id]
            if p.completed:
                subject_stats["completed"] += 1
            else:
                subject_stats["in_progress"] += 1
            subject_stats["total_time"] += p.time_spent_seconds
            if p.score:
                subject_stats["average_score"].append(p.score)
        
        # Calculate averages
        for subject_id, stats in analytics["learning_progress"]["subjects"].items():
            if stats["average_score"]:
                stats["average_score"] = np.mean(stats["average_score"])
            else:
                stats["average_score"] = 0
        
        # Activity patterns
        activities = db.query(UserActivity).filter(
            UserActivity.user_id == user_id,
            UserActivity.created_at.between(start_date, end_date)
        ).all()
        
        activity_by_type = defaultdict(int)
        activity_by_hour = defaultdict(int)
        activity_by_day = defaultdict(int)
        
        for activity in activities:
            activity_by_type[activity.activity_type] += 1
            activity_by_hour[activity.created_at.hour] += 1
            activity_by_day[activity.created_at.weekday()] += 1
        
        analytics["activity_patterns"] = {
            "by_type": dict(activity_by_type),
            "by_hour": dict(activity_by_hour),
            "by_day": dict(activity_by_day),
            "total_activities": len(activities)
        }
        
        # Performance metrics
        metrics = db.query(PerformanceMetric).filter(
            PerformanceMetric.user_id == user_id,
            PerformanceMetric.period_date.between(start_date, end_date)
        ).all()
        
        metrics_by_type = defaultdict(list)
        for metric in metrics:
            metrics_by_type[metric.metric_type].append({
                "value": metric.metric_value,
                "date": metric.period_date.isoformat()
            })
        
        analytics["performance_metrics"] = dict(metrics_by_type)
        
        # Engagement metrics
        engagement = db.query(UserEngagement).filter(
            UserEngagement.user_id == user_id,
            UserEngagement.date.between(start_date, end_date)
        ).all()
        
        if engagement:
            analytics["engagement"] = {
                "total_login_count": sum(e.login_count for e in engagement),
                "total_active_minutes": sum(e.active_minutes for e in engagement),
                "lessons_completed": sum(e.lessons_completed for e in engagement),
                "quests_completed": sum(e.quests_completed for e in engagement),
                "achievements_earned": sum(e.achievements_earned for e in engagement),
                "average_daily_minutes": np.mean([e.active_minutes for e in engagement]),
                "max_streak": max(e.streak_days for e in engagement) if engagement else 0
            }
        
        return analytics
    
    async def get_content_effectiveness(
        self,
        content_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """Analyze content effectiveness"""
        # Get or create effectiveness record
        effectiveness = db.query(ContentEffectiveness).filter(
            ContentEffectiveness.content_id == content_id
        ).first()
        
        if not effectiveness:
            effectiveness = ContentEffectiveness(content_id=content_id)
            db.add(effectiveness)
        
        # Calculate metrics
        progress_records = db.query(LearningProgress).filter(
            LearningProgress.content_id == content_id
        ).all()
        
        if progress_records:
            effectiveness.view_count = len(progress_records)
            effectiveness.completion_count = len([p for p in progress_records if p.completed])
            
            scores = [p.score for p in progress_records if p.score is not None]
            if scores:
                effectiveness.average_score = np.mean(scores)
            
            times = [p.time_spent_seconds for p in progress_records if p.time_spent_seconds > 0]
            if times:
                effectiveness.average_time_seconds = int(np.mean(times))
            
            effectiveness.engagement_rate = (effectiveness.completion_count / effectiveness.view_count) * 100
            
            # Calculate effectiveness score (custom formula)
            if effectiveness.average_score and effectiveness.engagement_rate:
                effectiveness.effectiveness_score = (
                    effectiveness.average_score * 0.6 +
                    effectiveness.engagement_rate * 0.4
                )
        
        effectiveness.last_calculated = datetime.utcnow()
        db.commit()
        
        return {
            "content_id": content_id,
            "view_count": effectiveness.view_count,
            "completion_count": effectiveness.completion_count,
            "completion_rate": (effectiveness.completion_count / effectiveness.view_count * 100) if effectiveness.view_count > 0 else 0,
            "average_score": effectiveness.average_score,
            "average_time_seconds": effectiveness.average_time_seconds,
            "engagement_rate": effectiveness.engagement_rate,
            "effectiveness_score": effectiveness.effectiveness_score,
            "last_updated": effectiveness.last_calculated.isoformat()
        }
    
    async def get_global_analytics(
        self,
        start_date: datetime,
        end_date: datetime,
        db: Session
    ) -> Dict[str, Any]:
        """Get platform-wide analytics"""
        analytics = {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }
        
        # Active users
        active_users = db.query(UserActivity.user_id).filter(
            UserActivity.created_at.between(start_date, end_date)
        ).distinct().count()
        
        analytics["users"] = {
            "active": active_users,
            "total": db.query(User).count(),
            "new": db.query(User).filter(
                User.created_at.between(start_date, end_date)
            ).count()
        }
        
        # Content statistics
        total_content = db.query(Content).count()
        content_views = db.query(LearningProgress).filter(
            LearningProgress.created_at.between(start_date, end_date)
        ).count()
        
        analytics["content"] = {
            "total": total_content,
            "views": content_views,
            "completions": db.query(LearningProgress).filter(
                LearningProgress.completed == True,
                LearningProgress.completed_at.between(start_date, end_date)
            ).count()
        }
        
        # Quest statistics
        analytics["quests"] = {
            "total": db.query(Quest).count(),
            "completed": db.query(LearningProgress).filter(
                LearningProgress.quest_id.isnot(None),
                LearningProgress.completed == True,
                LearningProgress.completed_at.between(start_date, end_date)
            ).count()
        }
        
        # Top performing content
        top_content = db.query(
            ContentEffectiveness.content_id,
            ContentEffectiveness.effectiveness_score
        ).order_by(
            ContentEffectiveness.effectiveness_score.desc()
        ).limit(10).all()
        
        analytics["top_content"] = [
            {"content_id": c[0], "score": c[1]} for c in top_content
        ]
        
        # Activity trends
        daily_activities = db.query(
            func.date(UserActivity.created_at).label("date"),
            func.count(UserActivity.id).label("count")
        ).filter(
            UserActivity.created_at.between(start_date, end_date)
        ).group_by(
            func.date(UserActivity.created_at)
        ).all()
        
        analytics["activity_trend"] = [
            {"date": str(a.date), "count": a.count} for a in daily_activities
        ]
        
        return analytics
    
    async def generate_report(
        self,
        report_type: str,
        start_date: datetime,
        end_date: datetime,
        filters: Optional[Dict] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Generate comprehensive report"""
        report = {
            "type": report_type,
            "generated_at": datetime.utcnow().isoformat(),
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "filters": filters or {}
        }
        
        if report_type == "user":
            if filters and "user_id" in filters:
                report["data"] = await self.get_user_analytics(
                    filters["user_id"], start_date, end_date, db
                )
        elif report_type == "global":
            report["data"] = await self.get_global_analytics(
                start_date, end_date, db
            )
        elif report_type == "content":
            # Content effectiveness report
            all_content = db.query(Content).all()
            content_reports = []
            
            for content in all_content:
                effectiveness = await self.get_content_effectiveness(
                    content.id, db
                )
                effectiveness["title"] = content.title
                content_reports.append(effectiveness)
            
            report["data"] = {
                "content_effectiveness": content_reports,
                "summary": {
                    "total_content": len(content_reports),
                    "average_effectiveness": np.mean([
                        c["effectiveness_score"] for c in content_reports 
                        if c["effectiveness_score"]
                    ]) if content_reports else 0
                }
            }
        
        return report
    
    async def _update_real_time_metrics(
        self,
        user_id: int,
        activity_type: str
    ):
        """Update real-time metrics in Redis"""
        # Update user activity count
        await self.redis_client.hincrby(
            f"analytics:user:{user_id}:today",
            activity_type,
            1
        )
        
        # Update global activity count
        await self.redis_client.hincrby(
            "analytics:global:today",
            activity_type,
            1
        )
        
        # Set expiry for daily metrics
        await self.redis_client.expire(
            f"analytics:user:{user_id}:today",
            86400  # 24 hours
        )
        await self.redis_client.expire(
            "analytics:global:today",
            86400
        )
    
    async def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time metrics from Redis"""
        # Get global metrics
        global_metrics = await self.redis_client.hgetall("analytics:global:today")
        
        # Get active users count
        active_users = await self.redis_client.scard("analytics:active_users:today")
        
        # Get recent events
        recent_events = await self.redis_client.lrange("analytics:events", 0, 9)
        
        return {
            "global_activity": {k.decode(): int(v) for k, v in global_metrics.items()},
            "active_users": active_users,
            "recent_events": [json.loads(e) for e in recent_events]
        }

# Singleton instance
analytics_service = AnalyticsService()