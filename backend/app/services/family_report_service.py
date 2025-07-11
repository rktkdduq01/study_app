"""
Family Report Service
Service for generating comprehensive learning reports for parents
"""

import asyncio
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import json
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
from io import BytesIO
import base64

from app.core.logger import get_logger
from app.core.redis_client import redis_client
from app.core.ai_tutor import ai_tutor_service
from app.models.family import (
    Family, FamilyMember, FamilyReport, ActivityMonitoring,
    ParentQuest, FamilyRole
)
from app.models.user import User
from app.models.analytics import LearningProgress, SubjectProgress
from app.models.gamification import UserAchievement, Achievement, UserQuest, QuestStatus
from app.schemas.family import ReportGenerationRequest

logger = get_logger(__name__)

class FamilyReportService:
    """Service for generating family learning reports"""
    
    def __init__(self, db: Session):
        self.db = db
        
    async def generate_report(self, parent_id: int, child_id: int, 
                            report_type: str = "weekly") -> FamilyReport:
        """Generate a comprehensive learning report"""
        try:
            # Verify relationship
            if not self._verify_parent_child_relationship(parent_id, child_id):
                raise ValueError("Invalid parent-child relationship")
                
            # Determine report period
            period_end = datetime.utcnow()
            if report_type == "daily":
                period_start = period_end - timedelta(days=1)
            elif report_type == "weekly":
                period_start = period_end - timedelta(days=7)
            elif report_type == "monthly":
                period_start = period_end - timedelta(days=30)
            else:
                raise ValueError(f"Invalid report type: {report_type}")
                
            # Get family
            family_member = self.db.query(FamilyMember).filter(
                and_(
                    FamilyMember.user_id == parent_id,
                    FamilyMember.role.in_([FamilyRole.PARENT, FamilyRole.GUARDIAN])
                )
            ).first()
            
            if not family_member:
                raise ValueError("Parent not found in any family")
                
            # Collect report data
            report_data = await self._collect_report_data(child_id, period_start, period_end)
            
            # Generate AI insights
            ai_insights = await self._generate_ai_insights(child_id, report_data)
            
            # Create report record
            report = FamilyReport(
                family_id=family_member.family_id,
                child_id=child_id,
                report_type=report_type,
                period_start=period_start,
                period_end=period_end,
                total_study_time=report_data["total_study_time"],
                subjects_studied=report_data["subjects_studied"],
                average_accuracy=report_data["average_accuracy"],
                goals_completed=report_data["goals_completed"],
                achievements_earned=[a["name"] for a in report_data["achievements"]],
                daily_breakdown=report_data["daily_breakdown"],
                subject_performance=report_data["subject_performance"],
                strength_areas=report_data["strength_areas"],
                improvement_areas=report_data["improvement_areas"],
                ai_insights=ai_insights["insights"],
                recommendations=ai_insights["recommendations"],
                status="generating"
            )
            
            self.db.add(report)
            self.db.commit()
            
            # Generate PDF report asynchronously
            asyncio.create_task(self._generate_pdf_report(report.id, report_data))
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            self.db.rollback()
            raise
            
    def _verify_parent_child_relationship(self, parent_id: int, child_id: int) -> bool:
        """Verify parent-child relationship"""
        # Similar to parent quest service
        parent_families = self.db.query(FamilyMember).filter(
            and_(
                FamilyMember.user_id == parent_id,
                FamilyMember.role.in_([FamilyRole.PARENT, FamilyRole.GUARDIAN])
            )
        ).all()
        
        for family_member in parent_families:
            child_member = self.db.query(FamilyMember).filter(
                and_(
                    FamilyMember.family_id == family_member.family_id,
                    FamilyMember.user_id == child_id,
                    FamilyMember.role == FamilyRole.CHILD
                )
            ).first()
            
            if child_member:
                return True
                
        return False
        
    async def _collect_report_data(self, child_id: int, 
                                 period_start: datetime, 
                                 period_end: datetime) -> Dict[str, Any]:
        """Collect all data for the report"""
        # Get child info
        child = self.db.query(User).filter(User.id == child_id).first()
        if not child:
            raise ValueError("Child not found")
            
        # Get activity data
        activities = self.db.query(ActivityMonitoring).filter(
            and_(
                ActivityMonitoring.user_id == child_id,
                ActivityMonitoring.start_time >= period_start,
                ActivityMonitoring.start_time <= period_end
            )
        ).all()
        
        # Calculate metrics
        total_study_time = sum(a.duration_seconds or 0 for a in activities) // 60  # minutes
        total_problems = sum(a.problems_attempted or 0 for a in activities)
        correct_problems = sum(a.problems_correct or 0 for a in activities)
        average_accuracy = (correct_problems / total_problems * 100) if total_problems > 0 else 0
        
        # Get subjects studied
        subjects_studied = list(set(a.subject for a in activities if a.subject))
        
        # Get daily breakdown
        daily_breakdown = self._calculate_daily_breakdown(activities, period_start, period_end)
        
        # Get subject performance
        subject_performance = self._calculate_subject_performance(activities)
        
        # Get learning progress
        progress_records = self.db.query(LearningProgress).filter(
            and_(
                LearningProgress.user_id == child_id,
                LearningProgress.date >= period_start.date(),
                LearningProgress.date <= period_end.date()
            )
        ).all()
        
        goals_completed = sum(p.goals_completed or 0 for p in progress_records)
        
        # Get achievements
        achievements = self._get_period_achievements(child_id, period_start, period_end)
        
        # Get quests completed
        completed_quests = self._get_completed_quests(child_id, period_start, period_end)
        
        # Identify strengths and improvement areas
        strength_areas = self._identify_strengths(subject_performance)
        improvement_areas = self._identify_improvement_areas(subject_performance)
        
        return {
            "child_name": child.username,
            "child_id": child_id,
            "period_start": period_start,
            "period_end": period_end,
            "total_study_time": total_study_time,
            "total_problems": total_problems,
            "correct_problems": correct_problems,
            "average_accuracy": int(average_accuracy),
            "subjects_studied": subjects_studied,
            "goals_completed": goals_completed,
            "achievements": achievements,
            "completed_quests": completed_quests,
            "daily_breakdown": daily_breakdown,
            "subject_performance": subject_performance,
            "strength_areas": strength_areas,
            "improvement_areas": improvement_areas,
            "activities": activities
        }
        
    def _calculate_daily_breakdown(self, activities: List[ActivityMonitoring], 
                                 period_start: datetime, 
                                 period_end: datetime) -> List[Dict[str, Any]]:
        """Calculate daily activity breakdown"""
        daily_data = defaultdict(lambda: {
            "date": None,
            "study_time": 0,
            "problems_attempted": 0,
            "problems_correct": 0,
            "subjects": set(),
            "activities": 0
        })
        
        for activity in activities:
            date_key = activity.start_time.date()
            daily = daily_data[date_key]
            
            daily["date"] = date_key.isoformat()
            daily["study_time"] += (activity.duration_seconds or 0) // 60
            daily["problems_attempted"] += activity.problems_attempted or 0
            daily["problems_correct"] += activity.problems_correct or 0
            if activity.subject:
                daily["subjects"].add(activity.subject)
            daily["activities"] += 1
            
        # Convert to list and ensure all days are included
        result = []
        current_date = period_start.date()
        
        while current_date <= period_end.date():
            if current_date in daily_data:
                data = daily_data[current_date]
                data["subjects"] = list(data["subjects"])
                result.append(data)
            else:
                result.append({
                    "date": current_date.isoformat(),
                    "study_time": 0,
                    "problems_attempted": 0,
                    "problems_correct": 0,
                    "subjects": [],
                    "activities": 0
                })
            current_date += timedelta(days=1)
            
        return result
        
    def _calculate_subject_performance(self, activities: List[ActivityMonitoring]) -> Dict[str, Any]:
        """Calculate performance by subject"""
        subject_data = defaultdict(lambda: {
            "total_time": 0,
            "problems_attempted": 0,
            "problems_correct": 0,
            "accuracy_rate": 0,
            "sessions": 0,
            "average_score": 0,
            "topics_covered": set()
        })
        
        for activity in activities:
            if not activity.subject:
                continue
                
            subject = subject_data[activity.subject]
            subject["total_time"] += (activity.duration_seconds or 0) // 60
            subject["problems_attempted"] += activity.problems_attempted or 0
            subject["problems_correct"] += activity.problems_correct or 0
            subject["sessions"] += 1
            
            if activity.score:
                # Calculate running average
                current_avg = subject["average_score"]
                subject["average_score"] = (
                    (current_avg * (subject["sessions"] - 1) + activity.score) / 
                    subject["sessions"]
                )
                
            if activity.topic:
                subject["topics_covered"].add(activity.topic)
                
        # Calculate accuracy rates
        for subject, data in subject_data.items():
            if data["problems_attempted"] > 0:
                data["accuracy_rate"] = int(
                    data["problems_correct"] / data["problems_attempted"] * 100
                )
            data["topics_covered"] = list(data["topics_covered"])
            data["average_score"] = int(data["average_score"])
            
        return dict(subject_data)
        
    def _get_period_achievements(self, child_id: int, 
                               period_start: datetime, 
                               period_end: datetime) -> List[Dict[str, Any]]:
        """Get achievements earned during period"""
        user_achievements = self.db.query(UserAchievement).join(Achievement).filter(
            and_(
                UserAchievement.user_id == child_id,
                UserAchievement.unlocked_at >= period_start,
                UserAchievement.unlocked_at <= period_end
            )
        ).all()
        
        return [
            {
                "name": ua.achievement.name,
                "description": ua.achievement.description,
                "category": ua.achievement.category,
                "unlocked_at": ua.unlocked_at.isoformat()
            }
            for ua in user_achievements
        ]
        
    def _get_completed_quests(self, child_id: int,
                            period_start: datetime,
                            period_end: datetime) -> List[Dict[str, Any]]:
        """Get quests completed during period"""
        completed_quests = self.db.query(UserQuest).filter(
            and_(
                UserQuest.user_id == child_id,
                UserQuest.status == QuestStatus.COMPLETED,
                UserQuest.completed_at >= period_start,
                UserQuest.completed_at <= period_end
            )
        ).all()
        
        quest_data = []
        for uq in completed_quests:
            if uq.parent_quest_id:
                # Parent quest
                parent_quest = self.db.query(ParentQuest).filter(
                    ParentQuest.id == uq.parent_quest_id
                ).first()
                
                if parent_quest:
                    quest_data.append({
                        "title": parent_quest.title,
                        "type": "parent_quest",
                        "completed_at": uq.completed_at.isoformat()
                    })
            elif uq.quest_id:
                # Regular quest
                quest_data.append({
                    "title": uq.quest.title if uq.quest else "Quest",
                    "type": "system_quest",
                    "completed_at": uq.completed_at.isoformat()
                })
                
        return quest_data
        
    def _identify_strengths(self, subject_performance: Dict[str, Any]) -> List[str]:
        """Identify strength areas based on performance"""
        strengths = []
        
        for subject, data in subject_performance.items():
            # High accuracy
            if data["accuracy_rate"] >= 85:
                strengths.append(f"Excellent accuracy in {subject} ({data['accuracy_rate']}%)")
                
            # Consistent practice
            if data["sessions"] >= 5:
                strengths.append(f"Consistent practice in {subject} ({data['sessions']} sessions)")
                
            # High scores
            if data["average_score"] >= 85:
                strengths.append(f"High performance in {subject} (avg score: {data['average_score']})")
                
        return strengths[:5]  # Top 5 strengths
        
    def _identify_improvement_areas(self, subject_performance: Dict[str, Any]) -> List[str]:
        """Identify areas needing improvement"""
        improvements = []
        
        for subject, data in subject_performance.items():
            # Low accuracy
            if data["accuracy_rate"] < 70 and data["problems_attempted"] > 10:
                improvements.append(f"Practice accuracy in {subject} (current: {data['accuracy_rate']}%)")
                
            # Limited practice time
            if data["total_time"] < 30:  # Less than 30 minutes
                improvements.append(f"Increase practice time in {subject}")
                
            # Low scores
            if data["average_score"] < 70 and data["average_score"] > 0:
                improvements.append(f"Focus on improving {subject} scores")
                
        return improvements[:5]  # Top 5 improvement areas
        
    async def _generate_ai_insights(self, child_id: int, 
                                  report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-powered insights and recommendations"""
        try:
            # Prepare context for AI
            context = {
                "child_id": child_id,
                "total_study_time": report_data["total_study_time"],
                "average_accuracy": report_data["average_accuracy"],
                "subjects_studied": report_data["subjects_studied"],
                "subject_performance": report_data["subject_performance"],
                "daily_breakdown": report_data["daily_breakdown"],
                "achievements": len(report_data["achievements"]),
                "goals_completed": report_data["goals_completed"]
            }
            
            # Get AI insights
            insights = await ai_tutor_service.analyze_learning_patterns(child_id, context)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(report_data, insights)
            
            return {
                "insights": insights,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Failed to generate AI insights: {e}")
            return {
                "insights": ["Unable to generate AI insights at this time"],
                "recommendations": ["Continue regular practice", "Review weak areas"]
            }
            
    def _generate_recommendations(self, report_data: Dict[str, Any], 
                                ai_insights: List[str]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Time-based recommendations
        avg_daily_time = report_data["total_study_time"] / 7  # Assuming weekly report
        if avg_daily_time < 30:
            recommendations.append("Aim for at least 30 minutes of daily practice")
        elif avg_daily_time > 120:
            recommendations.append("Consider breaking study sessions into shorter periods")
            
        # Accuracy-based recommendations
        if report_data["average_accuracy"] < 70:
            recommendations.append("Focus on understanding concepts before attempting more problems")
        elif report_data["average_accuracy"] > 90:
            recommendations.append("Try more challenging problems to continue growth")
            
        # Subject diversity
        if len(report_data["subjects_studied"]) < 3:
            recommendations.append("Explore more subjects for well-rounded learning")
            
        # Consistency
        daily_activities = [d["activities"] for d in report_data["daily_breakdown"]]
        if daily_activities.count(0) > 2:
            recommendations.append("Maintain consistent daily practice for better retention")
            
        # Add AI recommendations
        recommendations.extend(ai_insights[:3])
        
        return recommendations[:7]  # Return top 7 recommendations
        
    async def _generate_pdf_report(self, report_id: int, report_data: Dict[str, Any]):
        """Generate PDF report with visualizations"""
        try:
            report = self.db.query(FamilyReport).filter(FamilyReport.id == report_id).first()
            if not report:
                return
                
            # Create PDF
            pdf_buffer = BytesIO()
            
            with PdfPages(pdf_buffer) as pdf:
                # Page 1: Summary
                fig = plt.figure(figsize=(8.5, 11))
                fig.suptitle(f"Learning Report for {report_data['child_name']}", fontsize=16)
                
                # Add summary text
                ax = fig.add_subplot(111)
                ax.axis('off')
                
                summary_text = f"""
Period: {report_data['period_start'].strftime('%Y-%m-%d')} to {report_data['period_end'].strftime('%Y-%m-%d')}

Total Study Time: {report_data['total_study_time']} minutes
Average Accuracy: {report_data['average_accuracy']}%
Subjects Studied: {', '.join(report_data['subjects_studied'])}
Goals Completed: {report_data['goals_completed']}
Achievements Earned: {len(report_data['achievements'])}

Strengths:
{chr(10).join(f'• {s}' for s in report_data['strength_areas'])}

Areas for Improvement:
{chr(10).join(f'• {i}' for i in report_data['improvement_areas'])}
                """
                
                ax.text(0.1, 0.9, summary_text, transform=ax.transAxes, 
                       fontsize=12, verticalalignment='top')
                
                pdf.savefig(fig)
                plt.close(fig)
                
                # Page 2: Daily Activity Chart
                fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8.5, 11))
                fig.suptitle('Daily Activity Analysis', fontsize=14)
                
                # Study time chart
                dates = [datetime.fromisoformat(d['date']) for d in report_data['daily_breakdown']]
                study_times = [d['study_time'] for d in report_data['daily_breakdown']]
                
                ax1.bar(dates, study_times, color='skyblue')
                ax1.set_ylabel('Study Time (minutes)')
                ax1.set_title('Daily Study Time')
                ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
                ax1.xaxis.set_major_locator(mdates.DayLocator())
                
                # Accuracy chart
                daily_accuracy = []
                for d in report_data['daily_breakdown']:
                    if d['problems_attempted'] > 0:
                        accuracy = (d['problems_correct'] / d['problems_attempted']) * 100
                        daily_accuracy.append(accuracy)
                    else:
                        daily_accuracy.append(0)
                        
                ax2.plot(dates, daily_accuracy, marker='o', linestyle='-', color='green')
                ax2.set_ylabel('Accuracy (%)')
                ax2.set_ylim(0, 105)
                ax2.set_title('Daily Accuracy Rate')
                ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
                ax2.xaxis.set_major_locator(mdates.DayLocator())
                ax2.grid(True, alpha=0.3)
                
                plt.tight_layout()
                pdf.savefig(fig)
                plt.close(fig)
                
                # Page 3: Subject Performance
                if report_data['subject_performance']:
                    fig, ax = plt.subplots(figsize=(8.5, 11))
                    fig.suptitle('Subject Performance Analysis', fontsize=14)
                    
                    subjects = list(report_data['subject_performance'].keys())
                    accuracy_rates = [report_data['subject_performance'][s]['accuracy_rate'] 
                                    for s in subjects]
                    study_times = [report_data['subject_performance'][s]['total_time'] 
                                 for s in subjects]
                    
                    x = np.arange(len(subjects))
                    width = 0.35
                    
                    ax.bar(x - width/2, accuracy_rates, width, label='Accuracy %', color='lightgreen')
                    ax.bar(x + width/2, study_times, width, label='Study Time (min)', color='lightblue')
                    
                    ax.set_xlabel('Subjects')
                    ax.set_title('Performance by Subject')
                    ax.set_xticks(x)
                    ax.set_xticklabels(subjects)
                    ax.legend()
                    
                    pdf.savefig(fig)
                    plt.close(fig)
                
                # Page 4: Recommendations
                fig = plt.figure(figsize=(8.5, 11))
                fig.suptitle('Recommendations', fontsize=14)
                
                ax = fig.add_subplot(111)
                ax.axis('off')
                
                recommendations_text = "AI-Powered Recommendations:\n\n"
                for i, rec in enumerate(report.recommendations, 1):
                    recommendations_text += f"{i}. {rec}\n\n"
                    
                ax.text(0.1, 0.9, recommendations_text, transform=ax.transAxes,
                       fontsize=12, verticalalignment='top', wrap=True)
                
                pdf.savefig(fig)
                plt.close(fig)
            
            # Save PDF to storage
            pdf_buffer.seek(0)
            pdf_data = pdf_buffer.read()
            
            # In production, upload to S3 or similar
            # For now, save to local storage
            report_filename = f"report_{report_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
            report_path = f"/tmp/{report_filename}"
            
            with open(report_path, 'wb') as f:
                f.write(pdf_data)
                
            # Update report with URL
            report.report_url = report_path
            report.status = "generated"
            self.db.commit()
            
            logger.info(f"Generated PDF report: {report_filename}")
            
        except Exception as e:
            logger.error(f"Failed to generate PDF report: {e}")
            
            # Update report status
            report = self.db.query(FamilyReport).filter(FamilyReport.id == report_id).first()
            if report:
                report.status = "failed"
                self.db.commit()
                
    def get_family_reports(self, parent_id: int, child_id: Optional[int] = None,
                          limit: int = 10) -> List[FamilyReport]:
        """Get family reports for a parent"""
        # Get parent's families
        family_members = self.db.query(FamilyMember).filter(
            and_(
                FamilyMember.user_id == parent_id,
                FamilyMember.role.in_([FamilyRole.PARENT, FamilyRole.GUARDIAN])
            )
        ).all()
        
        family_ids = [fm.family_id for fm in family_members]
        
        query = self.db.query(FamilyReport).filter(
            FamilyReport.family_id.in_(family_ids)
        )
        
        if child_id:
            query = query.filter(FamilyReport.child_id == child_id)
            
        return query.order_by(FamilyReport.generated_at.desc()).limit(limit).all()
        
    def mark_report_viewed(self, report_id: int, parent_id: int) -> bool:
        """Mark report as viewed by parent"""
        try:
            report = self.db.query(FamilyReport).filter(FamilyReport.id == report_id).first()
            
            if not report:
                return False
                
            # Verify parent has access
            family_member = self.db.query(FamilyMember).filter(
                and_(
                    FamilyMember.family_id == report.family_id,
                    FamilyMember.user_id == parent_id,
                    FamilyMember.role.in_([FamilyRole.PARENT, FamilyRole.GUARDIAN])
                )
            ).first()
            
            if not family_member:
                return False
                
            report.viewed_at = datetime.utcnow()
            report.status = "viewed"
            
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark report as viewed: {e}")
            self.db.rollback()
            return False
            
    async def share_report(self, report_id: int, parent_id: int, 
                         share_with: List[str]) -> bool:
        """Share report with email addresses"""
        try:
            report = self.db.query(FamilyReport).filter(FamilyReport.id == report_id).first()
            
            if not report:
                return False
                
            # Verify parent has access
            family_member = self.db.query(FamilyMember).filter(
                and_(
                    FamilyMember.family_id == report.family_id,
                    FamilyMember.user_id == parent_id,
                    FamilyMember.role.in_([FamilyRole.PARENT, FamilyRole.GUARDIAN])
                )
            ).first()
            
            if not family_member:
                return False
                
            # Update shared list
            current_shared = report.shared_with or []
            report.shared_with = list(set(current_shared + share_with))
            
            self.db.commit()
            
            # Queue email sending
            # In production, this would send emails with report attachment
            for email in share_with:
                logger.info(f"Queued report {report_id} to be sent to {email}")
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to share report: {e}")
            self.db.rollback()
            return False