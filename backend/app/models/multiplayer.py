from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Boolean, JSON, Float, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from datetime import datetime
import enum

class SessionType(enum.Enum):
    COOP_QUEST = "coop_quest"
    PVP_BATTLE = "pvp_battle"
    STUDY_GROUP = "study_group"
    TOURNAMENT = "tournament"

class SessionStatus(enum.Enum):
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class MultiplayerSession(Base):
    __tablename__ = "multiplayer_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_code = Column(String(10), unique=True, index=True)  # For easy joining
    
    # Session info
    type = Column(SQLEnum(SessionType), nullable=False)
    status = Column(SQLEnum(SessionStatus), default=SessionStatus.WAITING)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Session settings
    max_players = Column(Integer, default=4)
    min_players = Column(Integer, default=2)
    is_public = Column(Boolean, default=True)
    difficulty = Column(Integer, default=1)  # 1-5
    
    # For quest/battle sessions
    quest_id = Column(Integer, ForeignKey('quests.id'), nullable=True)
    subject_id = Column(Integer, ForeignKey('subjects.id'), nullable=True)
    
    # Timing
    scheduled_start = Column(DateTime)
    actual_start = Column(DateTime)
    end_time = Column(DateTime)
    duration_minutes = Column(Integer)
    
    # Creator
    creator_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = relationship("User", foreign_keys=[creator_id])
    participants = relationship("SessionParticipant", back_populates="session", cascade="all, delete-orphan")
    quest = relationship("Quest")
    chat_room = relationship("ChatRoom", back_populates="party", uselist=False)
    
    def can_join(self, user_id: int) -> tuple[bool, str]:
        """Check if a user can join the session"""
        if self.status != SessionStatus.WAITING:
            return False, "Session already started"
        
        current_players = len([p for p in self.participants if p.status == 'active'])
        if current_players >= self.max_players:
            return False, "Session is full"
        
        if any(p.user_id == user_id for p in self.participants):
            return False, "Already in session"
        
        return True, "Can join"
    
    def can_start(self) -> tuple[bool, str]:
        """Check if session can start"""
        active_players = len([p for p in self.participants if p.status == 'active'])
        if active_players < self.min_players:
            return False, f"Need at least {self.min_players} players"
        return True, "Can start"

class SessionParticipant(Base):
    __tablename__ = "session_participants"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('multiplayer_sessions.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Participant info
    status = Column(String(20), default='active')  # active, disconnected, left, kicked
    role = Column(String(20), default='member')  # leader, member
    team = Column(Integer)  # For team-based sessions
    
    # Performance tracking
    score = Column(Integer, default=0)
    accuracy = Column(Float, default=0.0)
    questions_answered = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    
    # Rewards earned
    experience_earned = Column(Integer, default=0)
    coins_earned = Column(Integer, default=0)
    items_earned = Column(JSON, default=[])
    
    # Connection info
    last_ping = Column(DateTime)
    connection_quality = Column(String(20), default='good')  # good, fair, poor
    
    # Timestamps
    joined_at = Column(DateTime, default=datetime.utcnow)
    left_at = Column(DateTime)
    
    # Relationships
    session = relationship("MultiplayerSession", back_populates="participants")
    user = relationship("User")

class PvPBattle(Base):
    __tablename__ = "pvp_battles"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('multiplayer_sessions.id'), nullable=False)
    
    # Battle settings
    battle_mode = Column(String(50), nullable=False)  # quick_match, ranked, tournament
    time_limit_seconds = Column(Integer, default=300)  # 5 minutes default
    question_pool_size = Column(Integer, default=20)
    
    # Results
    winner_id = Column(Integer, ForeignKey('users.id'))
    draw = Column(Boolean, default=False)
    
    # Battle data
    battle_log = Column(JSON, default=[])  # Detailed log of battle events
    final_scores = Column(JSON, default={})  # {user_id: score}
    
    # Rating changes (for ranked battles)
    rating_changes = Column(JSON, default={})  # {user_id: {before: X, after: Y, change: Z}}
    
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Relationships
    session = relationship("MultiplayerSession")
    winner = relationship("User")

class StudyGroup(Base):
    __tablename__ = "study_groups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Group settings
    is_public = Column(Boolean, default=True)
    max_members = Column(Integer, default=10)
    subject_focus = Column(String(100))  # Primary subject
    
    # Group stats
    total_study_hours = Column(Float, default=0.0)
    average_performance = Column(Float, default=0.0)
    
    # Schedule
    regular_schedule = Column(JSON, default={})  # {day: time} for regular meetings
    
    # Creator and moderators
    creator_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    moderator_ids = Column(JSON, default=[])
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = relationship("User")
    members = relationship("StudyGroupMember", back_populates="group", cascade="all, delete-orphan")
    sessions = relationship("StudyGroupSession", back_populates="group", cascade="all, delete-orphan")

class StudyGroupMember(Base):
    __tablename__ = "study_group_members"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey('study_groups.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Member stats
    attendance_rate = Column(Float, default=100.0)
    contribution_score = Column(Integer, default=0)
    sessions_attended = Column(Integer, default=0)
    
    joined_at = Column(DateTime, default=datetime.utcnow)
    left_at = Column(DateTime)
    
    # Relationships
    group = relationship("StudyGroup", back_populates="members")
    user = relationship("User")

class StudyGroupSession(Base):
    __tablename__ = "study_group_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey('study_groups.id'), nullable=False)
    multiplayer_session_id = Column(Integer, ForeignKey('multiplayer_sessions.id'))
    
    # Session details
    topic = Column(String(200), nullable=False)
    objectives = Column(JSON, default=[])
    materials = Column(JSON, default=[])  # Links to study materials
    
    # Results
    attendee_count = Column(Integer, default=0)
    average_score = Column(Float, default=0.0)
    key_learnings = Column(JSON, default=[])
    
    scheduled_at = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=60)
    
    # Relationships
    group = relationship("StudyGroup", back_populates="sessions")
    multiplayer_session = relationship("MultiplayerSession")