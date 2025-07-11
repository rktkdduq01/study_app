from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class AchievementCategory(str, Enum):
    ACADEMIC = "academic"
    CONSISTENCY = "consistency"
    MASTERY = "mastery"
    SOCIAL = "social"
    SPECIAL = "special"
    MILESTONE = "milestone"


class AchievementRarity(str, Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class AchievementBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    category: AchievementCategory
    rarity: AchievementRarity = AchievementRarity.COMMON
    icon_name: Optional[str] = None
    badge_color: str = "#4CAF50"
    points: int = Field(ge=0, default=10)
    max_progress: int = Field(ge=1, default=1)
    is_hidden: bool = False
    requirements: Optional[Dict[str, Any]] = None
    xp_bonus: int = Field(ge=0, default=50)
    coin_bonus: int = Field(ge=0, default=20)
    gem_bonus: int = Field(ge=0, default=5)
    title_reward: Optional[str] = None


class AchievementCreate(AchievementBase):
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Achievement name cannot be empty')
        return v.strip()

    @validator('description')
    def validate_description(cls, v):
        if not v.strip():
            raise ValueError('Achievement description cannot be empty')
        return v.strip()


class AchievementUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    category: Optional[AchievementCategory] = None
    rarity: Optional[AchievementRarity] = None
    icon_name: Optional[str] = None
    badge_color: Optional[str] = None
    points: Optional[int] = Field(None, ge=0)
    max_progress: Optional[int] = Field(None, ge=1)
    is_hidden: Optional[bool] = None
    requirements: Optional[Dict[str, Any]] = None
    xp_bonus: Optional[int] = Field(None, ge=0)
    coin_bonus: Optional[int] = Field(None, ge=0)
    gem_bonus: Optional[int] = Field(None, ge=0)
    title_reward: Optional[str] = None
    is_active: Optional[bool] = None


class AchievementResponse(AchievementBase):
    id: int
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserAchievementBase(BaseModel):
    user_id: int
    achievement_id: int
    current_progress: int = Field(ge=0, default=0)
    is_completed: bool = False
    earned_at: Optional[datetime] = None


class UserAchievementCreate(BaseModel):
    achievement_id: int


class UserAchievementProgressUpdate(BaseModel):
    progress: int = Field(ge=0)
    
    @validator('progress')
    def validate_progress(cls, v):
        if v < 0:
            raise ValueError('Progress cannot be negative')
        return v


class UserAchievementResponse(BaseModel):
    id: int
    user_id: int
    achievement_id: int
    current_progress: int
    is_completed: bool
    earned_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    achievement: AchievementResponse

    class Config:
        from_attributes = True


class AchievementStats(BaseModel):
    total_achievements: int = 0
    completed_achievements: int = 0
    total_points: int = 0
    earned_points: int = 0
    completion_percentage: float = 0.0
    achievements_by_category: Dict[str, Dict[str, int]] = {}
    achievements_by_rarity: Dict[str, Dict[str, int]] = {}


class AchievementLeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    username: str
    total_points: int
    completed_achievements: int
    avatar_url: Optional[str] = None
    
    class Config:
        from_attributes = True


class AchievementNotification(BaseModel):
    achievement_id: int
    achievement_name: str
    achievement_description: str
    achievement_rarity: AchievementRarity
    points_earned: int
    completed_at: datetime
    is_new: bool = True