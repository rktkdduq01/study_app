"""
Family Monitoring System
Real-time monitoring and analytics for parent-child educational activities
"""

import asyncio
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional, Set
from collections import defaultdict, deque
import json
from dataclasses import dataclass, asdict
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.core.logger import get_logger
from app.core.redis_client import redis_client
from app.core.websocket_manager import websocket_manager
from app.models.family import (
    Family, FamilyMember, FamilyRole, ActivityMonitoring,
    ParentNotification, NotificationPreference
)
from app.models.user import User
from app.models.analytics import LearningProgress

logger = get_logger(__name__)

class ActivityStatus(Enum):
    """Activity status indicators"""
    ACTIVE = "active"
    IDLE = "idle"
    OFFLINE = "offline"

class AlertType(Enum):
    """Alert types for parents"""
    LOW_ACTIVITY = "low_activity"
    HIGH_ERROR_RATE = "high_error_rate"
    GOAL_ACHIEVED = "goal_achieved"
    MILESTONE_REACHED = "milestone_reached"
    HELP_NEEDED = "help_needed"
    EXCEPTIONAL_PERFORMANCE = "exceptional_performance"

@dataclass
class ChildActivity:
    """Real-time child activity data"""
    user_id: int
    username: str
    status: ActivityStatus
    current_activity: Optional[Dict[str, Any]]
    last_active: datetime
    today_stats: Dict[str, Any]
    current_session: Optional[Dict[str, Any]]

@dataclass
class MonitoringAlert:
    """Monitoring alert data"""
    alert_type: AlertType
    child_id: int
    child_name: str
    message: str
    severity: str
    data: Dict[str, Any]
    timestamp: datetime

class FamilyMonitoringService:
    """Service for real-time family monitoring"""
    
    def __init__(self, db: Session):
        self.db = db
        self.active_monitors: Dict[int, Set[int]] = defaultdict(set)  # parent_id -> child_ids
        self.activity_cache: Dict[int, ChildActivity] = {}  # child_id -> activity
        self.alert_queue: deque = deque(maxlen=1000)
        
        # Background tasks
        self._monitoring_task = None
        self._alert_task = None
        self._cleanup_task = None
        
    async def start_monitoring(self):
        """Start monitoring background tasks"""
        if self._monitoring_task is None:
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        if self._alert_task is None:
            self._alert_task = asyncio.create_task(self._alert_processing_loop())
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            
    async def stop_monitoring(self):
        """Stop monitoring background tasks"""
        tasks = [self._monitoring_task, self._alert_task, self._cleanup_task]
        for task in tasks:
            if task:
                task.cancel()
                
    async def register_parent_monitoring(self, parent_id: int, child_ids: List[int]):
        """Register parent for monitoring specific children"""
        self.active_monitors[parent_id].update(child_ids)
        
        # Send initial status
        for child_id in child_ids:
            activity = await self._get_child_activity(child_id)
            if activity:
                await self._send_activity_update(parent_id, activity)
                
        logger.info(f"Parent {parent_id} registered for monitoring {len(child_ids)} children")
        
    async def unregister_parent_monitoring(self, parent_id: int, child_ids: Optional[List[int]] = None):
        """Unregister parent from monitoring"""
        if child_ids:
            self.active_monitors[parent_id].difference_update(child_ids)
        else:
            del self.active_monitors[parent_id]
            
    async def record_child_activity(self, child_id: int, activity_data: Dict[str, Any]):
        """Record child activity for monitoring"""
        try:
            # Create activity monitoring record
            activity = ActivityMonitoring(
                user_id=child_id,
                session_id=activity_data.get("session_id"),
                activity_type=activity_data.get("activity_type"),
                subject=activity_data.get("subject"),
                topic=activity_data.get("topic"),
                start_time=datetime.utcnow(),
                problems_attempted=activity_data.get("problems_attempted", 0),
                problems_correct=activity_data.get("problems_correct", 0),
                score=activity_data.get("score"),
                metadata=activity_data.get("metadata", {})
            )
            
            self.db.add(activity)
            self.db.commit()
            
            # Update cache
            await self._update_activity_cache(child_id, activity_data)
            
            # Check for alerts
            await self._check_activity_alerts(child_id, activity_data)
            
            # Notify monitoring parents
            await self._notify_monitoring_parents(child_id)
            
        except Exception as e:
            logger.error(f"Failed to record child activity: {e}")
            self.db.rollback()
            
    async def _get_child_activity(self, child_id: int) -> Optional[ChildActivity]:
        """Get current child activity status"""
        try:
            # Check cache first
            if child_id in self.activity_cache:
                cached = self.activity_cache[child_id]
                # Update if cache is recent (< 1 minute old)
                if (datetime.utcnow() - cached.last_active).total_seconds() < 60:
                    return cached
                    
            # Get user info
            user = self.db.query(User).filter(User.id == child_id).first()
            if not user:
                return None
                
            # Get current activity from Redis
            current_activity_key = f"user_activity:{child_id}"
            current_activity_data = await redis_client.get(current_activity_key)
            current_activity = json.loads(current_activity_data) if current_activity_data else None
            
            # Get today's stats
            today_stats = await self._get_today_stats(child_id)
            
            # Get current session
            session_key = f"user_session:{child_id}"
            session_data = await redis_client.get(session_key)
            current_session = json.loads(session_data) if session_data else None
            
            # Determine status
            if current_activity and current_activity.get("last_update"):
                last_update = datetime.fromisoformat(current_activity["last_update"])
                idle_seconds = (datetime.utcnow() - last_update).total_seconds()
                
                if idle_seconds < 300:  # Active in last 5 minutes
                    status = ActivityStatus.ACTIVE
                elif idle_seconds < 1800:  # Active in last 30 minutes
                    status = ActivityStatus.IDLE
                else:
                    status = ActivityStatus.OFFLINE
            else:
                status = ActivityStatus.OFFLINE
                
            activity = ChildActivity(
                user_id=child_id,
                username=user.username,
                status=status,
                current_activity=current_activity,
                last_active=datetime.utcnow() if status == ActivityStatus.ACTIVE else 
                          datetime.fromisoformat(current_activity["last_update"]) if current_activity else
                          datetime.utcnow() - timedelta(hours=1),
                today_stats=today_stats,
                current_session=current_session
            )
            
            # Update cache
            self.activity_cache[child_id] = activity
            
            return activity
            
        except Exception as e:
            logger.error(f"Failed to get child activity: {e}")
            return None
            
    async def _get_today_stats(self, child_id: int) -> Dict[str, Any]:
        """Get today's statistics for a child"""
        try:
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Query today's activities
            activities = self.db.query(ActivityMonitoring).filter(
                and_(
                    ActivityMonitoring.user_id == child_id,
                    ActivityMonitoring.start_time >= today_start
                )
            ).all()
            
            # Calculate stats
            total_time = sum(a.duration_seconds or 0 for a in activities)
            total_problems = sum(a.problems_attempted or 0 for a in activities)
            correct_problems = sum(a.problems_correct or 0 for a in activities)
            
            subjects_studied = list(set(a.subject for a in activities if a.subject))
            
            # Get progress data
            progress = self.db.query(LearningProgress).filter(
                and_(
                    LearningProgress.user_id == child_id,
                    LearningProgress.date == today_start.date()
                )
            ).first()
            
            return {
                "total_time_minutes": total_time // 60,
                "problems_attempted": total_problems,
                "problems_correct": correct_problems,
                "accuracy_rate": (correct_problems / total_problems * 100) if total_problems > 0 else 0,
                "subjects_studied": subjects_studied,
                "activities_count": len(activities),
                "xp_earned": progress.xp_earned if progress else 0,
                "goals_completed": progress.goals_completed if progress else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get today stats: {e}")
            return {}
            
    async def _update_activity_cache(self, child_id: int, activity_data: Dict[str, Any]):
        """Update activity cache with new data"""
        try:
            # Store in Redis for real-time access
            activity_key = f"user_activity:{child_id}"
            activity_data["last_update"] = datetime.utcnow().isoformat()
            
            await redis_client.setex(
                activity_key,
                3600,  # 1 hour TTL
                json.dumps(activity_data)
            )
            
            # Update local cache if exists
            if child_id in self.activity_cache:
                cached = self.activity_cache[child_id]
                cached.current_activity = activity_data
                cached.last_active = datetime.utcnow()
                cached.status = ActivityStatus.ACTIVE
                
        except Exception as e:
            logger.error(f"Failed to update activity cache: {e}")
            
    async def _check_activity_alerts(self, child_id: int, activity_data: Dict[str, Any]):
        """Check if activity triggers any alerts"""
        try:
            # Get family member settings
            family_member = self.db.query(FamilyMember).filter(
                and_(
                    FamilyMember.user_id == child_id,
                    FamilyMember.role == FamilyRole.CHILD,
                    FamilyMember.status == "active"
                )
            ).first()
            
            if not family_member:
                return
                
            prefs = family_member.monitoring_preferences or {}
            thresholds = prefs.get("alert_thresholds", {})
            
            # Check error rate
            if activity_data.get("problems_attempted", 0) > 5:
                error_rate = (1 - activity_data.get("problems_correct", 0) / 
                            activity_data.get("problems_attempted", 1)) * 100
                            
                if error_rate > thresholds.get("high_error_rate", 30):
                    await self._create_alert(
                        AlertType.HIGH_ERROR_RATE,
                        child_id,
                        f"High error rate detected: {error_rate:.1f}%",
                        "warning",
                        {"error_rate": error_rate, "subject": activity_data.get("subject")}
                    )
                    
            # Check for help needed
            if activity_data.get("help_requests", 0) > 3:
                await self._create_alert(
                    AlertType.HELP_NEEDED,
                    child_id,
                    "Multiple help requests detected",
                    "warning",
                    {"help_requests": activity_data.get("help_requests")}
                )
                
            # Check for exceptional performance
            if activity_data.get("score", 0) >= 95 and activity_data.get("problems_attempted", 0) >= 10:
                await self._create_alert(
                    AlertType.EXCEPTIONAL_PERFORMANCE,
                    child_id,
                    f"Excellent performance in {activity_data.get('subject', 'activity')}!",
                    "success",
                    {"score": activity_data.get("score"), "subject": activity_data.get("subject")}
                )
                
        except Exception as e:
            logger.error(f"Failed to check activity alerts: {e}")
            
    async def _create_alert(self, alert_type: AlertType, child_id: int, 
                          message: str, severity: str, data: Dict[str, Any]):
        """Create monitoring alert"""
        try:
            # Get child info
            child = self.db.query(User).filter(User.id == child_id).first()
            if not child:
                return
                
            alert = MonitoringAlert(
                alert_type=alert_type,
                child_id=child_id,
                child_name=child.username,
                message=message,
                severity=severity,
                data=data,
                timestamp=datetime.utcnow()
            )
            
            # Add to queue
            self.alert_queue.append(alert)
            
            # Store in Redis for persistence
            alert_key = f"family_alert:{child_id}:{datetime.utcnow().timestamp()}"
            await redis_client.setex(
                alert_key,
                86400,  # 24 hour TTL
                json.dumps(asdict(alert), default=str)
            )
            
        except Exception as e:
            logger.error(f"Failed to create alert: {e}")
            
    async def _notify_monitoring_parents(self, child_id: int):
        """Notify parents monitoring this child"""
        try:
            # Get child's current activity
            activity = await self._get_child_activity(child_id)
            if not activity:
                return
                
            # Find parents monitoring this child
            for parent_id, monitored_children in self.active_monitors.items():
                if child_id in monitored_children:
                    await self._send_activity_update(parent_id, activity)
                    
        except Exception as e:
            logger.error(f"Failed to notify monitoring parents: {e}")
            
    async def _send_activity_update(self, parent_id: int, activity: ChildActivity):
        """Send activity update to parent via WebSocket"""
        try:
            message = {
                "type": "child_activity_update",
                "data": {
                    "child_id": activity.user_id,
                    "username": activity.username,
                    "status": activity.status.value,
                    "current_activity": activity.current_activity,
                    "last_active": activity.last_active.isoformat(),
                    "today_stats": activity.today_stats
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Send via WebSocket to parent's monitoring group
            await websocket_manager.send_to_group(
                f"parent_monitoring_{parent_id}",
                message
            )
            
        except Exception as e:
            logger.error(f"Failed to send activity update: {e}")
            
    async def _monitoring_loop(self):
        """Background monitoring loop"""
        while True:
            try:
                await asyncio.sleep(30)  # Update every 30 seconds
                
                # Update all monitored children
                monitored_children = set()
                for children in self.active_monitors.values():
                    monitored_children.update(children)
                    
                for child_id in monitored_children:
                    activity = await self._get_child_activity(child_id)
                    if activity:
                        # Check for status changes
                        await self._check_status_changes(child_id, activity)
                        
                        # Update parents
                        await self._notify_monitoring_parents(child_id)
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                
    async def _check_status_changes(self, child_id: int, activity: ChildActivity):
        """Check for significant status changes"""
        try:
            # Check if child went offline
            if activity.status == ActivityStatus.OFFLINE:
                # Check last activity time
                family_member = self.db.query(FamilyMember).filter(
                    FamilyMember.user_id == child_id
                ).first()
                
                if family_member:
                    prefs = family_member.monitoring_preferences or {}
                    low_activity_threshold = prefs.get("alert_thresholds", {}).get("low_activity_days", 3)
                    
                    # Check if inactive for threshold days
                    days_inactive = (datetime.utcnow() - activity.last_active).days
                    if days_inactive >= low_activity_threshold:
                        await self._create_alert(
                            AlertType.LOW_ACTIVITY,
                            child_id,
                            f"No activity for {days_inactive} days",
                            "warning",
                            {"days_inactive": days_inactive}
                        )
                        
        except Exception as e:
            logger.error(f"Failed to check status changes: {e}")
            
    async def _alert_processing_loop(self):
        """Process alerts and send notifications"""
        while True:
            try:
                await asyncio.sleep(10)  # Process every 10 seconds
                
                # Process queued alerts
                alerts_to_process = []
                while self.alert_queue and len(alerts_to_process) < 10:
                    alerts_to_process.append(self.alert_queue.popleft())
                    
                for alert in alerts_to_process:
                    await self._process_alert(alert)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Alert processing error: {e}")
                
    async def _process_alert(self, alert: MonitoringAlert):
        """Process and send alert to parents"""
        try:
            # Get parents of this child
            family_members = self.db.query(FamilyMember).filter(
                and_(
                    FamilyMember.user_id == alert.child_id,
                    FamilyMember.role == FamilyRole.CHILD,
                    FamilyMember.status == "active"
                )
            ).all()
            
            for member in family_members:
                # Get parents in the same family
                parents = self.db.query(FamilyMember).filter(
                    and_(
                        FamilyMember.family_id == member.family_id,
                        FamilyMember.role.in_([FamilyRole.PARENT, FamilyRole.GUARDIAN]),
                        FamilyMember.status == "active"
                    )
                ).all()
                
                for parent in parents:
                    # Check notification preferences
                    if self._should_send_alert(parent, alert):
                        await self._send_alert_to_parent(parent, alert)
                        
        except Exception as e:
            logger.error(f"Failed to process alert: {e}")
            
    def _should_send_alert(self, parent: FamilyMember, alert: MonitoringAlert) -> bool:
        """Check if alert should be sent based on preferences"""
        if parent.notification_preference == NotificationPreference.NONE:
            return False
            
        if parent.notification_preference == NotificationPreference.REAL_TIME:
            return True
            
        # For other preferences, check timing
        # This would be implemented based on batching logic
        return True
        
    async def _send_alert_to_parent(self, parent: FamilyMember, alert: MonitoringAlert):
        """Send alert to parent"""
        try:
            # Create notification record
            notification = ParentNotification(
                parent_id=parent.user_id,
                child_id=alert.child_id,
                notification_type=alert.alert_type.value,
                title=f"Alert: {alert.child_name}",
                message=alert.message,
                severity=alert.severity,
                related_data=alert.data
            )
            
            self.db.add(notification)
            self.db.commit()
            
            # Send real-time notification
            if "in_app" in parent.notification_channels:
                await websocket_manager.send_to_group(
                    f"user_{parent.user_id}",
                    {
                        "type": "parent_alert",
                        "alert": asdict(alert, dict_factory=lambda x: {
                            k: v.isoformat() if isinstance(v, datetime) else 
                               v.value if hasattr(v, 'value') else v 
                            for k, v in x
                        })
                    }
                )
                
            # Queue email notification if enabled
            if "email" in parent.notification_channels:
                # This would queue email notification
                pass
                
        except Exception as e:
            logger.error(f"Failed to send alert to parent: {e}")
            self.db.rollback()
            
    async def _cleanup_loop(self):
        """Cleanup old data"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                # Clean old activity cache
                cutoff_time = datetime.utcnow() - timedelta(hours=1)
                to_remove = []
                
                for child_id, activity in self.activity_cache.items():
                    if activity.last_active < cutoff_time:
                        to_remove.append(child_id)
                        
                for child_id in to_remove:
                    del self.activity_cache[child_id]
                    
                logger.info(f"Cleaned up {len(to_remove)} inactive cache entries")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
                
    async def get_monitoring_dashboard(self, parent_id: int) -> Dict[str, Any]:
        """Get monitoring dashboard data for parent"""
        try:
            # Get monitored children
            family_members = self.db.query(FamilyMember).filter(
                and_(
                    FamilyMember.user_id == parent_id,
                    FamilyMember.role.in_([FamilyRole.PARENT, FamilyRole.GUARDIAN]),
                    FamilyMember.status == "active"
                )
            ).all()
            
            children_data = []
            
            for member in family_members:
                # Get children in family
                children = self.db.query(FamilyMember).filter(
                    and_(
                        FamilyMember.family_id == member.family_id,
                        FamilyMember.role == FamilyRole.CHILD,
                        FamilyMember.status == "active"
                    )
                ).all()
                
                for child in children:
                    # Get child activity
                    activity = await self._get_child_activity(child.user_id)
                    if activity:
                        children_data.append({
                            "user_id": activity.user_id,
                            "username": activity.username,
                            "status": activity.status.value,
                            "last_active": activity.last_active.isoformat(),
                            "today_stats": activity.today_stats,
                            "current_activity": activity.current_activity
                        })
                        
            # Get recent alerts
            recent_alerts = []
            alert_keys = await redis_client.keys("family_alert:*")
            
            for key in alert_keys[-20:]:  # Last 20 alerts
                alert_data = await redis_client.get(key)
                if alert_data:
                    alert = json.loads(alert_data)
                    # Check if alert is for monitored children
                    if any(c["user_id"] == alert["child_id"] for c in children_data):
                        recent_alerts.append(alert)
                        
            return {
                "children": children_data,
                "recent_alerts": sorted(recent_alerts, 
                                      key=lambda x: x["timestamp"], 
                                      reverse=True)[:10],
                "summary": {
                    "total_children": len(children_data),
                    "active_children": sum(1 for c in children_data if c["status"] == "active"),
                    "total_study_time_today": sum(c["today_stats"].get("total_time_minutes", 0) 
                                                for c in children_data),
                    "total_problems_today": sum(c["today_stats"].get("problems_attempted", 0) 
                                              for c in children_data)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get monitoring dashboard: {e}")
            return {"error": str(e)}

# Global monitoring service instance (to be initialized with DB session)
monitoring_service = None

def get_monitoring_service(db: Session) -> FamilyMonitoringService:
    """Get or create monitoring service instance"""
    global monitoring_service
    if monitoring_service is None:
        monitoring_service = FamilyMonitoringService(db)
    return monitoring_service