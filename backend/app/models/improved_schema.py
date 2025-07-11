"""
Improved Database Schema Design
This file demonstrates the improved ERD structure with fixes for identified issues
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, JSON, Text, Float, CheckConstraint, Index, UniqueConstraint
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime
from typing import Optional

from app.db.base_class import Base

# ============= CORE USER ENTITIES =============

class User(Base):
    """Streamlined User model - authentication and basic info only"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_superuser = Column(Boolean, default=False, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    
    # Timestamps with timezone
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True))
    
    # Relationships with proper lazy loading
    profile = relationship("UserProfile", back_populates="user", uselist=False, lazy="select", cascade="all, delete-orphan")
    game_stats = relationship("UserGameStats", back_populates="user", uselist=False, lazy="select", cascade="all, delete-orphan")
    learning_profile = relationship("UserLearningProfile", back_populates="user", uselist=False, lazy="select", cascade="all, delete-orphan")
    
    # Collections - use dynamic loading for large datasets
    quest_progress = relationship("QuestProgress", back_populates="user", lazy="dynamic", cascade="all, delete-orphan")
    achievements = relationship("UserAchievement", back_populates="user", lazy="dynamic", cascade="all, delete-orphan")
    subject_progress = relationship("SubjectProgress", back_populates="user", lazy="dynamic", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_email_active', 'email', 'is_active'),
        Index('idx_user_created_at', 'created_at'),
    )


class UserProfile(Base):
    """User profile information - separated from auth data"""
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    
    # Profile data
    display_name = Column(String(100))
    bio = Column(Text)
    avatar_url = Column(String(500))
    language = Column(String(10), default="ko", nullable=False)
    timezone = Column(String(50), default="Asia/Seoul", nullable=False)
    
    # Preferences stored as relations, not JSON
    notification_settings = Column(JSON, default={})
    ui_preferences = Column(JSON, default={})
    
    # Timestamps
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="profile")
    preferred_subjects = relationship("UserSubjectPreference", back_populates="profile", cascade="all, delete-orphan")


class UserGameStats(Base):
    """Centralized game statistics - single source of truth"""
    __tablename__ = "user_game_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    
    # Character info
    character_class = Column(String(50), default="warrior", nullable=False)
    character_level = Column(Integer, default=1, nullable=False)
    total_xp = Column(Integer, default=0, nullable=False, index=True)
    
    # Currency - single source
    coins = Column(Integer, default=0, nullable=False)
    gems = Column(Integer, default=0, nullable=False)
    
    # Battle stats
    pvp_rating = Column(Integer, default=1000, nullable=False, index=True)
    pvp_wins = Column(Integer, default=0, nullable=False)
    pvp_losses = Column(Integer, default=0, nullable=False)
    pvp_draws = Column(Integer, default=0, nullable=False)
    
    # Guild info
    guild_id = Column(Integer, ForeignKey("guilds.id", ondelete="SET NULL"), index=True)
    guild_contribution_points = Column(Integer, default=0, nullable=False)
    
    # Computed property for win rate
    @hybrid_property
    def pvp_win_rate(self):
        total_matches = self.pvp_wins + self.pvp_losses
        return (self.pvp_wins / total_matches * 100) if total_matches > 0 else 0
    
    # Relationships
    user = relationship("User", back_populates="game_stats")
    guild = relationship("Guild", back_populates="members")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('character_level >= 1', name='check_character_level_positive'),
        CheckConstraint('total_xp >= 0', name='check_xp_non_negative'),
        CheckConstraint('coins >= 0', name='check_coins_non_negative'),
        CheckConstraint('gems >= 0', name='check_gems_non_negative'),
        CheckConstraint('pvp_rating >= 0', name='check_rating_non_negative'),
        Index('idx_game_stats_level_xp', 'character_level', 'total_xp'),
        Index('idx_game_stats_pvp_rating', 'pvp_rating'),
    )


class UserLearningProfile(Base):
    """User's learning statistics and progress"""
    __tablename__ = "user_learning_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    
    # Learning stats
    total_study_minutes = Column(Integer, default=0, nullable=False)
    total_problems_solved = Column(Integer, default=0, nullable=False)
    total_problems_correct = Column(Integer, default=0, nullable=False)
    current_streak_days = Column(Integer, default=0, nullable=False)
    longest_streak_days = Column(Integer, default=0, nullable=False)
    last_study_date = Column(DateTime(timezone=True))
    
    # Learning preferences
    preferred_difficulty = Column(Integer, default=2, nullable=False)  # 1-5 scale
    study_goal_minutes_daily = Column(Integer, default=30, nullable=False)
    
    # Computed accuracy
    @hybrid_property
    def overall_accuracy(self):
        if self.total_problems_solved == 0:
            return 0
        return (self.total_problems_correct / self.total_problems_solved * 100)
    
    # Relationships
    user = relationship("User", back_populates="learning_profile")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('total_study_minutes >= 0', name='check_study_minutes_non_negative'),
        CheckConstraint('preferred_difficulty BETWEEN 1 AND 5', name='check_difficulty_range'),
        CheckConstraint('study_goal_minutes_daily >= 0', name='check_goal_non_negative'),
    )


# ============= SUBJECT AND PROGRESS =============

class Subject(Base):
    """Subject master table"""
    __tablename__ = "subjects"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    icon_url = Column(String(500))
    color_hex = Column(String(7))
    category = Column(String(50), nullable=False, index=True)  # math, science, language, etc.
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    progress_records = relationship("SubjectProgress", back_populates="subject", lazy="dynamic")
    contents = relationship("Content", back_populates="subject", lazy="dynamic")
    
    # Indexes
    __table_args__ = (
        Index('idx_subject_category_active', 'category', 'is_active'),
    )


class SubjectProgress(Base):
    """User's progress in each subject"""
    __tablename__ = "subject_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Progress data
    level = Column(Integer, default=1, nullable=False)
    current_xp = Column(Integer, default=0, nullable=False)
    total_xp = Column(Integer, default=0, nullable=False)
    mastery_level = Column(Integer, default=0, nullable=False)  # 0-100
    
    # Statistics
    total_time_minutes = Column(Integer, default=0, nullable=False)
    problems_solved = Column(Integer, default=0, nullable=False)
    problems_correct = Column(Integer, default=0, nullable=False)
    last_activity_at = Column(DateTime(timezone=True))
    
    # Computed accuracy for this subject
    @hybrid_property
    def accuracy_rate(self):
        if self.problems_solved == 0:
            return 0
        return (self.problems_correct / self.problems_solved * 100)
    
    # Relationships
    user = relationship("User", back_populates="subject_progress")
    subject = relationship("Subject", back_populates="progress_records")
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('user_id', 'subject_id', name='uq_user_subject'),
        CheckConstraint('level >= 1', name='check_subject_level_positive'),
        CheckConstraint('mastery_level BETWEEN 0 AND 100', name='check_mastery_range'),
        Index('idx_subject_progress_user_subject', 'user_id', 'subject_id'),
        Index('idx_subject_progress_level', 'level'),
    )


class UserSubjectPreference(Base):
    """User's subject preferences - normalized from JSON"""
    __tablename__ = "user_subject_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    preference_level = Column(Integer, default=3, nullable=False)  # 1-5 scale
    
    # Relationships
    profile = relationship("UserProfile", back_populates="preferred_subjects")
    subject = relationship("Subject")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('profile_id', 'subject_id', name='uq_profile_subject_pref'),
        CheckConstraint('preference_level BETWEEN 1 AND 5', name='check_preference_range'),
    )


# ============= QUEST SYSTEM =============

class Quest(Base):
    """Quest definitions"""
    __tablename__ = "quests"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    quest_type = Column(String(50), nullable=False, index=True)  # daily, weekly, story, challenge
    
    # Requirements and content
    requirements = Column(JSON, nullable=False)
    content_id = Column(Integer, ForeignKey("contents.id", ondelete="SET NULL"), index=True)
    
    # Rewards defined in separate table for flexibility
    xp_reward = Column(Integer, default=0, nullable=False)
    coin_reward = Column(Integer, default=0, nullable=False)
    
    # Metadata
    difficulty_level = Column(Integer, default=1, nullable=False)
    estimated_minutes = Column(Integer)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    progress_records = relationship("QuestProgress", back_populates="quest", lazy="dynamic")
    rewards = relationship("QuestReward", back_populates="quest", cascade="all, delete-orphan")
    content = relationship("Content", back_populates="quests")
    
    # Indexes
    __table_args__ = (
        Index('idx_quest_type_active', 'quest_type', 'is_active'),
        Index('idx_quest_difficulty', 'difficulty_level'),
    )


class QuestProgress(Base):
    """User's quest progress"""
    __tablename__ = "quest_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    quest_id = Column(Integer, ForeignKey("quests.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Progress tracking
    status = Column(String(20), default="active", nullable=False, index=True)  # active, completed, failed, expired
    progress_percentage = Column(Integer, default=0, nullable=False)
    progress_data = Column(JSON, default={})
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True))
    last_progress_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="quest_progress")
    quest = relationship("Quest", back_populates="progress_records")
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('user_id', 'quest_id', name='uq_user_quest'),
        CheckConstraint('progress_percentage BETWEEN 0 AND 100', name='check_progress_range'),
        CheckConstraint("status IN ('active', 'completed', 'failed', 'expired')", name='check_quest_status'),
        Index('idx_quest_progress_user_status', 'user_id', 'status'),
        Index('idx_quest_progress_user_quest', 'user_id', 'quest_id'),
    )


class QuestReward(Base):
    """Quest rewards - normalized"""
    __tablename__ = "quest_rewards"
    
    id = Column(Integer, primary_key=True, index=True)
    quest_id = Column(Integer, ForeignKey("quests.id", ondelete="CASCADE"), nullable=False, index=True)
    reward_type = Column(String(50), nullable=False)  # item, achievement, title, etc.
    reward_value = Column(String(255), nullable=False)
    reward_quantity = Column(Integer, default=1, nullable=False)
    
    # Relationships
    quest = relationship("Quest", back_populates="rewards")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('reward_quantity > 0', name='check_reward_quantity_positive'),
    )


# ============= ACHIEVEMENT SYSTEM =============

class Achievement(Base):
    """Achievement definitions"""
    __tablename__ = "achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    category = Column(String(50), nullable=False, index=True)
    
    # Achievement details
    icon_url = Column(String(500))
    points = Column(Integer, default=10, nullable=False)
    requirements = Column(JSON, nullable=False)
    
    # Rarity and order
    rarity = Column(String(20), default="common", nullable=False)  # common, rare, epic, legendary
    display_order = Column(Integer, default=0, nullable=False)
    is_hidden = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user_achievements = relationship("UserAchievement", back_populates="achievement", lazy="dynamic")
    
    # Indexes
    __table_args__ = (
        Index('idx_achievement_category_order', 'category', 'display_order'),
        CheckConstraint("rarity IN ('common', 'rare', 'epic', 'legendary')", name='check_achievement_rarity'),
    )


class UserAchievement(Base):
    """User's earned achievements"""
    __tablename__ = "user_achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    achievement_id = Column(Integer, ForeignKey("achievements.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Achievement data
    earned_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    progress_data = Column(JSON, default={})
    is_claimed = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="achievements")
    achievement = relationship("Achievement", back_populates="user_achievements")
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('user_id', 'achievement_id', name='uq_user_achievement'),
        Index('idx_user_achievement_user_earned', 'user_id', 'earned_at'),
    )


# ============= GUILD SYSTEM =============

class Guild(Base):
    """Guild definitions"""
    __tablename__ = "guilds"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    tag = Column(String(10), unique=True, nullable=False, index=True)
    description = Column(Text)
    
    # Guild details
    leader_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    level = Column(Integer, default=1, nullable=False)
    experience = Column(Integer, default=0, nullable=False)
    max_members = Column(Integer, default=30, nullable=False)
    
    # Guild settings
    is_public = Column(Boolean, default=True, nullable=False, index=True)
    min_level_requirement = Column(Integer, default=1, nullable=False)
    settings = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    leader = relationship("User", foreign_keys=[leader_id])
    members = relationship("UserGameStats", back_populates="guild", lazy="dynamic")
    guild_quests = relationship("GuildQuest", back_populates="guild", lazy="dynamic")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('level >= 1', name='check_guild_level_positive'),
        CheckConstraint('max_members > 0', name='check_max_members_positive'),
        Index('idx_guild_public_level', 'is_public', 'min_level_requirement'),
    )


class GuildQuest(Base):
    """Guild collaborative quests"""
    __tablename__ = "guild_quests"
    
    id = Column(Integer, primary_key=True, index=True)
    guild_id = Column(Integer, ForeignKey("guilds.id", ondelete="CASCADE"), nullable=False, index=True)
    quest_id = Column(Integer, ForeignKey("quests.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Progress tracking
    status = Column(String(20), default="active", nullable=False, index=True)
    total_progress = Column(Integer, default=0, nullable=False)
    required_progress = Column(Integer, nullable=False)
    contributor_count = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Relationships
    guild = relationship("Guild", back_populates="guild_quests")
    quest = relationship("Quest")
    contributions = relationship("GuildQuestContribution", back_populates="guild_quest", cascade="all, delete-orphan")
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('guild_id', 'quest_id', name='uq_guild_quest'),
        CheckConstraint("status IN ('active', 'completed', 'failed', 'expired')", name='check_guild_quest_status'),
        Index('idx_guild_quest_status_expires', 'status', 'expires_at'),
    )


class GuildQuestContribution(Base):
    """Individual contributions to guild quests"""
    __tablename__ = "guild_quest_contributions"
    
    id = Column(Integer, primary_key=True, index=True)
    guild_quest_id = Column(Integer, ForeignKey("guild_quests.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Contribution data
    contribution_amount = Column(Integer, default=0, nullable=False)
    last_contribution_at = Column(DateTime(timezone=True))
    
    # Relationships
    guild_quest = relationship("GuildQuest", back_populates="contributions")
    user = relationship("User")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('guild_quest_id', 'user_id', name='uq_guild_quest_user'),
        CheckConstraint('contribution_amount >= 0', name='check_contribution_non_negative'),
    )


# ============= CONTENT SYSTEM =============

class Content(Base):
    """Learning content"""
    __tablename__ = "contents"
    
    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Content details
    title = Column(String(200), nullable=False)
    content_type = Column(String(50), nullable=False, index=True)  # lesson, quiz, practice, video
    difficulty_level = Column(Integer, nullable=False, index=True)
    
    # Content data
    content_data = Column(JSON, nullable=False)
    metadata = Column(JSON, default={})
    
    # Stats
    estimated_minutes = Column(Integer)
    prerequisite_content_ids = Column(JSON, default=[])
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    version = Column(Integer, default=1, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    subject = relationship("Subject", back_populates="contents")
    quests = relationship("Quest", back_populates="content", lazy="dynamic")
    user_progress = relationship("UserContentProgress", back_populates="content", lazy="dynamic")
    
    # Indexes
    __table_args__ = (
        Index('idx_content_subject_type_active', 'subject_id', 'content_type', 'is_active'),
        Index('idx_content_difficulty', 'difficulty_level'),
        CheckConstraint('difficulty_level BETWEEN 1 AND 5', name='check_content_difficulty_range'),
    )


class UserContentProgress(Base):
    """User's progress on specific content"""
    __tablename__ = "user_content_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content_id = Column(Integer, ForeignKey("contents.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Progress data
    status = Column(String(20), default="not_started", nullable=False)  # not_started, in_progress, completed
    completion_percentage = Column(Integer, default=0, nullable=False)
    best_score = Column(Integer)
    attempt_count = Column(Integer, default=0, nullable=False)
    
    # Time tracking
    total_time_seconds = Column(Integer, default=0, nullable=False)
    first_accessed_at = Column(DateTime(timezone=True))
    last_accessed_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User")
    content = relationship("Content", back_populates="user_progress")
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('user_id', 'content_id', name='uq_user_content'),
        CheckConstraint('completion_percentage BETWEEN 0 AND 100', name='check_content_completion_range'),
        CheckConstraint("status IN ('not_started', 'in_progress', 'completed')", name='check_content_status'),
        Index('idx_user_content_progress', 'user_id', 'content_id', 'status'),
    )


# ============= BATTLE SYSTEM =============

class Battle(Base):
    """PvP battle records"""
    __tablename__ = "battles"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Participants
    challenger_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    defender_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    winner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    
    # Battle details
    battle_type = Column(String(20), nullable=False)  # ranked, friendly, tournament
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="SET NULL"), index=True)
    
    # Scores and ratings
    challenger_score = Column(Integer, default=0, nullable=False)
    defender_score = Column(Integer, default=0, nullable=False)
    challenger_rating_change = Column(Integer, default=0, nullable=False)
    defender_rating_change = Column(Integer, default=0, nullable=False)
    
    # Battle data
    duration_seconds = Column(Integer)
    battle_data = Column(JSON, default={})
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ended_at = Column(DateTime(timezone=True))
    
    # Relationships
    challenger = relationship("User", foreign_keys=[challenger_id])
    defender = relationship("User", foreign_keys=[defender_id])
    winner = relationship("User", foreign_keys=[winner_id])
    subject = relationship("Subject")
    
    # Indexes
    __table_args__ = (
        Index('idx_battle_users_started', 'challenger_id', 'defender_id', 'started_at'),
        Index('idx_battle_type_started', 'battle_type', 'started_at'),
        CheckConstraint("battle_type IN ('ranked', 'friendly', 'tournament')", name='check_battle_type'),
    )


# ============= ANALYTICS TABLES =============

class DailyUserActivity(Base):
    """Daily aggregated user activity"""
    __tablename__ = "daily_user_activity"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    activity_date = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Aggregated metrics
    study_minutes = Column(Integer, default=0, nullable=False)
    problems_attempted = Column(Integer, default=0, nullable=False)
    problems_correct = Column(Integer, default=0, nullable=False)
    quests_completed = Column(Integer, default=0, nullable=False)
    xp_earned = Column(Integer, default=0, nullable=False)
    battles_participated = Column(Integer, default=0, nullable=False)
    
    # Subject breakdown (stored as JSON for flexibility)
    subject_breakdown = Column(JSON, default={})
    
    # Relationships
    user = relationship("User")
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('user_id', 'activity_date', name='uq_user_activity_date'),
        Index('idx_daily_activity_user_date', 'user_id', 'activity_date'),
        Index('idx_daily_activity_date', 'activity_date'),
    )


class ContentEffectiveness(Base):
    """Track content effectiveness metrics"""
    __tablename__ = "content_effectiveness"
    
    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("contents.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Metrics
    view_count = Column(Integer, default=0, nullable=False)
    completion_count = Column(Integer, default=0, nullable=False)
    average_score = Column(Float)
    average_time_seconds = Column(Integer)
    retry_rate = Column(Float)
    
    # Relationships
    content = relationship("Content")
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('content_id', 'date', name='uq_content_effectiveness_date'),
        Index('idx_content_effectiveness_date', 'date'),
    )