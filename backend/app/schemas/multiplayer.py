from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum

# Enums
class SessionTypeEnum(str, Enum):
    coop_quest = "coop_quest"
    pvp_battle = "pvp_battle"
    study_group = "study_group"
    tournament = "tournament"

class SessionStatusEnum(str, Enum):
    waiting = "waiting"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"

# Session schemas
class SessionCreate(BaseModel):
    type: SessionTypeEnum
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None
    max_players: int = Field(default=4, ge=2, le=20)
    is_public: bool = True
    quest_id: Optional[int] = None
    subject_id: Optional[int] = None
    difficulty: int = Field(default=1, ge=1, le=5)

class SessionJoin(BaseModel):
    session_code: str = Field(..., min_length=6, max_length=6)

class SessionResponse(BaseModel):
    id: int
    code: str
    type: str
    name: str
    status: str
    participants: int
    max_players: int
    creator_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Guild schemas
class GuildCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=50)
    description: Optional[str] = None
    tag: Optional[str] = Field(None, min_length=2, max_length=5)
    is_public: bool = True

class GuildResponse(BaseModel):
    id: int
    name: str
    tag: str
    level: str
    member_count: int
    max_members: int
    owner_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class GuildMemberResponse(BaseModel):
    user_id: int
    username: str
    role: str
    contribution_points: int
    joined_at: datetime

    class Config:
        from_attributes = True

class GuildQuestCreate(BaseModel):
    quest_id: int
    min_participants: int = Field(default=3, ge=1, le=10)
    max_participants: int = Field(default=10, ge=2, le=50)

class GuildAnnouncementCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=2000)
    priority: str = Field(default="normal", regex="^(low|normal|high|urgent)$")
    expires_at: Optional[datetime] = None

# Friend schemas
class FriendRequestCreate(BaseModel):
    receiver_id: int
    message: Optional[str] = Field(None, max_length=500)

class FriendRequestResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class FriendshipResponse(BaseModel):
    id: int
    friend_id: int
    friend_username: str
    friendship_level: int
    is_online: bool
    last_interaction: Optional[datetime]

    class Config:
        from_attributes = True

# Chat schemas
class ChatMessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)
    message_type: str = Field(default="text", regex="^(text|image|system|achievement)$")
    reply_to_id: Optional[int] = None
    attachments: Optional[List[Dict[str, Any]]] = []

class ChatMessageResponse(BaseModel):
    id: int
    room_id: int
    sender_id: int
    content: str
    message_type: str
    created_at: datetime

    class Config:
        from_attributes = True

class ChatRoomResponse(BaseModel):
    id: int
    name: Optional[str]
    type: str
    participant_count: int
    unread_count: int
    last_message: Optional[ChatMessageResponse]

    class Config:
        from_attributes = True

# PvP Battle schemas
class BattleAnswerSubmit(BaseModel):
    answer: str
    time_taken: float = Field(..., ge=0)

class BattleResultResponse(BaseModel):
    winner_id: Optional[int]
    draw: bool
    final_scores: Dict[int, int]
    rating_changes: Dict[int, Dict[str, int]]
    rewards: Dict[str, Any]

    class Config:
        from_attributes = True

# Study Group schemas
class StudyGroupCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None
    is_public: bool = True
    max_members: int = Field(default=10, ge=2, le=50)
    subject_focus: Optional[str] = None
    regular_schedule: Optional[Dict[str, str]] = {}

class StudyGroupResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    member_count: int
    total_study_hours: float
    average_performance: float
    creator_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# WebSocket message schemas
class WSMessage(BaseModel):
    type: str
    data: Dict[str, Any]
    timestamp: Optional[datetime] = None

class WSTypingIndicator(BaseModel):
    room_id: int
    is_typing: bool

class WSUserStatus(BaseModel):
    user_id: int
    status: str  # online, offline, away, busy

# Leaderboard schemas
class LeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    username: str
    score: int
    character_class: Optional[str]
    guild_name: Optional[str]

class PvPLeaderboardEntry(LeaderboardEntry):
    rating: int
    wins: int
    losses: int
    win_rate: float