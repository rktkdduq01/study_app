from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Boolean, JSON, Index
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from datetime import datetime

class ChatRoom(Base):
    __tablename__ = "chat_rooms"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    type = Column(String(20), nullable=False)  # direct, guild, party, global
    
    # Room settings
    is_active = Column(Boolean, default=True)
    max_members = Column(Integer)
    is_moderated = Column(Boolean, default=False)
    
    # For guild/party chats
    guild_id = Column(Integer, ForeignKey('guilds.id'), nullable=True)
    party_id = Column(Integer, ForeignKey('multiplayer_sessions.id'), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    messages = relationship("ChatMessage", back_populates="room", cascade="all, delete-orphan")
    participants = relationship("ChatParticipant", back_populates="room", cascade="all, delete-orphan")
    
    def add_participant(self, user_id: int, role: str = "member"):
        """Add a participant to the chat room"""
        participant = ChatParticipant(
            room_id=self.id,
            user_id=user_id,
            role=role
        )
        self.participants.append(participant)
        return participant

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey('chat_rooms.id'), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Message content
    content = Column(Text, nullable=False)
    message_type = Column(String(20), default='text')  # text, image, system, achievement
    
    # Metadata
    edited = Column(Boolean, default=False)
    edited_at = Column(DateTime)
    deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    
    # For replies
    reply_to_id = Column(Integer, ForeignKey('chat_messages.id'), nullable=True)
    
    # Attachments
    attachments = Column(JSON, default=[])  # List of attachment URLs/data
    
    # Reactions
    reactions = Column(JSON, default={})  # {emoji: [user_ids]}
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    room = relationship("ChatRoom", back_populates="messages")
    sender = relationship("User")
    reply_to = relationship("ChatMessage", remote_side=[id])
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_room_created', 'room_id', 'created_at'),
    )

class ChatParticipant(Base):
    __tablename__ = "chat_participants"
    
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey('chat_rooms.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Participant settings
    role = Column(String(20), default='member')  # member, moderator, admin
    nickname = Column(String(50))  # Custom nickname in this chat
    
    # Status
    last_read_message_id = Column(Integer, ForeignKey('chat_messages.id'))
    unread_count = Column(Integer, default=0)
    is_muted = Column(Boolean, default=False)
    muted_until = Column(DateTime)
    
    # Notifications
    notifications_enabled = Column(Boolean, default=True)
    mention_notifications = Column(Boolean, default=True)
    
    joined_at = Column(DateTime, default=datetime.utcnow)
    left_at = Column(DateTime)
    
    # Relationships
    room = relationship("ChatRoom", back_populates="participants")
    user = relationship("User")
    last_read_message = relationship("ChatMessage", foreign_keys=[last_read_message_id])

class DirectMessage(Base):
    """Simplified table for quick direct message lookups"""
    __tablename__ = "direct_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    user1_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user2_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    room_id = Column(Integer, ForeignKey('chat_rooms.id'), nullable=False, unique=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user1 = relationship("User", foreign_keys=[user1_id])
    user2 = relationship("User", foreign_keys=[user2_id])
    room = relationship("ChatRoom")
    
    @staticmethod
    def create_direct_message(user1_id: int, user2_id: int, room_id: int):
        """Create direct message with consistent ordering"""
        if user1_id > user2_id:
            user1_id, user2_id = user2_id, user1_id
        return DirectMessage(
            user1_id=user1_id,
            user2_id=user2_id,
            room_id=room_id
        )