from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from io import BytesIO
import xlsxwriter
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import json

from ..models.analytics import (
    UserActivity, LearningProgress, PerformanceMetric,
    ContentEffectiveness, UserEngagement, ReportSnapshot
)
from ..models.user import User
from ..models.subject import Subject
from ..models.content import Content
from ..models.quest import Quest, QuestProgress
from ..core.redis_client import redis_client
from ..services.email_service import email_service

class ReportGenerator:
    def __init__(self):
        self.redis_client = redis_client
    
    async def generate_user_report(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        db: Session
    ) -> Dict[str, Any]:
        """Generate comprehensive user report"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        report = {
            "report_type": "user_report",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "created_at": user.created_at.isoformat()
            },
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
        # Learning Summary
        progress_records = db.query(LearningProgress).filter(
            LearningProgress.user_id == user_id,
            LearningProgress.updated_at.between(start_date, end_date)
        ).all()
        
        report["learning_summary"] = {
            "total_items_attempted": len(progress_records),
            "items_completed": len([p for p in progress_records if p.completed]),
            "total_time_spent": sum(p.time_spent_seconds for p in progress_records),
            "average_score": np.mean([p.score for p in progress_records if p.score]) if progress_records else 0,
            "subjects_studied": len(set(p.subject_id for p in progress_records))
        }
        
        # Subject Breakdown
        subject_stats = {}
        for progress in progress_records:
            subject = db.query(Subject).filter(Subject.id == progress.subject_id).first()
            if subject:
                if subject.name not in subject_stats:
                    subject_stats[subject.name] = {
                        "attempts": 0,
                        "completions": 0,
                        "total_time": 0,
                        "scores": []
                    }
                
                stats = subject_stats[subject.name]
                stats["attempts"] += 1
                if progress.completed:
                    stats["completions"] += 1
                stats["total_time"] += progress.time_spent_seconds
                if progress.score is not None:
                    stats["scores"].append(progress.score)
        
        # Calculate averages
        for subject, stats in subject_stats.items():
            stats["average_score"] = np.mean(stats["scores"]) if stats["scores"] else 0
            stats["completion_rate"] = (stats["completions"] / stats["attempts"] * 100) if stats["attempts"] > 0 else 0
        
        report["subject_breakdown"] = subject_stats
        
        # Activity Patterns
        activities = db.query(UserActivity).filter(
            UserActivity.user_id == user_id,
            UserActivity.created_at.between(start_date, end_date)
        ).all()
        
        activity_by_day = {}
        activity_by_type = {}
        
        for activity in activities:
            # By day
            day = activity.created_at.date().isoformat()
            if day not in activity_by_day:
                activity_by_day[day] = 0
            activity_by_day[day] += 1
            
            # By type
            if activity.activity_type not in activity_by_type:
                activity_by_type[activity.activity_type] = 0
            activity_by_type[activity.activity_type] += 1
        
        report["activity_patterns"] = {
            "by_day": activity_by_day,
            "by_type": activity_by_type,
            "total_activities": len(activities),
            "average_daily_activities": len(activities) / max((end_date - start_date).days, 1)
        }
        
        # Performance Trends
        performance_metrics = db.query(PerformanceMetric).filter(
            PerformanceMetric.user_id == user_id,
            PerformanceMetric.period_date.between(start_date, end_date)
        ).order_by(PerformanceMetric.period_date).all()
        
        performance_trends = {}
        for metric in performance_metrics:
            if metric.metric_type not in performance_trends:
                performance_trends[metric.metric_type] = []
            
            performance_trends[metric.metric_type].append({
                "date": metric.period_date.isoformat(),
                "value": metric.metric_value,
                "period": metric.period_type
            })
        
        report["performance_trends"] = performance_trends
        
        # Quest Progress
        quest_progress = db.query(QuestProgress).filter(
            QuestProgress.user_id == user_id,
            QuestProgress.updated_at.between(start_date, end_date)
        ).all()
        
        report["quest_summary"] = {
            "total_quests": len(quest_progress),
            "completed_quests": len([q for q in quest_progress if q.status == "completed"]),
            "in_progress_quests": len([q for q in quest_progress if q.status == "active"]),
            "total_xp_earned": sum(q.xp_earned for q in quest_progress)
        }
        
        # Engagement Metrics
        engagement_records = db.query(UserEngagement).filter(
            UserEngagement.user_id == user_id,
            UserEngagement.date.between(start_date, end_date)
        ).all()
        
        if engagement_records:
            report["engagement_metrics"] = {
                "total_active_days": len(engagement_records),
                "total_active_minutes": sum(e.active_minutes for e in engagement_records),
                "average_daily_minutes": np.mean([e.active_minutes for e in engagement_records]),
                "max_streak": max(e.streak_days for e in engagement_records),
                "total_interactions": sum(e.interaction_count for e in engagement_records)
            }
        
        return report
    
    async def generate_content_report(
        self,
        start_date: datetime,
        end_date: datetime,
        db: Session
    ) -> Dict[str, Any]:
        """Generate content effectiveness report"""
        report = {
            "report_type": "content_report",
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
        # Get all content with effectiveness metrics
        content_effectiveness = db.query(ContentEffectiveness).all()
        
        content_data = []
        for ce in content_effectiveness:
            content = db.query(Content).filter(Content.id == ce.content_id).first()
            if content:
                # Get progress data for this content in the period
                progress_in_period = db.query(LearningProgress).filter(
                    LearningProgress.content_id == content.id,
                    LearningProgress.created_at.between(start_date, end_date)
                ).all()
                
                content_data.append({
                    "content_id": content.id,
                    "title": content.title,
                    "type": content.type,
                    "subject": content.subject.name if content.subject else "Unknown",
                    "difficulty": content.difficulty,
                    "total_views": ce.view_count,
                    "completion_rate": (ce.completion_count / ce.view_count * 100) if ce.view_count > 0 else 0,
                    "average_score": ce.average_score,
                    "average_time": ce.average_time_seconds,
                    "engagement_rate": ce.engagement_rate,
                    "effectiveness_score": ce.effectiveness_score,
                    "views_in_period": len(progress_in_period),
                    "completions_in_period": len([p for p in progress_in_period if p.completed])
                })
        
        # Sort by effectiveness score
        content_data.sort(key=lambda x: x["effectiveness_score"] or 0, reverse=True)
        
        report["content_analysis"] = {
            "total_content": len(content_data),
            "top_performing": content_data[:10],
            "bottom_performing": content_data[-10:] if len(content_data) > 10 else [],
            "average_effectiveness": np.mean([c["effectiveness_score"] for c in content_data if c["effectiveness_score"]]) if content_data else 0
        }
        
        # Content by type analysis
        content_by_type = {}
        for content in content_data:
            content_type = content["type"]
            if content_type not in content_by_type:
                content_by_type[content_type] = {
                    "count": 0,
                    "total_views": 0,
                    "total_completions": 0,
                    "effectiveness_scores": []
                }
            
            stats = content_by_type[content_type]
            stats["count"] += 1
            stats["total_views"] += content["views_in_period"]
            stats["total_completions"] += content["completions_in_period"]
            if content["effectiveness_score"]:
                stats["effectiveness_scores"].append(content["effectiveness_score"])
        
        # Calculate averages
        for content_type, stats in content_by_type.items():
            stats["average_effectiveness"] = np.mean(stats["effectiveness_scores"]) if stats["effectiveness_scores"] else 0
            stats["completion_rate"] = (stats["total_completions"] / stats["total_views"] * 100) if stats["total_views"] > 0 else 0
        
        report["content_by_type"] = content_by_type
        
        return report
    
    async def generate_revenue_report(
        self,
        start_date: datetime,
        end_date: datetime,
        db: Session
    ) -> Dict[str, Any]:
        """Generate revenue and subscription report"""
        from ..models.subscription import Subscription, Payment
        
        report = {
            "report_type": "revenue_report",
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
        # Get all payments in period
        payments = db.query(Payment).filter(
            Payment.payment_date.between(start_date, end_date),
            Payment.status == "completed"
        ).all()
        
        # Revenue summary
        total_revenue = sum(p.amount for p in payments)
        payment_by_type = {}
        payment_by_day = {}
        
        for payment in payments:
            # By type
            if payment.payment_type not in payment_by_type:
                payment_by_type[payment.payment_type] = {
                    "count": 0,
                    "total": 0
                }
            payment_by_type[payment.payment_type]["count"] += 1
            payment_by_type[payment.payment_type]["total"] += payment.amount
            
            # By day
            day = payment.payment_date.date().isoformat()
            if day not in payment_by_day:
                payment_by_day[day] = 0
            payment_by_day[day] += payment.amount
        
        report["revenue_summary"] = {
            "total_revenue": total_revenue,
            "total_transactions": len(payments),
            "average_transaction": total_revenue / len(payments) if payments else 0,
            "by_type": payment_by_type,
            "by_day": payment_by_day
        }
        
        # Subscription metrics
        active_subscriptions = db.query(Subscription).filter(
            Subscription.status == "active"
        ).all()
        
        new_subscriptions = db.query(Subscription).filter(
            Subscription.start_date.between(start_date, end_date)
        ).all()
        
        cancelled_subscriptions = db.query(Subscription).filter(
            Subscription.status == "cancelled",
            Subscription.end_date.between(start_date, end_date)
        ).all()
        
        # MRR calculation
        mrr = sum(s.plan.price for s in active_subscriptions)
        
        report["subscription_metrics"] = {
            "active_subscriptions": len(active_subscriptions),
            "new_subscriptions": len(new_subscriptions),
            "cancelled_subscriptions": len(cancelled_subscriptions),
            "churn_rate": (len(cancelled_subscriptions) / len(active_subscriptions) * 100) if active_subscriptions else 0,
            "monthly_recurring_revenue": mrr,
            "average_revenue_per_user": mrr / len(active_subscriptions) if active_subscriptions else 0
        }
        
        return report
    
    async def export_to_excel(
        self,
        report_data: Dict[str, Any],
        output_buffer: BytesIO
    ) -> BytesIO:
        """Export report data to Excel format"""
        workbook = xlsxwriter.Workbook(output_buffer)
        
        # Add formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4CAF50',
            'font_color': 'white',
            'border': 1
        })
        
        # Summary sheet
        summary_sheet = workbook.add_worksheet('Summary')
        summary_sheet.write(0, 0, 'Report Type', header_format)
        summary_sheet.write(0, 1, report_data.get('report_type', 'Unknown'))
        summary_sheet.write(1, 0, 'Generated At', header_format)
        summary_sheet.write(1, 1, report_data.get('generated_at', ''))
        summary_sheet.write(2, 0, 'Period Start', header_format)
        summary_sheet.write(2, 1, report_data.get('period', {}).get('start', ''))
        summary_sheet.write(3, 0, 'Period End', header_format)
        summary_sheet.write(3, 1, report_data.get('period', {}).get('end', ''))
        
        # Add data sheets based on report type
        if report_data['report_type'] == 'user_report':
            self._add_user_report_sheets(workbook, report_data, header_format)
        elif report_data['report_type'] == 'content_report':
            self._add_content_report_sheets(workbook, report_data, header_format)
        elif report_data['report_type'] == 'revenue_report':
            self._add_revenue_report_sheets(workbook, report_data, header_format)
        
        workbook.close()
        output_buffer.seek(0)
        return output_buffer
    
    def _add_user_report_sheets(self, workbook, report_data, header_format):
        """Add user report specific sheets"""
        # Learning Summary
        if 'learning_summary' in report_data:
            sheet = workbook.add_worksheet('Learning Summary')
            row = 0
            for key, value in report_data['learning_summary'].items():
                sheet.write(row, 0, key.replace('_', ' ').title(), header_format)
                sheet.write(row, 1, value)
                row += 1
        
        # Subject Breakdown
        if 'subject_breakdown' in report_data:
            sheet = workbook.add_worksheet('Subject Breakdown')
            sheet.write(0, 0, 'Subject', header_format)
            sheet.write(0, 1, 'Attempts', header_format)
            sheet.write(0, 2, 'Completions', header_format)
            sheet.write(0, 3, 'Avg Score', header_format)
            sheet.write(0, 4, 'Total Time (min)', header_format)
            sheet.write(0, 5, 'Completion Rate', header_format)
            
            row = 1
            for subject, stats in report_data['subject_breakdown'].items():
                sheet.write(row, 0, subject)
                sheet.write(row, 1, stats['attempts'])
                sheet.write(row, 2, stats['completions'])
                sheet.write(row, 3, f"{stats['average_score']:.1f}")
                sheet.write(row, 4, stats['total_time'] // 60)
                sheet.write(row, 5, f"{stats['completion_rate']:.1f}%")
                row += 1
    
    def _add_content_report_sheets(self, workbook, report_data, header_format):
        """Add content report specific sheets"""
        if 'content_analysis' in report_data:
            sheet = workbook.add_worksheet('Content Performance')
            headers = ['Content ID', 'Title', 'Type', 'Subject', 'Views', 'Completion Rate', 'Avg Score', 'Effectiveness']
            for col, header in enumerate(headers):
                sheet.write(0, col, header, header_format)
            
            row = 1
            for content in report_data['content_analysis']['top_performing']:
                sheet.write(row, 0, content['content_id'])
                sheet.write(row, 1, content['title'])
                sheet.write(row, 2, content['type'])
                sheet.write(row, 3, content['subject'])
                sheet.write(row, 4, content['views_in_period'])
                sheet.write(row, 5, f"{content['completion_rate']:.1f}%")
                sheet.write(row, 6, f"{content['average_score']:.1f}" if content['average_score'] else 'N/A')
                sheet.write(row, 7, f"{content['effectiveness_score']:.1f}" if content['effectiveness_score'] else 'N/A')
                row += 1
    
    def _add_revenue_report_sheets(self, workbook, report_data, header_format):
        """Add revenue report specific sheets"""
        if 'revenue_summary' in report_data:
            sheet = workbook.add_worksheet('Revenue Summary')
            sheet.write(0, 0, 'Metric', header_format)
            sheet.write(0, 1, 'Value', header_format)
            
            sheet.write(1, 0, 'Total Revenue')
            sheet.write(1, 1, f"${report_data['revenue_summary']['total_revenue']:.2f}")
            sheet.write(2, 0, 'Total Transactions')
            sheet.write(2, 1, report_data['revenue_summary']['total_transactions'])
            sheet.write(3, 0, 'Average Transaction')
            sheet.write(3, 1, f"${report_data['revenue_summary']['average_transaction']:.2f}")
    
    async def schedule_report(
        self,
        report_type: str,
        schedule: str,  # daily, weekly, monthly
        recipients: List[str],
        filters: Optional[Dict] = None,
        db: Session = None
    ):
        """Schedule automated report generation"""
        # This would typically integrate with a job scheduler
        # For now, we'll just store the schedule configuration
        schedule_config = {
            "report_type": report_type,
            "schedule": schedule,
            "recipients": recipients,
            "filters": filters,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Store in Redis for the scheduler to pick up
        await self.redis_client.hset(
            "scheduled_reports",
            f"{report_type}_{schedule}",
            json.dumps(schedule_config)
        )
        
        return schedule_config

# Singleton instance
report_generator = ReportGenerator()