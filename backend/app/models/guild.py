from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Boolean, Table, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from datetime import datetime
from typing import Optional
import enum

# Association tables
guild_members = Table(
    'guild_members',
    Base.metadata,
    Column('guild_id', Integer, ForeignKey('guilds.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('joined_at', DateTime, default=datetime.utcnow),
    Column('role', String(50), default='member'),  # member, officer, leader
    Column('contribution_points', Integer, default=0)
)

guild_invitations = Table(
    'guild_invitations',
    Base.metadata,
    Column('id', Integer, primary_key=True, index=True),
    Column('guild_id', Integer, ForeignKey('guilds.id')),
    Column('inviter_id', Integer, ForeignKey('users.id')),
    Column('invitee_id', Integer, ForeignKey('users.id')),
    Column('status', String(20), default='pending'),  # pending, accepted, declined, expired
    Column('created_at', DateTime, default=datetime.utcnow),
    Column('expires_at', DateTime)
)

class GuildLevel(enum.Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    DIAMOND = "diamond"

class Guild(Base):
    __tablename__ = "guilds"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text)
    tag = Column(String(10), unique=True, nullable=False)  # Short guild tag
    
    # Guild stats
    level = Column(SQLEnum(GuildLevel), default=GuildLevel.BRONZE)
    experience = Column(Integer, default=0)
    max_members = Column(Integer, default=50)
    
    # Guild settings
    is_public = Column(Boolean, default=True)  # Public guilds can be joined freely
    min_level_requirement = Column(Integer, default=1)
    auto_accept_members = Column(Boolean, default=False)
    
    # Guild features
    emblem = Column(String(255))  # URL to guild emblem
    banner = Column(String(255))  # URL to guild banner
    primary_color = Column(String(7), default="#3498db")  # Hex color
    secondary_color = Column(String(7), default="#2c3e50")
    
    # Guild stats and achievements
    total_quests_completed = Column(Integer, default=0)
    total_pvp_wins = Column(Integer, default=0)
    weekly_activity_points = Column(Integer, default=0)
    guild_bank_coins = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    owner = relationship("User", foreign_keys=[owner_id], back_populates="owned_guild")
    members = relationship("User", secondary=guild_members, back_populates="guild")
    
    # Guild activities
    quests = relationship("GuildQuest", back_populates="guild", cascade="all, delete-orphan")
    announcements = relationship("GuildAnnouncement", back_populates="guild", cascade="all, delete-orphan")
    
    def add_member(self, user, role="member"):
        """Add a member to the guild"""
        if user not in self.members and len(self.members) < self.max_members:
            self.members.append(user)
            return True
        return False
    
    def remove_member(self, user):
        """Remove a member from the guild"""
        if user in self.members and user.id != self.owner_id:
            self.members.remove(user)
            return True
        return False
    
    def get_member_count(self):
        """Get current member count"""
        return len(self.members)
    
    def can_join(self, user):
        """Check if user can join the guild"""
        if len(self.members) >= self.max_members:
            return False, "Guild is full"
        if user.level < self.min_level_requirement:
            return False, f"Minimum level {self.min_level_requirement} required"
        if user in self.members:
            return False, "Already a member"
        return True, "Can join"

class GuildQuest(Base):
    __tablename__ = "guild_quests"
    
    id = Column(Integer, primary_key=True, index=True)
    guild_id = Column(Integer, ForeignKey('guilds.id'), nullable=False)
    quest_id = Column(Integer, ForeignKey('quests.id'), nullable=False)
    
    # Quest progress
    status = Column(String(20), default='active')  # active, completed, failed
    progress = Column(JSON, default={})  # Track progress by member
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    
    # Rewards
    guild_exp_reward = Column(Integer, default=0)
    guild_coin_reward = Column(Integer, default=0)
    
    # Participation
    min_participants = Column(Integer, default=3)
    max_participants = Column(Integer, default=10)
    participants = Column(JSON, default=[])  # List of user IDs
    
    # Relationships
    guild = relationship("Guild", back_populates="quests")
    quest = relationship("Quest")

class GuildAnnouncement(Base):
    __tablename__ = "guild_announcements"
    
    id = Column(Integer, primary_key=True, index=True)
    guild_id = Column(Integer, ForeignKey('guilds.id'), nullable=False)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    priority = Column(String(20), default='normal')  # low, normal, high, urgent
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime)
    
    # Relationships
    guild = relationship("Guild", back_populates="announcements")
    author = relationship("User")