from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class UserRole(str, enum.Enum):
    """User role enumeration"""
    PARENT = "parent"
    CHILD = "child"
    ADMIN = "admin"


class User(Base):
    """User model for authentication and basic information"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.CHILD, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Parent-child relationship
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    character = relationship("Character", back_populates="user", uselist=False, cascade="all, delete-orphan")
    children = relationship("User", backref="parent", remote_side=[id])
    quest_progress = relationship("QuestProgress", back_populates="user", cascade="all, delete-orphan")
    achievements = relationship("UserAchievement", back_populates="user", cascade="all, delete-orphan")
    family_memberships = relationship("FamilyMember", back_populates="user", cascade="all, delete-orphan")
    learning_sessions = relationship("LearningSession", back_populates="user", cascade="all, delete-orphan")
    learning_profile = relationship("LearningProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    personalized_contents = relationship("PersonalizedContent", back_populates="user", cascade="all, delete-orphan")
    subscription = relationship("Subscription", back_populates="user", uselist=False, cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")
    
    # Multiplayer relationships
    owned_guild = relationship("Guild", back_populates="owner", uselist=False, foreign_keys="Guild.owner_id")
    guild = relationship("Guild", secondary="guild_members", back_populates="members", viewonly=True)
    friendships = relationship("Friendship", 
                             primaryjoin="or_(User.id==Friendship.user1_id, User.id==Friendship.user2_id)",
                             viewonly=True)
    
    # Additional stats for multiplayer
    pvp_rating = Column(Integer, default=1200)  # ELO rating
    pvp_wins = Column(Integer, default=0)
    pvp_losses = Column(Integer, default=0)
    total_study_hours = Column(Integer, default=0)
    
    # Two-factor authentication
    two_factor_secret = Column(String, nullable=True)
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_backup_codes = Column(String, nullable=True)  # Encrypted JSON
    
    def __repr__(self):
        return f"<User {self.username}>"


class UserProfile(Base):
    """Extended user profile information"""
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Personal information
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    grade = Column(Integer, nullable=True)  # 학년
    
    # Learning preferences
    preferred_subjects = Column(String, nullable=True)  # JSON string of subject list
    learning_style = Column(String, nullable=True)  # visual, auditory, kinesthetic
    study_time_preference = Column(String, nullable=True)  # morning, afternoon, evening
    
    # Avatar/Profile
    avatar_url = Column(String, nullable=True)
    bio = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="profile")
    
    def __repr__(self):
        return f"<UserProfile for user_id={self.user_id}>"