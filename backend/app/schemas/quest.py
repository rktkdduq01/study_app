from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class QuestType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    SPECIAL = "special"
    STORY = "story"
    CHALLENGE = "challenge"


class QuestDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


class QuestStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class QuestBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=1000)
    quest_type: QuestType
    difficulty: QuestDifficulty
    subject: Optional[str] = None
    objectives: List[Dict[str, Any]] = Field(default_factory=list)
    exp_reward: int = Field(ge=0, default=0)
    coin_reward: int = Field(ge=0, default=0)
    gem_reward: int = Field(ge=0, default=0)
    achievement_points: int = Field(ge=0, default=0)
    time_limit_minutes: Optional[int] = Field(None, ge=1)
    min_level: int = Field(ge=1, default=1)
    max_attempts: Optional[int] = Field(None, ge=1)
    prerequisites: Optional[List[int]] = None
    is_repeatable: bool = False
    cooldown_hours: Optional[int] = Field(None, ge=0)


class QuestCreate(QuestBase):
    @validator('title')
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError('Quest title cannot be empty')
        return v.strip()

    @validator('description')
    def validate_description(cls, v):
        if not v.strip():
            raise ValueError('Quest description cannot be empty')
        return v.strip()

    @validator('objectives')
    def validate_objectives(cls, v):
        if not v:
            raise ValueError('Quest must have at least one objective')
        return v


class QuestUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1, max_length=1000)
    quest_type: Optional[QuestType] = None
    difficulty: Optional[QuestDifficulty] = None
    subject: Optional[str] = None
    objectives: Optional[List[Dict[str, Any]]] = None
    exp_reward: Optional[int] = Field(None, ge=0)
    coin_reward: Optional[int] = Field(None, ge=0)
    gem_reward: Optional[int] = Field(None, ge=0)
    achievement_points: Optional[int] = Field(None, ge=0)
    time_limit_minutes: Optional[int] = Field(None, ge=1)
    min_level: Optional[int] = Field(None, ge=1)
    max_attempts: Optional[int] = Field(None, ge=1)
    prerequisites: Optional[List[int]] = None
    is_repeatable: Optional[bool] = None
    cooldown_hours: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class QuestResponse(QuestBase):
    id: int
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QuestProgressBase(BaseModel):
    user_id: int
    quest_id: int
    status: QuestStatus = QuestStatus.NOT_STARTED
    progress: Dict[str, Any] = Field(default_factory=dict)
    attempts: int = Field(ge=0, default=0)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_attempt_at: Optional[datetime] = None


class QuestProgressCreate(BaseModel):
    quest_id: int


class QuestProgressUpdate(BaseModel):
    status: Optional[QuestStatus] = None
    progress: Optional[Dict[str, Any]] = None
    
    @validator('progress')
    def validate_progress(cls, v):
        if v is not None and not isinstance(v, dict):
            raise ValueError('Progress must be a dictionary')
        return v


class QuestProgressResponse(BaseModel):
    id: int
    user_id: int
    quest_id: int
    status: QuestStatus
    progress: Dict[str, Any]
    attempts: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    last_attempt_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    quest: QuestResponse

    class Config:
        from_attributes = True


class QuestSubmission(BaseModel):
    quest_progress_id: int
    answers: Dict[str, Any]
    time_spent_seconds: Optional[int] = Field(None, ge=0)
    
    @validator('answers')
    def validate_answers(cls, v):
        if not v:
            raise ValueError('Answers cannot be empty')
        return v


class QuestResult(BaseModel):
    quest_progress_id: int
    is_correct: bool
    score: float = Field(ge=0, le=100)
    feedback: Optional[str] = None
    exp_earned: int = 0
    coins_earned: int = 0
    gems_earned: int = 0
    achievement_points_earned: int = 0
    objectives_completed: List[str] = []
    new_achievements: List[int] = []


class QuestStats(BaseModel):
    total_quests_available: int = 0
    quests_completed: int = 0
    quests_in_progress: int = 0
    total_exp_earned: int = 0
    total_coins_earned: int = 0
    total_gems_earned: int = 0
    completion_rate: float = 0.0
    average_score: float = 0.0
    quests_by_type: Dict[str, Dict[str, int]] = {}
    quests_by_difficulty: Dict[str, Dict[str, int]] = {}


class DailyQuestSet(BaseModel):
    date: datetime
    quests: List[QuestResponse]
    completed_count: int = 0
    total_count: int = 0


class QuestRecommendation(BaseModel):
    quest: QuestResponse
    recommendation_score: float = Field(ge=0, le=1)
    reason: str
    estimated_completion_time: int  # in minutes
    difficulty_match: float = Field(ge=0, le=1)