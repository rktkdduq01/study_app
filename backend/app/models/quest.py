from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class QuestType(str, enum.Enum):
    """Quest type enumeration"""
    PRACTICE = "practice"  # 연습 문제
    CHALLENGE = "challenge"  # 도전 과제
    DAILY = "daily"  # 일일 퀘스트
    WEEKLY = "weekly"  # 주간 퀘스트
    SPECIAL = "special"  # 특별 이벤트


class QuestDifficulty(str, enum.Enum):
    """Quest difficulty levels"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


class QuestStatus(str, enum.Enum):
    """Quest completion status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class Quest(Base):
    """Quest model - represents learning tasks and challenges"""
    __tablename__ = "quests"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Quest information
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    subject = Column(String, nullable=False)  # math, korean, science, etc.
    quest_type = Column(SQLEnum(QuestType), default=QuestType.PRACTICE)
    difficulty = Column(SQLEnum(QuestDifficulty), default=QuestDifficulty.MEDIUM)
    
    # Requirements and rewards
    min_level = Column(Integer, default=1)
    max_level = Column(Integer, nullable=True)
    xp_reward = Column(Integer, default=10)
    coin_reward = Column(Integer, default=5)
    gem_reward = Column(Integer, default=0)
    
    # Quest content (JSON)
    content = Column(JSON, nullable=False)  # Questions, tasks, etc.
    answer_key = Column(JSON, nullable=True)  # Correct answers
    hints = Column(JSON, default=[])  # Hint system
    
    # AI-generated flags
    is_ai_generated = Column(Boolean, default=False)
    ai_prompt = Column(Text, nullable=True)  # Prompt used for generation
    ai_model = Column(String, nullable=True)  # Model used (gpt-4, claude, etc.)
    
    # Timing
    time_limit = Column(Integer, nullable=True)  # Time limit in seconds
    available_from = Column(DateTime(timezone=True), nullable=True)
    available_until = Column(DateTime(timezone=True), nullable=True)
    
    # Stats
    times_completed = Column(Integer, default=0)
    average_completion_time = Column(Integer, default=0)  # In seconds
    success_rate = Column(Integer, default=0)  # Percentage
    
    # Flags
    is_active = Column(Boolean, default=True)
    requires_parent_approval = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    progress_records = relationship("QuestProgress", back_populates="quest", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Quest {self.title} ({self.subject})>"


class QuestProgress(Base):
    """Track user progress on quests"""
    __tablename__ = "quest_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    quest_id = Column(Integer, ForeignKey("quests.id"), nullable=False)
    
    # Progress tracking
    status = Column(SQLEnum(QuestStatus), default=QuestStatus.NOT_STARTED)
    progress_percentage = Column(Integer, default=0)
    score = Column(Integer, default=0)
    
    # Attempts and answers
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    user_answers = Column(JSON, default={})  # Store user's answers
    
    # Time tracking
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    time_spent = Column(Integer, default=0)  # Total seconds spent
    
    # Rewards earned
    xp_earned = Column(Integer, default=0)
    coins_earned = Column(Integer, default=0)
    gems_earned = Column(Integer, default=0)
    
    # Feedback
    feedback = Column(Text, nullable=True)  # AI or teacher feedback
    rating = Column(Integer, nullable=True)  # User rating 1-5
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="quest_progress")
    quest = relationship("Quest", back_populates="progress_records")
    
    def __repr__(self):
        return f"<QuestProgress user_id={self.user_id} quest_id={self.quest_id} status={self.status}>"