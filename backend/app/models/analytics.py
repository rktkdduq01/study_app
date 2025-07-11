from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey, Text, Boolean, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base

class UserActivity(Base):
    __tablename__ = "user_activities"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    activity_type = Column(String(50), nullable=False)  # login, logout, quest_complete, lesson_complete, etc.
    activity_data = Column(JSON, default={})
    duration_seconds = Column(Integer, default=0)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="activities")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_user_activity_type', 'user_id', 'activity_type'),
        Index('idx_activity_created_at', 'created_at'),
    )

class LearningProgress(Base):
    __tablename__ = "learning_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    content_id = Column(Integer, ForeignKey("content.id"))
    quest_id = Column(Integer, ForeignKey("quests.id"))
    
    progress_percentage = Column(Float, default=0.0)
    time_spent_seconds = Column(Integer, default=0)
    attempts = Column(Integer, default=0)
    score = Column(Float)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    subject = relationship("Subject")
    content = relationship("Content")
    quest = relationship("Quest")
    
    __table_args__ = (
        Index('idx_learning_progress_user_subject', 'user_id', 'subject_id'),
        Index('idx_learning_progress_completed', 'completed'),
    )

class PerformanceMetric(Base):
    __tablename__ = "performance_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    metric_type = Column(String(50), nullable=False)  # accuracy, speed, consistency, engagement
    metric_value = Column(Float, nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    
    period_type = Column(String(20), nullable=False)  # daily, weekly, monthly, yearly
    period_date = Column(DateTime, nullable=False)
    
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    subject = relationship("Subject")
    
    __table_args__ = (
        Index('idx_performance_user_type', 'user_id', 'metric_type'),
        Index('idx_performance_period', 'period_type', 'period_date'),
    )

class GameplayAnalytics(Base):
    __tablename__ = "gameplay_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String(100), nullable=False)
    
    event_type = Column(String(50), nullable=False)  # level_up, achievement_unlock, item_acquired, etc.
    event_data = Column(JSON, default={})
    
    character_level = Column(Integer)
    total_xp = Column(Integer)
    play_time_seconds = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    
    __table_args__ = (
        Index('idx_gameplay_user_session', 'user_id', 'session_id'),
        Index('idx_gameplay_event_type', 'event_type'),
    )

class ContentEffectiveness(Base):
    __tablename__ = "content_effectiveness"
    
    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("content.id"), nullable=False)
    
    view_count = Column(Integer, default=0)
    completion_count = Column(Integer, default=0)
    average_score = Column(Float)
    average_time_seconds = Column(Integer)
    
    engagement_rate = Column(Float)  # percentage of users who interact
    difficulty_rating = Column(Float)  # user-perceived difficulty
    effectiveness_score = Column(Float)  # calculated effectiveness metric
    
    last_calculated = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    content = relationship("Content")

class UserEngagement(Base):
    __tablename__ = "user_engagement"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    
    login_count = Column(Integer, default=0)
    active_minutes = Column(Integer, default=0)
    lessons_completed = Column(Integer, default=0)
    quests_completed = Column(Integer, default=0)
    achievements_earned = Column(Integer, default=0)
    
    interaction_count = Column(Integer, default=0)  # total interactions
    streak_days = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User")
    
    __table_args__ = (
        Index('idx_engagement_user_date', 'user_id', 'date'),
    )

class ReportSnapshot(Base):
    __tablename__ = "report_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    report_type = Column(String(50), nullable=False)  # daily, weekly, monthly, custom
    report_data = Column(JSON, nullable=False)
    
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    
    generated_by = Column(Integer, ForeignKey("users.id"))
    generated_at = Column(DateTime, default=datetime.utcnow)
    
    # For scheduled reports
    is_scheduled = Column(Boolean, default=False)
    recipients = Column(JSON, default=[])  # list of email addresses
    
    # Relationships
    generator = relationship("User")

class AggregatedMetrics(Base):
    __tablename__ = "aggregated_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    
    dimension_type = Column(String(50))  # user, subject, content, global
    dimension_id = Column(Integer)  # ID of the dimension (user_id, subject_id, etc.)
    
    aggregation_type = Column(String(20), nullable=False)  # sum, avg, count, max, min
    period_type = Column(String(20), nullable=False)  # hourly, daily, weekly, monthly
    period_date = Column(DateTime, nullable=False)
    
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_aggregated_metric_period', 'metric_name', 'period_type', 'period_date'),
        Index('idx_aggregated_dimension', 'dimension_type', 'dimension_id'),
    )

class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"
    
    id = Column(Integer, primary_key=True, index=True)
    event_name = Column(String(100), nullable=False)
    event_category = Column(String(50), nullable=False)
    
    user_id = Column(Integer, ForeignKey("users.id"))
    session_id = Column(String(100))
    
    properties = Column(JSON, default={})
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # For A/B testing
    experiment_id = Column(String(50))
    variant_id = Column(String(50))
    
    # Relationships
    user = relationship("User")
    
    __table_args__ = (
        Index('idx_analytics_event_name', 'event_name', 'timestamp'),
        Index('idx_analytics_user_session', 'user_id', 'session_id'),
    )