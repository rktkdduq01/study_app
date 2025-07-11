from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime

from app.models.friend import FriendRequest, Friendship, UserBlock
from app.models.user import User
from app.core.exceptions import BadRequestException, NotFoundException, ForbiddenException
from app.services.websocket_service import manager as ws_manager

class FriendService:
    @staticmethod
    async def send_friend_request(
        db: Session,
        sender: User,
        receiver_id: int,
        message: Optional[str] = None
    ) -> FriendRequest:
        """Send a friend request"""
        # Check if receiver exists
        receiver = db.query(User).filter(User.id == receiver_id).first()
        if not receiver:
            raise NotFoundException("User not found")
        
        # Check if already friends
        existing_friendship = db.query(Friendship).filter(
            or_(
                and_(Friendship.user1_id == min(sender.id, receiver_id),
                     Friendship.user2_id == max(sender.id, receiver_id))
            )
        ).first()
        
        if existing_friendship:
            raise BadRequestException("Already friends with this user")
        
        # Check if blocked
        blocked = db.query(UserBlock).filter(
            or_(
                and_(UserBlock.blocker_id == sender.id, UserBlock.blocked_id == receiver_id),
                and_(UserBlock.blocker_id == receiver_id, UserBlock.blocked_id == sender.id)
            )
        ).first()
        
        if blocked:
            raise ForbiddenException("Cannot send friend request to this user")
        
        # Check for existing pending request
        existing_request = db.query(FriendRequest).filter(
            and_(
                FriendRequest.sender_id == sender.id,
                FriendRequest.receiver_id == receiver_id,
                FriendRequest.status == 'pending'
            )
        ).first()
        
        if existing_request:
            raise BadRequestException("Friend request already sent")
        
        # Check for reverse request
        reverse_request = db.query(FriendRequest).filter(
            and_(
                FriendRequest.sender_id == receiver_id,
                FriendRequest.receiver_id == sender.id,
                FriendRequest.status == 'pending'
            )
        ).first()
        
        if reverse_request:
            # Auto-accept if reverse request exists
            return await FriendService.accept_friend_request(db, sender, reverse_request.id)
        
        # Create friend request
        friend_request = FriendRequest(
            sender_id=sender.id,
            receiver_id=receiver_id,
            message=message
        )
        
        db.add(friend_request)
        db.commit()
        
        # Send notification
        await ws_manager.send_notification(
            user_id=receiver_id,
            notification={
                "type": "friend_request",
                "request_id": friend_request.id,
                "sender_id": sender.id,
                "sender_username": sender.username,
                "message": message or f"{sender.username} wants to be your friend!"
            }
        )
        
        return friend_request
    
    @staticmethod
    async def accept_friend_request(
        db: Session,
        user: User,
        request_id: int
    ) -> Friendship:
        """Accept a friend request"""
        friend_request = db.query(FriendRequest).filter(
            FriendRequest.id == request_id
        ).first()
        
        if not friend_request:
            raise NotFoundException("Friend request not found")
        
        if friend_request.receiver_id != user.id:
            raise ForbiddenException("This request is not for you")
        
        if friend_request.status != 'pending':
            raise BadRequestException("Request already processed")
        
        # Update request status
        friend_request.status = 'accepted'
        friend_request.responded_at = datetime.utcnow()
        
        # Create friendship
        friendship = Friendship.create_friendship(
            friend_request.sender_id,
            friend_request.receiver_id
        )
        
        db.add(friendship)
        db.commit()
        
        # Send notifications
        await ws_manager.send_notification(
            user_id=friend_request.sender_id,
            notification={
                "type": "friend_request_accepted",
                "user_id": user.id,
                "username": user.username,
                "message": f"{user.username} accepted your friend request!"
            }
        )
        
        await ws_manager.send_notification(
            user_id=user.id,
            notification={
                "type": "new_friend",
                "user_id": friend_request.sender_id,
                "username": friend_request.sender.username,
                "message": f"You are now friends with {friend_request.sender.username}"
            }
        )
        
        return friendship
    
    @staticmethod
    async def decline_friend_request(
        db: Session,
        user: User,
        request_id: int
    ) -> Dict[str, Any]:
        """Decline a friend request"""
        friend_request = db.query(FriendRequest).filter(
            FriendRequest.id == request_id
        ).first()
        
        if not friend_request:
            raise NotFoundException("Friend request not found")
        
        if friend_request.receiver_id != user.id:
            raise ForbiddenException("This request is not for you")
        
        if friend_request.status != 'pending':
            raise BadRequestException("Request already processed")
        
        # Update request status
        friend_request.status = 'declined'
        friend_request.responded_at = datetime.utcnow()
        
        db.commit()
        
        return {"message": "Friend request declined"}
    
    @staticmethod
    async def remove_friend(
        db: Session,
        user: User,
        friend_id: int
    ) -> Dict[str, Any]:
        """Remove a friend"""
        # Find friendship
        user1_id, user2_id = sorted([user.id, friend_id])
        friendship = db.query(Friendship).filter(
            and_(
                Friendship.user1_id == user1_id,
                Friendship.user2_id == user2_id
            )
        ).first()
        
        if not friendship:
            raise NotFoundException("Friendship not found")
        
        # Delete friendship
        db.delete(friendship)
        db.commit()
        
        # Send notification
        await ws_manager.send_notification(
            user_id=friend_id,
            notification={
                "type": "friend_removed",
                "user_id": user.id,
                "username": user.username,
                "message": f"{user.username} removed you from their friends list"
            }
        )
        
        return {"message": "Friend removed successfully"}
    
    @staticmethod
    async def block_user(
        db: Session,
        blocker: User,
        blocked_id: int,
        reason: Optional[str] = None
    ) -> UserBlock:
        """Block a user"""
        if blocker.id == blocked_id:
            raise BadRequestException("Cannot block yourself")
        
        # Check if already blocked
        existing_block = db.query(UserBlock).filter(
            and_(
                UserBlock.blocker_id == blocker.id,
                UserBlock.blocked_id == blocked_id
            )
        ).first()
        
        if existing_block:
            raise BadRequestException("User already blocked")
        
        # Remove friendship if exists
        user1_id, user2_id = sorted([blocker.id, blocked_id])
        friendship = db.query(Friendship).filter(
            and_(
                Friendship.user1_id == user1_id,
                Friendship.user2_id == user2_id
            )
        ).first()
        
        if friendship:
            db.delete(friendship)
        
        # Cancel pending friend requests
        db.query(FriendRequest).filter(
            and_(
                or_(
                    and_(FriendRequest.sender_id == blocker.id,
                         FriendRequest.receiver_id == blocked_id),
                    and_(FriendRequest.sender_id == blocked_id,
                         FriendRequest.receiver_id == blocker.id)
                ),
                FriendRequest.status == 'pending'
            )
        ).update({"status": "blocked"})
        
        # Create block
        block = UserBlock(
            blocker_id=blocker.id,
            blocked_id=blocked_id,
            reason=reason
        )
        
        db.add(block)
        db.commit()
        
        return block
    
    @staticmethod
    async def unblock_user(
        db: Session,
        blocker: User,
        blocked_id: int
    ) -> Dict[str, Any]:
        """Unblock a user"""
        block = db.query(UserBlock).filter(
            and_(
                UserBlock.blocker_id == blocker.id,
                UserBlock.blocked_id == blocked_id
            )
        ).first()
        
        if not block:
            raise NotFoundException("Block not found")
        
        db.delete(block)
        db.commit()
        
        return {"message": "User unblocked successfully"}
    
    @staticmethod
    def get_friends_list(
        db: Session,
        user: User,
        limit: int = 50,
        offset: int = 0,
        online_only: bool = False
    ) -> List[Dict[str, Any]]:
        """Get user's friends list"""
        friendships = db.query(Friendship).filter(
            or_(
                Friendship.user1_id == user.id,
                Friendship.user2_id == user.id
            )
        ).limit(limit).offset(offset).all()
        
        friends = []
        for friendship in friendships:
            friend_id = friendship.get_other_user_id(user.id)
            friend = db.query(User).filter(User.id == friend_id).first()
            
            if friend:
                # Check online status (would need to implement online tracking)
                is_online = ws_manager.is_user_online(friend.id)
                
                if online_only and not is_online:
                    continue
                
                friends.append({
                    "id": friend.id,
                    "username": friend.username,
                    "level": friend.character.level if friend.character else 1,
                    "character_class": friend.character.character_class if friend.character else None,
                    "is_online": is_online,
                    "friendship_level": friendship.friendship_level,
                    "favorite": friendship.favorite,
                    "last_interaction": friendship.last_interaction.isoformat() if friendship.last_interaction else None
                })
        
        return friends
    
    @staticmethod
    def get_pending_requests(
        db: Session,
        user: User,
        request_type: str = "received"  # received or sent
    ) -> List[Dict[str, Any]]:
        """Get pending friend requests"""
        if request_type == "received":
            requests = db.query(FriendRequest).filter(
                and_(
                    FriendRequest.receiver_id == user.id,
                    FriendRequest.status == 'pending'
                )
            ).all()
            
            return [{
                "id": req.id,
                "sender_id": req.sender_id,
                "sender_username": req.sender.username,
                "message": req.message,
                "created_at": req.created_at.isoformat()
            } for req in requests]
        else:
            requests = db.query(FriendRequest).filter(
                and_(
                    FriendRequest.sender_id == user.id,
                    FriendRequest.status == 'pending'
                )
            ).all()
            
            return [{
                "id": req.id,
                "receiver_id": req.receiver_id,
                "receiver_username": req.receiver.username,
                "message": req.message,
                "created_at": req.created_at.isoformat()
            } for req in requests]
    
    @staticmethod
    async def update_friendship_interaction(
        db: Session,
        user: User,
        friend_id: int
    ) -> Friendship:
        """Update friendship interaction stats"""
        user1_id, user2_id = sorted([user.id, friend_id])
        friendship = db.query(Friendship).filter(
            and_(
                Friendship.user1_id == user1_id,
                Friendship.user2_id == user2_id
            )
        ).first()
        
        if not friendship:
            raise NotFoundException("Friendship not found")
        
        friendship.increase_interaction()
        db.commit()
        
        # Check for friendship level milestone
        if friendship.friendship_level % 5 == 0:  # Every 5 levels
            # Send notification about friendship milestone
            for uid in [user1_id, user2_id]:
                await ws_manager.send_notification(
                    user_id=uid,
                    notification={
                        "type": "friendship_milestone",
                        "friendship_level": friendship.friendship_level,
                        "message": f"Your friendship has reached level {friendship.friendship_level}!"
                    }
                )
        
        return friendship