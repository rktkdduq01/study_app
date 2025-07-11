"""
Family and Parent Dashboard schemas
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class FamilyRole(str, Enum):
    PARENT = "parent"
    CHILD = "child"
    GUARDIAN = "guardian"


class NotificationChannel(str, Enum):
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class AlertType(str, Enum):
    LOW_ACTIVITY = "low_activity"
    HIGH_ERROR_RATE = "high_error_rate"
    ACHIEVEMENT_UNLOCKED = "achievement_unlocked"
    QUEST_COMPLETED = "quest_completed"
    DAILY_SUMMARY = "daily_summary"
    WEEKLY_REPORT = "weekly_report"


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class ActivityStatus(str, Enum):
    ACTIVE = "active"
    IDLE = "idle"
    OFFLINE = "offline"


class QuestRequirementType(str, Enum):
    STUDY_TIME = "study_time"
    PROBLEMS_SOLVED = "problems_solved"
    CHAPTERS_READ = "chapters_read"
    QUESTS_COMPLETED = "quests_completed"
    SCORE_THRESHOLD = "score_threshold"


class RewardType(str, Enum):
    XP = "xp"
    COINS = "coins"
    BADGES = "badges"
    REAL_WORLD = "real_world"
    CUSTOM = "custom"


# Family Management Schemas
class FamilyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class FamilyCreate(FamilyBase):
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Family name cannot be empty')
        return v.strip()


class FamilyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class FamilyResponse(FamilyBase):
    id: int
    created_by: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    member_count: Optional[int] = 0

    class Config:
        from_attributes = True


# Family Member Schemas
class FamilyMemberBase(BaseModel):
    user_id: int
    role: FamilyRole = FamilyRole.CHILD


class FamilyMemberCreate(FamilyMemberBase):
    family_id: Optional[int] = None  # Optional when inviting


class FamilyMemberUpdate(BaseModel):
    role: Optional[FamilyRole] = None
    is_active: Optional[bool] = None


class FamilyMemberResponse(FamilyMemberBase):
    id: int
    family_id: int
    joined_at: datetime
    is_active: bool
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    user_avatar: Optional[str] = None

    class Config:
        from_attributes = True


# Parent Quest Schemas
class QuestRequirement(BaseModel):
    type: QuestRequirementType
    value: int
    description: Optional[str] = None


class QuestReward(BaseModel):
    type: RewardType
    value: Dict[str, Any]
    description: Optional[str] = None


class ParentQuestBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=1000)
    requirements: List[QuestRequirement]
    rewards: List[QuestReward]
    child_id: int
    due_date: Optional[datetime] = None
    is_recurring: bool = False
    recurrence_pattern: Optional[Dict[str, Any]] = None


class ParentQuestCreate(ParentQuestBase):
    @validator('title')
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError('Quest title cannot be empty')
        return v.strip()

    @validator('requirements')
    def validate_requirements(cls, v):
        if not v:
            raise ValueError('At least one requirement is needed')
        return v


class ParentQuestUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1, max_length=1000)
    requirements: Optional[List[QuestRequirement]] = None
    rewards: Optional[List[QuestReward]] = None
    due_date: Optional[datetime] = None
    is_active: Optional[bool] = None


class ParentQuestResponse(ParentQuestBase):
    id: int
    created_by: int
    family_id: int
    is_active: bool
    is_completed: bool
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    progress: Optional[Dict[str, Any]] = {}

    class Config:
        from_attributes = True


# Activity Monitoring Schemas
class ActivityMonitoringCreate(BaseModel):
    child_id: int
    activity_type: str
    activity_data: Dict[str, Any]
    duration_minutes: Optional[int] = None


class ActivityMonitoringResponse(BaseModel):
    id: int
    family_id: int
    child_id: int
    activity_type: str
    activity_data: Dict[str, Any]
    duration_minutes: Optional[int]
    created_at: datetime
    child_name: Optional[str] = None

    class Config:
        from_attributes = True


# Dashboard Data Schemas
class ChildActivitySummary(BaseModel):
    child_id: int
    child_name: str
    avatar_url: Optional[str]
    status: ActivityStatus
    last_active: Optional[datetime]
    today_stats: Dict[str, Any]
    weekly_stats: Dict[str, Any]
    current_level: int
    current_streak: int
    active_quests: int
    completed_quests_today: int


class DashboardData(BaseModel):
    family_id: int
    family_name: str
    children: List[ChildActivitySummary]
    recent_activities: List[ActivityMonitoringResponse]
    pending_quests: List[ParentQuestResponse]
    recent_achievements: List[Dict[str, Any]]
    alerts: List[Dict[str, Any]]


# Report Schemas
class ReportType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class FamilyReportCreate(BaseModel):
    report_type: ReportType
    child_id: Optional[int] = None  # None means all children
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    include_ai_insights: bool = True


class FamilyReportResponse(BaseModel):
    id: int
    family_id: int
    report_type: ReportType
    report_data: Dict[str, Any]
    ai_insights: Optional[Dict[str, Any]]
    generated_at: datetime
    generated_by: int
    file_url: Optional[str] = None

    class Config:
        from_attributes = True


# Notification Schemas
class NotificationPreferences(BaseModel):
    channels: List[NotificationChannel] = [NotificationChannel.IN_APP]
    alert_types: Dict[AlertType, bool] = {
        AlertType.LOW_ACTIVITY: True,
        AlertType.HIGH_ERROR_RATE: True,
        AlertType.ACHIEVEMENT_UNLOCKED: True,
        AlertType.QUEST_COMPLETED: True,
        AlertType.DAILY_SUMMARY: False,
        AlertType.WEEKLY_REPORT: True
    }
    quiet_hours_start: Optional[int] = 22  # 10 PM
    quiet_hours_end: Optional[int] = 7    # 7 AM


class ParentNotificationBase(BaseModel):
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    child_id: Optional[int] = None
    action_url: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class ParentNotificationCreate(ParentNotificationBase):
    pass


class ParentNotificationResponse(ParentNotificationBase):
    id: int
    family_id: int
    parent_id: int
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime]

    class Config:
        from_attributes = True


# Real-time Monitoring Schemas
class MonitoringAlert(BaseModel):
    type: AlertType
    severity: AlertSeverity
    child_id: int
    child_name: str
    message: str
    details: Dict[str, Any]
    timestamp: datetime


class LiveActivityUpdate(BaseModel):
    child_id: int
    child_name: str
    activity_type: str
    activity_details: Dict[str, Any]
    timestamp: datetime


# Family Settings Schemas
class AlertThresholds(BaseModel):
    low_activity_hours: int = 2  # Alert if inactive for 2 hours
    high_error_rate_percentage: int = 50  # Alert if error rate > 50%
    min_daily_study_minutes: int = 30  # Alert if study time < 30 min


class FamilySettings(BaseModel):
    notification_preferences: NotificationPreferences
    alert_thresholds: AlertThresholds
    dashboard_refresh_interval: int = 60  # seconds
    report_generation_day: int = 1  # 1st of each month
    timezone: str = "UTC"


class FamilySettingsUpdate(BaseModel):
    notification_preferences: Optional[NotificationPreferences] = None
    alert_thresholds: Optional[AlertThresholds] = None
    dashboard_refresh_interval: Optional[int] = Field(None, ge=10, le=300)
    report_generation_day: Optional[int] = Field(None, ge=1, le=28)
    timezone: Optional[str] = None