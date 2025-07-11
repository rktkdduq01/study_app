from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.core.config import settings


class Character(Base):
    """Game character model - represents the player's in-game avatar"""
    __tablename__ = "characters"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Character info
    name = Column(String, nullable=False)
    avatar_type = Column(String, default="warrior")  # warrior, mage, scholar, etc.
    
    # Overall stats
    level = Column(Integer, default=settings.INITIAL_USER_LEVEL)
    total_xp = Column(Integer, default=settings.INITIAL_USER_XP)
    hp = Column(Integer, default=100)
    max_hp = Column(Integer, default=100)
    
    # Game currency
    coins = Column(Integer, default=0)
    gems = Column(Integer, default=0)
    
    # RPG Stats
    strength = Column(Integer, default=10)  # 문제 해결력
    intelligence = Column(Integer, default=10)  # 학습 속도
    wisdom = Column(Integer, default=10)  # 이해도
    charisma = Column(Integer, default=10)  # 협동 능력
    
    # Equipment and inventory (JSON)
    equipment = Column(JSON, default={})
    inventory = Column(JSON, default=[])
    
    # Achievements and titles
    titles = Column(JSON, default=[])
    active_title = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="character")
    subject_levels = relationship("SubjectLevel", back_populates="character", cascade="all, delete-orphan")
    
    def calculate_level_from_xp(self):
        """Calculate level based on total XP"""
        # Simple level calculation: level = sqrt(xp / 100)
        import math
        return max(1, int(math.sqrt(self.total_xp / 100)))
    
    def __repr__(self):
        return f"<Character {self.name} (Level {self.level})>"


class SubjectLevel(Base):
    """Subject-specific level tracking"""
    __tablename__ = "subject_levels"
    
    id = Column(Integer, primary_key=True, index=True)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    subject = Column(String, nullable=False)  # math, korean, science, english, programming
    
    # Level and XP
    level = Column(Integer, default=1)
    current_xp = Column(Integer, default=0)
    total_xp = Column(Integer, default=0)
    
    # Subject-specific stats
    mastery_points = Column(Integer, default=0)
    skill_points = Column(Integer, default=0)
    
    # Performance metrics
    accuracy_rate = Column(Float, default=0.0)
    completion_rate = Column(Float, default=0.0)
    average_time_per_quest = Column(Float, default=0.0)
    
    # Streaks
    current_streak = Column(Integer, default=0)
    best_streak = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    character = relationship("Character", back_populates="subject_levels")
    
    def __repr__(self):
        return f"<SubjectLevel {self.subject} Level {self.level}>"