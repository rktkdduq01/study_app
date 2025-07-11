from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from enum import Enum


class SubjectType(str, Enum):
    MATH = "math"
    KOREAN = "korean"
    ENGLISH = "english"
    SCIENCE = "science"
    SOCIAL = "social"
    HISTORY = "history"


class SubjectLevelBase(BaseModel):
    subject: SubjectType
    level: int = Field(ge=1, le=100, default=1)
    experience: int = Field(ge=0, default=0)
    exp_to_next_level: int = Field(ge=0, default=100)


class SubjectLevelCreate(SubjectLevelBase):
    character_id: int


class SubjectLevelUpdate(BaseModel):
    level: Optional[int] = Field(None, ge=1, le=100)
    experience: Optional[int] = Field(None, ge=0)
    exp_to_next_level: Optional[int] = Field(None, ge=0)


class SubjectLevelResponse(SubjectLevelBase):
    id: int
    character_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CharacterBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    avatar_url: Optional[str] = None
    total_level: int = Field(ge=1, default=1)
    total_experience: int = Field(ge=0, default=0)
    coins: int = Field(ge=0, default=0)
    gems: int = Field(ge=0, default=0)
    streak_days: int = Field(ge=0, default=0)
    last_active_date: Optional[datetime] = None


class CharacterCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    avatar_url: Optional[str] = None
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Character name cannot be empty')
        return v.strip()


class CharacterUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    avatar_url: Optional[str] = None
    total_level: Optional[int] = Field(None, ge=1)
    total_experience: Optional[int] = Field(None, ge=0)
    coins: Optional[int] = Field(None, ge=0)
    gems: Optional[int] = Field(None, ge=0)
    streak_days: Optional[int] = Field(None, ge=0)
    last_active_date: Optional[datetime] = None

    @validator('name')
    def validate_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Character name cannot be empty')
        return v.strip() if v else v


class CharacterResponse(CharacterBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    subject_levels: List[SubjectLevelResponse] = []

    class Config:
        from_attributes = True


class CharacterWithStats(CharacterResponse):
    quests_completed: int = 0
    achievements_earned: int = 0
    total_study_time_minutes: int = 0
    
    class Config:
        from_attributes = True


class ExperienceGain(BaseModel):
    subject: SubjectType
    experience_gained: int = Field(gt=0)
    reason: Optional[str] = None


class CurrencyUpdate(BaseModel):
    coins: Optional[int] = Field(None, ge=0)
    gems: Optional[int] = Field(None, ge=0)
    reason: Optional[str] = None


class CharacterRanking(BaseModel):
    rank: int
    character_id: int
    character_name: str
    user_id: int
    total_level: int
    total_experience: int
    avatar_url: Optional[str] = None
    
    class Config:
        from_attributes = True