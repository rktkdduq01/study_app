from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime
import json

from app.models.chat import ChatRoom, ChatMessage, ChatParticipant, DirectMessage
from app.models.user import User
from app.models.friend import Friendship, UserBlock
from app.core.exceptions import BadRequestException, NotFoundException, ForbiddenException
from app.services.websocket_service import manager as ws_manager
from app.services.security_audit import SecurityAudit

class ChatService:
    def __init__(self):
        self.security_audit = SecurityAudit()
    
    async def create_direct_message_room(
        self,
        db: Session,
        user1: User,
        user2_id: int
    ) -> ChatRoom:
        """Create or get direct message room between two users"""
        # Check if users are blocked
        blocked = db.query(UserBlock).filter(
            or_(
                and_(UserBlock.blocker_id == user1.id, UserBlock.blocked_id == user2_id),
                and_(UserBlock.blocker_id == user2_id, UserBlock.blocked_id == user1.id)
            )
        ).first()
        
        if blocked:
            raise ForbiddenException("Cannot create chat with blocked user")
        
        # Check for existing DM
        user1_id, user2_id = sorted([user1.id, user2_id])
        existing_dm = db.query(DirectMessage).filter(
            and_(
                DirectMessage.user1_id == user1_id,
                DirectMessage.user2_id == user2_id
            )
        ).first()
        
        if existing_dm:
            return existing_dm.room
        
        # Create new chat room
        room = ChatRoom(
            name=f"DM-{user1_id}-{user2_id}",
            type="direct",
            max_members=2
        )
        db.add(room)
        db.flush()
        
        # Add participants
        room.add_participant(user1_id)
        room.add_participant(user2_id)
        
        # Create DM record
        dm = DirectMessage.create_direct_message(user1_id, user2_id, room.id)
        db.add(dm)
        
        db.commit()
        return room
    
    async def send_message(
        self,
        db: Session,
        user: User,
        room_id: int,
        content: str,
        message_type: str = "text",
        reply_to_id: Optional[int] = None,
        attachments: Optional[List[Dict]] = None
    ) -> ChatMessage:
        """Send a message to a chat room"""
        # Security check
        if not self.security_audit.is_content_safe(content):
            raise BadRequestException("Message contains inappropriate content")
        
        # Get room and check access
        room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
        if not room or not room.is_active:
            raise NotFoundException("Chat room not found")
        
        # Check if user is participant
        participant = db.query(ChatParticipant).filter(
            and_(
                ChatParticipant.room_id == room_id,
                ChatParticipant.user_id == user.id,
                ChatParticipant.left_at.is_(None)
            )
        ).first()
        
        if not participant:
            raise ForbiddenException("You are not a participant in this chat")
        
        # Check if muted
        if participant.is_muted and (
            not participant.muted_until or participant.muted_until > datetime.utcnow()
        ):
            raise ForbiddenException("You are muted in this chat")
        
        # Create message
        message = ChatMessage(
            room_id=room_id,
            sender_id=user.id,
            content=content,
            message_type=message_type,
            reply_to_id=reply_to_id,
            attachments=attachments or []
        )
        
        db.add(message)
        db.flush()
        
        # Update participant unread counts
        other_participants = db.query(ChatParticipant).filter(
            and_(
                ChatParticipant.room_id == room_id,
                ChatParticipant.user_id != user.id,
                ChatParticipant.left_at.is_(None)
            )
        ).all()
        
        for p in other_participants:
            p.unread_count += 1
        
        db.commit()
        
        # Send real-time notification
        message_data = {
            "id": message.id,
            "room_id": room_id,
            "sender_id": user.id,
            "sender_username": user.username,
            "content": content,
            "message_type": message_type,
            "reply_to_id": reply_to_id,
            "attachments": attachments,
            "created_at": message.created_at.isoformat()
        }
        
        # Send to all online participants
        for p in other_participants:
            if p.notifications_enabled:
                await ws_manager.send_chat_message(
                    user_id=p.user_id,
                    message=message_data
                )
        
        return message
    
    async def edit_message(
        self,
        db: Session,
        user: User,
        message_id: int,
        new_content: str
    ) -> ChatMessage:
        """Edit a message"""
        message = db.query(ChatMessage).filter(
            and_(
                ChatMessage.id == message_id,
                ChatMessage.deleted == False
            )
        ).first()
        
        if not message:
            raise NotFoundException("Message not found")
        
        if message.sender_id != user.id:
            raise ForbiddenException("You can only edit your own messages")
        
        # Security check
        if not self.security_audit.is_content_safe(new_content):
            raise BadRequestException("Message contains inappropriate content")
        
        message.content = new_content
        message.edited = True
        message.edited_at = datetime.utcnow()
        
        db.commit()
        
        # Notify participants
        participants = db.query(ChatParticipant).filter(
            and_(
                ChatParticipant.room_id == message.room_id,
                ChatParticipant.left_at.is_(None)
            )
        ).all()
        
        for p in participants:
            await ws_manager.send_chat_update(
                user_id=p.user_id,
                update={
                    "type": "message_edited",
                    "message_id": message_id,
                    "new_content": new_content,
                    "edited_at": message.edited_at.isoformat()
                }
            )
        
        return message
    
    async def delete_message(
        self,
        db: Session,
        user: User,
        message_id: int
    ) -> Dict[str, Any]:
        """Delete a message"""
        message = db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
        
        if not message:
            raise NotFoundException("Message not found")
        
        # Check permissions
        participant = db.query(ChatParticipant).filter(
            and_(
                ChatParticipant.room_id == message.room_id,
                ChatParticipant.user_id == user.id
            )
        ).first()
        
        if not participant:
            raise ForbiddenException("You are not in this chat")
        
        # Only sender or moderator/admin can delete
        if message.sender_id != user.id and participant.role not in ['moderator', 'admin']:
            raise ForbiddenException("You can only delete your own messages")
        
        message.deleted = True
        message.deleted_at = datetime.utcnow()
        
        db.commit()
        
        # Notify participants
        participants = db.query(ChatParticipant).filter(
            and_(
                ChatParticipant.room_id == message.room_id,
                ChatParticipant.left_at.is_(None)
            )
        ).all()
        
        for p in participants:
            await ws_manager.send_chat_update(
                user_id=p.user_id,
                update={
                    "type": "message_deleted",
                    "message_id": message_id,
                    "deleted_by": user.id
                }
            )
        
        return {"message": "Message deleted successfully"}
    
    async def add_reaction(
        self,
        db: Session,
        user: User,
        message_id: int,
        emoji: str
    ) -> ChatMessage:
        """Add reaction to message"""
        message = db.query(ChatMessage).filter(
            and_(
                ChatMessage.id == message_id,
                ChatMessage.deleted == False
            )
        ).first()
        
        if not message:
            raise NotFoundException("Message not found")
        
        # Check if user is in chat
        participant = db.query(ChatParticipant).filter(
            and_(
                ChatParticipant.room_id == message.room_id,
                ChatParticipant.user_id == user.id,
                ChatParticipant.left_at.is_(None)
            )
        ).first()
        
        if not participant:
            raise ForbiddenException("You are not in this chat")
        
        # Add reaction
        reactions = message.reactions or {}
        if emoji not in reactions:
            reactions[emoji] = []
        
        if user.id not in reactions[emoji]:
            reactions[emoji].append(user.id)
            message.reactions = reactions
            db.commit()
            
            # Notify participants
            await self._notify_reaction_change(
                db, message.room_id, message_id, emoji, user.id, "added"
            )
        
        return message
    
    async def remove_reaction(
        self,
        db: Session,
        user: User,
        message_id: int,
        emoji: str
    ) -> ChatMessage:
        """Remove reaction from message"""
        message = db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
        
        if not message:
            raise NotFoundException("Message not found")
        
        reactions = message.reactions or {}
        if emoji in reactions and user.id in reactions[emoji]:
            reactions[emoji].remove(user.id)
            if not reactions[emoji]:
                del reactions[emoji]
            
            message.reactions = reactions
            db.commit()
            
            # Notify participants
            await self._notify_reaction_change(
                db, message.room_id, message_id, emoji, user.id, "removed"
            )
        
        return message
    
    async def mark_as_read(
        self,
        db: Session,
        user: User,
        room_id: int,
        message_id: int
    ) -> Dict[str, Any]:
        """Mark messages as read up to message_id"""
        participant = db.query(ChatParticipant).filter(
            and_(
                ChatParticipant.room_id == room_id,
                ChatParticipant.user_id == user.id
            )
        ).first()
        
        if not participant:
            raise NotFoundException("You are not in this chat")
        
        participant.last_read_message_id = message_id
        participant.unread_count = 0
        
        db.commit()
        
        return {"last_read_message_id": message_id}
    
    async def get_chat_history(
        self,
        db: Session,
        user: User,
        room_id: int,
        limit: int = 50,
        before_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get chat history"""
        # Check access
        participant = db.query(ChatParticipant).filter(
            and_(
                ChatParticipant.room_id == room_id,
                ChatParticipant.user_id == user.id
            )
        ).first()
        
        if not participant:
            raise ForbiddenException("You are not in this chat")
        
        query = db.query(ChatMessage).filter(
            and_(
                ChatMessage.room_id == room_id,
                ChatMessage.created_at >= participant.joined_at
            )
        )
        
        if before_id:
            query = query.filter(ChatMessage.id < before_id)
        
        messages = query.order_by(ChatMessage.created_at.desc()).limit(limit).all()
        
        return [{
            "id": msg.id,
            "sender_id": msg.sender_id,
            "sender_username": msg.sender.username,
            "content": msg.content if not msg.deleted else "[Deleted]",
            "message_type": msg.message_type,
            "edited": msg.edited,
            "deleted": msg.deleted,
            "reply_to_id": msg.reply_to_id,
            "reactions": msg.reactions,
            "attachments": msg.attachments,
            "created_at": msg.created_at.isoformat()
        } for msg in reversed(messages)]
    
    async def _notify_reaction_change(
        self,
        db: Session,
        room_id: int,
        message_id: int,
        emoji: str,
        user_id: int,
        action: str
    ):
        """Notify participants of reaction change"""
        participants = db.query(ChatParticipant).filter(
            and_(
                ChatParticipant.room_id == room_id,
                ChatParticipant.left_at.is_(None)
            )
        ).all()
        
        for p in participants:
            await ws_manager.send_chat_update(
                user_id=p.user_id,
                update={
                    "type": "reaction_update",
                    "message_id": message_id,
                    "emoji": emoji,
                    "user_id": user_id,
                    "action": action
                }
            )