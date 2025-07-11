from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class AchievementCategory(str, enum.Enum):
    """Achievement category types"""
    ACADEMIC = "academic"  # 학업 성취
    CONSISTENCY = "consistency"  # 꾸준함
    MASTERY = "mastery"  # 숙달
    SOCIAL = "social"  # 사회성
    SPECIAL = "special"  # 특별 이벤트
    MILESTONE = "milestone"  # 마일스톤


class AchievementRarity(str, enum.Enum):
    """Achievement rarity levels"""
    COMMON = "common"  # 일반
    UNCOMMON = "uncommon"  # 희귀
    RARE = "rare"  # 영웅
    EPIC = "epic"  # 전설
    LEGENDARY = "legendary"  # 신화


class Achievement(Base):
    """Achievement model - represents badges and accomplishments"""
    __tablename__ = "achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Achievement information
    name = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=False)
    category = Column(SQLEnum(AchievementCategory), default=AchievementCategory.ACADEMIC)
    rarity = Column(SQLEnum(AchievementRarity), default=AchievementRarity.COMMON)
    
    # Visual elements
    icon_name = Column(String, nullable=False)  # Icon identifier
    badge_color = Column(String, default="#4CAF50")  # Hex color
    
    # Requirements (JSON)
    requirements = Column(JSON, nullable=False)
    # Example: {
    #   "type": "quest_completion",
    #   "subject": "math",
    #   "count": 10,
    #   "difficulty": "hard"
    # }
    
    # Rewards
    xp_bonus = Column(Integer, default=50)
    coin_bonus = Column(Integer, default=20)
    gem_bonus = Column(Integer, default=5)
    title_reward = Column(String, nullable=True)  # Special title
    
    # Progress tracking
    max_progress = Column(Integer, default=1)  # For progressive achievements
    is_repeatable = Column(Boolean, default=False)
    
    # Visibility
    is_hidden = Column(Boolean, default=False)  # Hidden until unlocked
    is_active = Column(Boolean, default=True)
    
    # Stats
    points = Column(Integer, default=10)
    times_earned = Column(Integer, default=0)
    first_earned_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Special flags
    is_seasonal = Column(Boolean, default=False)
    season = Column(String, nullable=True)  # "2024-spring", etc.
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user_achievements = relationship("UserAchievement", back_populates="achievement", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Achievement {self.name} ({self.rarity})>"


class UserAchievement(Base):
    """Track which achievements users have earned"""
    __tablename__ = "user_achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    achievement_id = Column(Integer, ForeignKey("achievements.id"), nullable=False)
    
    # Progress tracking
    current_progress = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)
    completion_count = Column(Integer, default=0)  # For repeatable achievements
    
    # Notification status
    is_claimed = Column(Boolean, default=False)  # Rewards claimed
    is_notified = Column(Boolean, default=False)  # User notified
    
    # Timestamps
    earned_at = Column(DateTime(timezone=True), nullable=True)
    claimed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="achievements")
    achievement = relationship("Achievement", back_populates="user_achievements")
    
    def __repr__(self):
        return f"<UserAchievement user_id={self.user_id} achievement_id={self.achievement_id} completed={self.is_completed}>"