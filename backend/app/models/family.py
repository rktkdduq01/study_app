"""
Family-related database models
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class FamilyRole(str, enum.Enum):
    """Family member roles"""
    PARENT = "parent"
    CHILD = "child"
    GUARDIAN = "guardian"


class AlertType(str, enum.Enum):
    """Alert types for monitoring"""
    LOW_ACTIVITY = "low_activity"
    HIGH_ERROR_RATE = "high_error_rate"
    ACHIEVEMENT_UNLOCKED = "achievement_unlocked"
    QUEST_COMPLETED = "quest_completed"
    DAILY_SUMMARY = "daily_summary"
    WEEKLY_REPORT = "weekly_report"


class AlertSeverity(str, enum.Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class Family(Base):
    """Family group model"""
    __tablename__ = "families"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    members = relationship("FamilyMember", back_populates="family", cascade="all, delete-orphan")
    quests = relationship("ParentQuest", back_populates="family", cascade="all, delete-orphan")
    reports = relationship("FamilyReport", back_populates="family", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Family {self.name}>"


class FamilyMember(Base):
    """Family membership model"""
    __tablename__ = "family_members"
    
    id = Column(Integer, primary_key=True, index=True)
    family_id = Column(Integer, ForeignKey("families.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(SQLEnum(FamilyRole), default=FamilyRole.CHILD)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    family = relationship("Family", back_populates="members")
    user = relationship("User", back_populates="family_memberships")
    
    def __repr__(self):
        return f"<FamilyMember user_id={self.user_id} role={self.role}>"


class ParentQuest(Base):
    """Custom quests created by parents for children"""
    __tablename__ = "parent_quests"
    
    id = Column(Integer, primary_key=True, index=True)
    family_id = Column(Integer, ForeignKey("families.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    child_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Quest details
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    requirements = Column(JSON, nullable=False)  # List of requirements
    rewards = Column(JSON, nullable=False)  # List of rewards
    
    # Quest settings
    due_date = Column(DateTime(timezone=True), nullable=True)
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(JSON, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    progress = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    family = relationship("Family", back_populates="quests")
    created_by_user = relationship("User", foreign_keys=[created_by])
    child_user = relationship("User", foreign_keys=[child_id])
    progress_logs = relationship("QuestProgressLog", back_populates="quest", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ParentQuest {self.title}>"


class QuestProgressLog(Base):
    """Track progress on parent-assigned quests"""
    __tablename__ = "quest_progress_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    quest_id = Column(Integer, ForeignKey("parent_quests.id"), nullable=False)
    child_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Progress data
    activity_type = Column(String, nullable=False)
    activity_data = Column(JSON, nullable=False)
    progress_value = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    quest = relationship("ParentQuest", back_populates="progress_logs")
    child = relationship("User")
    
    def __repr__(self):
        return f"<QuestProgressLog quest_id={self.quest_id} progress={self.progress_value}>"


class ActivityMonitoring(Base):
    """Real-time activity monitoring for children"""
    __tablename__ = "activity_monitoring"
    
    id = Column(Integer, primary_key=True, index=True)
    family_id = Column(Integer, ForeignKey("families.id"), nullable=False)
    child_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Activity details
    activity_type = Column(String, nullable=False)
    activity_data = Column(JSON, nullable=False)
    duration_minutes = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    family = relationship("Family")
    child = relationship("User")
    
    def __repr__(self):
        return f"<ActivityMonitoring child_id={self.child_id} type={self.activity_type}>"


class FamilyReport(Base):
    """Generated reports for families"""
    __tablename__ = "family_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    family_id = Column(Integer, ForeignKey("families.id"), nullable=False)
    generated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Report details
    report_type = Column(String, nullable=False)  # daily, weekly, monthly, custom
    report_data = Column(JSON, nullable=False)
    ai_insights = Column(JSON, nullable=True)
    file_url = Column(String, nullable=True)
    
    # Timestamps
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    family = relationship("Family", back_populates="reports")
    generated_by_user = relationship("User")
    
    def __repr__(self):
        return f"<FamilyReport type={self.report_type} family_id={self.family_id}>"


class ParentNotification(Base):
    """Notifications for parents"""
    __tablename__ = "parent_notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    family_id = Column(Integer, ForeignKey("families.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Notification details
    alert_type = Column(SQLEnum(AlertType), nullable=False)
    severity = Column(SQLEnum(AlertSeverity), default=AlertSeverity.INFO)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    child_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action_url = Column(String, nullable=True)
    data = Column(JSON, nullable=True)
    
    # Status
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    family = relationship("Family")
    parent = relationship("User", foreign_keys=[parent_id])
    child = relationship("User", foreign_keys=[child_id])
    
    def __repr__(self):
        return f"<ParentNotification type={self.alert_type} parent_id={self.parent_id}>"