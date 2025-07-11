from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from datetime import datetime

class FriendRequest(Base):
    __tablename__ = "friend_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    receiver_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    status = Column(String(20), default='pending')  # pending, accepted, declined, blocked
    message = Column(String(500))  # Optional message with friend request
    
    created_at = Column(DateTime, default=datetime.utcnow)
    responded_at = Column(DateTime)
    
    # Relationships
    sender = relationship("User", foreign_keys=[sender_id], backref="sent_friend_requests")
    receiver = relationship("User", foreign_keys=[receiver_id], backref="received_friend_requests")
    
    # Ensure unique friend requests
    __table_args__ = (
        UniqueConstraint('sender_id', 'receiver_id', name='_sender_receiver_uc'),
    )

class Friendship(Base):
    __tablename__ = "friendships"
    
    id = Column(Integer, primary_key=True, index=True)
    user1_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user2_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Friendship stats
    friendship_level = Column(Integer, default=1)  # Increases with interactions
    interaction_count = Column(Integer, default=0)
    last_interaction = Column(DateTime)
    
    # Features
    favorite = Column(Boolean, default=False)  # Mark as favorite/best friend
    notifications_enabled = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user1 = relationship("User", foreign_keys=[user1_id])
    user2 = relationship("User", foreign_keys=[user2_id])
    
    # Ensure unique friendships (lower ID always user1)
    __table_args__ = (
        UniqueConstraint('user1_id', 'user2_id', name='_user1_user2_uc'),
    )
    
    @staticmethod
    def create_friendship(user1_id: int, user2_id: int):
        """Create friendship with consistent ordering"""
        if user1_id > user2_id:
            user1_id, user2_id = user2_id, user1_id
        return Friendship(user1_id=user1_id, user2_id=user2_id)
    
    def get_other_user_id(self, user_id: int) -> int:
        """Get the other user in the friendship"""
        return self.user2_id if user_id == self.user1_id else self.user1_id
    
    def increase_interaction(self):
        """Increase interaction count and potentially level"""
        self.interaction_count += 1
        self.last_interaction = datetime.utcnow()
        
        # Level up friendship every 10 interactions
        if self.interaction_count % 10 == 0:
            self.friendship_level += 1

class UserBlock(Base):
    __tablename__ = "user_blocks"
    
    id = Column(Integer, primary_key=True, index=True)
    blocker_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    blocked_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    reason = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    blocker = relationship("User", foreign_keys=[blocker_id], backref="blocked_users")
    blocked = relationship("User", foreign_keys=[blocked_id], backref="blocked_by")
    
    # Ensure unique blocks
    __table_args__ = (
        UniqueConstraint('blocker_id', 'blocked_id', name='_blocker_blocked_uc'),
    )