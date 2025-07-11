from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

from ..models.analytics import (
    UserActivity, LearningProgress, PerformanceMetric,
    GameplayAnalytics, UserEngagement, AggregatedMetrics
)
from ..models.user import User
from ..models.quest import Quest, QuestProgress
from ..models.achievement import Achievement, UserAchievement
from ..models.character import Character
from ..database import SessionLocal
from ..core.redis_client import redis_client

logger = logging.getLogger(__name__)

class DataAggregationService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.redis_client = redis_client
        self._setup_scheduled_jobs()
    
    def _setup_scheduled_jobs(self):
        """Setup scheduled aggregation jobs"""
        # Hourly aggregation
        self.scheduler.add_job(
            self.aggregate_hourly_metrics,
            CronTrigger(minute=5),  # Run at 5 minutes past every hour
            id="hourly_aggregation"
        )
        
        # Daily aggregation
        self.scheduler.add_job(
            self.aggregate_daily_metrics,
            CronTrigger(hour=1, minute=0),  # Run at 1:00 AM daily
            id="daily_aggregation"
        )
        
        # Weekly aggregation
        self.scheduler.add_job(
            self.aggregate_weekly_metrics,
            CronTrigger(day_of_week=1, hour=2, minute=0),  # Run on Monday at 2:00 AM
            id="weekly_aggregation"
        )
        
        # Monthly aggregation
        self.scheduler.add_job(
            self.aggregate_monthly_metrics,
            CronTrigger(day=1, hour=3, minute=0),  # Run on 1st of month at 3:00 AM
            id="monthly_aggregation"
        )
    
    def start(self):
        """Start the scheduler"""
        self.scheduler.start()
        logger.info("Data aggregation scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("Data aggregation scheduler stopped")
    
    async def aggregate_hourly_metrics(self):
        """Aggregate metrics on an hourly basis"""
        db = SessionLocal()
        try:
            now = datetime.utcnow()
            hour_start = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
            hour_end = hour_start + timedelta(hours=1)
            
            logger.info(f"Starting hourly aggregation for {hour_start} to {hour_end}")
            
            # Aggregate user activities
            activities = db.query(
                UserActivity.user_id,
                UserActivity.activity_type,
                func.count(UserActivity.id).label("count"),
                func.sum(UserActivity.duration_seconds).label("total_duration")
            ).filter(
                UserActivity.created_at.between(hour_start, hour_end)
            ).group_by(
                UserActivity.user_id,
                UserActivity.activity_type
            ).all()
            
            # Store aggregated metrics
            for activity in activities:
                metric = AggregatedMetrics(
                    metric_name=f"activity_{activity.activity_type}",
                    metric_value=activity.count,
                    dimension_type="user",
                    dimension_id=activity.user_id,
                    aggregation_type="count",
                    period_type="hourly",
                    period_date=hour_start,
                    metadata={
                        "total_duration": activity.total_duration or 0
                    }
                )
                db.add(metric)
            
            # Aggregate learning progress
            progress = db.query(
                LearningProgress.user_id,
                LearningProgress.subject_id,
                func.count(LearningProgress.id).label("attempts"),
                func.avg(LearningProgress.score).label("avg_score"),
                func.sum(LearningProgress.time_spent_seconds).label("total_time")
            ).filter(
                LearningProgress.updated_at.between(hour_start, hour_end)
            ).group_by(
                LearningProgress.user_id,
                LearningProgress.subject_id
            ).all()
            
            for p in progress:
                # Average score metric
                if p.avg_score is not None:
                    metric = AggregatedMetrics(
                        metric_name="learning_score",
                        metric_value=float(p.avg_score),
                        dimension_type="user_subject",
                        dimension_id=p.user_id,
                        aggregation_type="avg",
                        period_type="hourly",
                        period_date=hour_start,
                        metadata={
                            "subject_id": p.subject_id,
                            "attempts": p.attempts,
                            "total_time": p.total_time or 0
                        }
                    )
                    db.add(metric)
            
            db.commit()
            logger.info("Hourly aggregation completed successfully")
            
            # Update Redis with latest metrics
            await self._update_redis_metrics(hour_start, "hourly")
            
        except Exception as e:
            logger.error(f"Error in hourly aggregation: {str(e)}")
            db.rollback()
        finally:
            db.close()
    
    async def aggregate_daily_metrics(self):
        """Aggregate metrics on a daily basis"""
        db = SessionLocal()
        try:
            now = datetime.utcnow()
            day_start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            logger.info(f"Starting daily aggregation for {day_start} to {day_end}")
            
            # User engagement metrics
            users = db.query(User).filter(User.is_active == True).all()
            
            for user in users:
                # Calculate daily engagement
                activities = db.query(UserActivity).filter(
                    UserActivity.user_id == user.id,
                    UserActivity.created_at.between(day_start, day_end)
                ).all()
                
                login_count = len([a for a in activities if a.activity_type == "login"])
                active_minutes = sum(a.duration_seconds for a in activities) // 60
                
                # Learning metrics
                lessons_completed = db.query(LearningProgress).filter(
                    LearningProgress.user_id == user.id,
                    LearningProgress.completed == True,
                    LearningProgress.completed_at.between(day_start, day_end),
                    LearningProgress.content_id.isnot(None)
                ).count()
                
                quests_completed = db.query(QuestProgress).filter(
                    QuestProgress.user_id == user.id,
                    QuestProgress.status == "completed",
                    QuestProgress.completed_at.between(day_start, day_end)
                ).count()
                
                achievements_earned = db.query(UserAchievement).filter(
                    UserAchievement.user_id == user.id,
                    UserAchievement.unlocked_at.between(day_start, day_end)
                ).count()
                
                # Calculate streak
                yesterday = day_start - timedelta(days=1)
                yesterday_engagement = db.query(UserEngagement).filter(
                    UserEngagement.user_id == user.id,
                    UserEngagement.date == yesterday
                ).first()
                
                streak_days = 0
                if login_count > 0:
                    if yesterday_engagement and yesterday_engagement.login_count > 0:
                        streak_days = yesterday_engagement.streak_days + 1
                    else:
                        streak_days = 1
                
                # Create or update engagement record
                engagement = db.query(UserEngagement).filter(
                    UserEngagement.user_id == user.id,
                    UserEngagement.date == day_start
                ).first()
                
                if not engagement:
                    engagement = UserEngagement(
                        user_id=user.id,
                        date=day_start
                    )
                    db.add(engagement)
                
                engagement.login_count = login_count
                engagement.active_minutes = active_minutes
                engagement.lessons_completed = lessons_completed
                engagement.quests_completed = quests_completed
                engagement.achievements_earned = achievements_earned
                engagement.interaction_count = len(activities)
                engagement.streak_days = streak_days
            
            # Global daily metrics
            total_active_users = db.query(
                func.count(func.distinct(UserActivity.user_id))
            ).filter(
                UserActivity.created_at.between(day_start, day_end)
            ).scalar()
            
            metric = AggregatedMetrics(
                metric_name="active_users",
                metric_value=total_active_users or 0,
                dimension_type="global",
                dimension_id=0,
                aggregation_type="count",
                period_type="daily",
                period_date=day_start
            )
            db.add(metric)
            
            # Content effectiveness update
            from .analytics_service import analytics_service
            contents = db.query(Content).all()
            for content in contents:
                await analytics_service.get_content_effectiveness(content.id, db)
            
            db.commit()
            logger.info("Daily aggregation completed successfully")
            
        except Exception as e:
            logger.error(f"Error in daily aggregation: {str(e)}")
            db.rollback()
        finally:
            db.close()
    
    async def aggregate_weekly_metrics(self):
        """Aggregate metrics on a weekly basis"""
        db = SessionLocal()
        try:
            now = datetime.utcnow()
            week_start = (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
            week_end = now.replace(hour=0, minute=0, second=0, microsecond=0)
            
            logger.info(f"Starting weekly aggregation for {week_start} to {week_end}")
            
            # Aggregate daily metrics into weekly
            daily_metrics = db.query(AggregatedMetrics).filter(
                AggregatedMetrics.period_type == "daily",
                AggregatedMetrics.period_date.between(week_start, week_end)
            ).all()
            
            # Group by metric name and dimension
            weekly_aggregates = {}
            for metric in daily_metrics:
                key = (metric.metric_name, metric.dimension_type, metric.dimension_id)
                if key not in weekly_aggregates:
                    weekly_aggregates[key] = []
                weekly_aggregates[key].append(metric.metric_value)
            
            # Create weekly metrics
            for (name, dim_type, dim_id), values in weekly_aggregates.items():
                if values:
                    # Determine aggregation based on metric name
                    if "count" in name or "total" in name:
                        value = sum(values)
                        agg_type = "sum"
                    else:
                        value = sum(values) / len(values)
                        agg_type = "avg"
                    
                    metric = AggregatedMetrics(
                        metric_name=name,
                        metric_value=value,
                        dimension_type=dim_type,
                        dimension_id=dim_id,
                        aggregation_type=agg_type,
                        period_type="weekly",
                        period_date=week_start
                    )
                    db.add(metric)
            
            db.commit()
            logger.info("Weekly aggregation completed successfully")
            
        except Exception as e:
            logger.error(f"Error in weekly aggregation: {str(e)}")
            db.rollback()
        finally:
            db.close()
    
    async def aggregate_monthly_metrics(self):
        """Aggregate metrics on a monthly basis"""
        db = SessionLocal()
        try:
            now = datetime.utcnow()
            month_start = (now.replace(day=1) - timedelta(days=1)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_end = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            logger.info(f"Starting monthly aggregation for {month_start} to {month_end}")
            
            # Similar to weekly but for monthly data
            weekly_metrics = db.query(AggregatedMetrics).filter(
                AggregatedMetrics.period_type == "weekly",
                AggregatedMetrics.period_date >= month_start,
                AggregatedMetrics.period_date < month_end
            ).all()
            
            # Group and aggregate
            monthly_aggregates = {}
            for metric in weekly_metrics:
                key = (metric.metric_name, metric.dimension_type, metric.dimension_id)
                if key not in monthly_aggregates:
                    monthly_aggregates[key] = []
                monthly_aggregates[key].append(metric.metric_value)
            
            for (name, dim_type, dim_id), values in monthly_aggregates.items():
                if values:
                    if "count" in name or "total" in name:
                        value = sum(values)
                        agg_type = "sum"
                    else:
                        value = sum(values) / len(values)
                        agg_type = "avg"
                    
                    metric = AggregatedMetrics(
                        metric_name=name,
                        metric_value=value,
                        dimension_type=dim_type,
                        dimension_id=dim_id,
                        aggregation_type=agg_type,
                        period_type="monthly",
                        period_date=month_start
                    )
                    db.add(metric)
            
            # Generate monthly report snapshot
            from .analytics_service import analytics_service
            report = await analytics_service.generate_report(
                "global", month_start, month_end, None, db
            )
            
            from ..models.analytics import ReportSnapshot
            snapshot = ReportSnapshot(
                report_type="monthly",
                report_data=report,
                start_date=month_start,
                end_date=month_end,
                is_scheduled=True
            )
            db.add(snapshot)
            
            db.commit()
            logger.info("Monthly aggregation completed successfully")
            
        except Exception as e:
            logger.error(f"Error in monthly aggregation: {str(e)}")
            db.rollback()
        finally:
            db.close()
    
    async def _update_redis_metrics(self, period_date: datetime, period_type: str):
        """Update Redis with latest aggregated metrics for real-time access"""
        try:
            # Store latest metrics in Redis
            key = f"analytics:aggregated:{period_type}:{period_date.date()}"
            
            # Get metrics from database
            db = SessionLocal()
            metrics = db.query(AggregatedMetrics).filter(
                AggregatedMetrics.period_date == period_date,
                AggregatedMetrics.period_type == period_type
            ).all()
            
            # Convert to dictionary for Redis storage
            metrics_dict = {}
            for metric in metrics:
                metric_key = f"{metric.metric_name}:{metric.dimension_type}:{metric.dimension_id}"
                metrics_dict[metric_key] = metric.metric_value
            
            # Store in Redis with expiration
            if metrics_dict:
                await self.redis_client.hmset(key, metrics_dict)
                await self.redis_client.expire(key, 86400 * 7)  # Keep for 7 days
            
            db.close()
            
        except Exception as e:
            logger.error(f"Error updating Redis metrics: {str(e)}")
    
    async def calculate_real_time_metrics(self, user_id: Optional[int] = None):
        """Calculate real-time metrics on demand"""
        try:
            db = SessionLocal()
            now = datetime.utcnow()
            hour_ago = now - timedelta(hours=1)
            
            metrics = {
                "timestamp": now.isoformat(),
                "period": "last_hour"
            }
            
            if user_id:
                # User-specific metrics
                activities = db.query(UserActivity).filter(
                    UserActivity.user_id == user_id,
                    UserActivity.created_at >= hour_ago
                ).count()
                
                progress = db.query(LearningProgress).filter(
                    LearningProgress.user_id == user_id,
                    LearningProgress.updated_at >= hour_ago
                ).all()
                
                metrics["user_metrics"] = {
                    "activities": activities,
                    "lessons_attempted": len(progress),
                    "average_score": sum(p.score for p in progress if p.score) / len(progress) if progress else 0
                }
            else:
                # Global metrics
                active_users = db.query(
                    func.count(func.distinct(UserActivity.user_id))
                ).filter(
                    UserActivity.created_at >= hour_ago
                ).scalar()
                
                total_activities = db.query(UserActivity).filter(
                    UserActivity.created_at >= hour_ago
                ).count()
                
                metrics["global_metrics"] = {
                    "active_users": active_users or 0,
                    "total_activities": total_activities
                }
            
            db.close()
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating real-time metrics: {str(e)}")
            return {}

# Singleton instance
data_aggregation_service = DataAggregationService()