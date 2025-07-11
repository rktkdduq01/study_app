from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.models.multiplayer import SessionType, SessionStatus
from app.services.multiplayer_service import MultiplayerService
from app.services.guild_service import GuildService
from app.services.friend_service import FriendService
from app.services.chat_service import ChatService
from app.services.websocket_service import manager as ws_manager
from app.schemas.multiplayer import (
    SessionCreate, SessionResponse, SessionJoin,
    GuildCreate, GuildResponse, GuildMemberResponse,
    FriendRequestCreate, FriendRequestResponse,
    ChatMessageCreate, ChatMessageResponse
)
from app.utils.logger import api_logger

router = APIRouter()
multiplayer_service = MultiplayerService()
guild_service = GuildService()
friend_service = FriendService()
chat_service = ChatService()

# WebSocket endpoint
@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: int,
    db: Session = Depends(deps.get_db)
):
    """WebSocket connection endpoint"""
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        await websocket.close(code=4001, reason="User not found")
        return
    
    await ws_manager.connect(websocket, user_id)
    
    try:
        while True:
            data = await websocket.receive_json()
            await ws_manager.handle_message(websocket, user_id, data)
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        api_logger.error("WebSocket error", error=e, user_id=user.id if user else None)
        ws_manager.disconnect(websocket)

# Multiplayer Sessions

@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    session_data: SessionCreate,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Create a new multiplayer session"""
    session = await multiplayer_service.create_session(
        db=db,
        user=current_user,
        session_type=SessionType(session_data.type),
        name=session_data.name,
        description=session_data.description,
        max_players=session_data.max_players,
        is_public=session_data.is_public,
        quest_id=session_data.quest_id,
        subject_id=session_data.subject_id,
        difficulty=session_data.difficulty
    )
    
    return SessionResponse(
        id=session.id,
        code=session.session_code,
        type=session.type.value,
        name=session.name,
        status=session.status.value,
        participants=1,
        max_players=session.max_players,
        creator_id=session.creator_id,
        created_at=session.created_at
    )

@router.post("/sessions/join", response_model=dict)
async def join_session(
    join_data: SessionJoin,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Join a multiplayer session"""
    result = await multiplayer_service.join_session(
        db=db,
        user=current_user,
        session_code=join_data.session_code
    )
    return result

@router.post("/sessions/{session_id}/start")
async def start_session(
    session_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Start a multiplayer session"""
    result = await multiplayer_service.start_session(
        db=db,
        user=current_user,
        session_id=session_id
    )
    return result

@router.post("/sessions/{session_id}/answer")
async def submit_answer(
    session_id: int,
    answer: str,
    time_taken: float,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Submit answer in PvP battle"""
    result = await multiplayer_service.submit_answer(
        db=db,
        user=current_user,
        session_id=session_id,
        answer=answer,
        time_taken=time_taken
    )
    return result

# Guild endpoints

@router.post("/guilds", response_model=GuildResponse)
async def create_guild(
    guild_data: GuildCreate,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Create a new guild"""
    guild = await guild_service.create_guild(
        db=db,
        user=current_user,
        name=guild_data.name,
        description=guild_data.description,
        tag=guild_data.tag,
        is_public=guild_data.is_public
    )
    
    return GuildResponse(
        id=guild.id,
        name=guild.name,
        tag=guild.tag,
        level=guild.level.value,
        member_count=guild.get_member_count(),
        max_members=guild.max_members,
        owner_id=guild.owner_id,
        created_at=guild.created_at
    )

@router.post("/guilds/{guild_id}/join")
async def join_guild(
    guild_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Join a guild"""
    result = await guild_service.join_guild(
        db=db,
        user=current_user,
        guild_id=guild_id
    )
    return result

@router.post("/guilds/{guild_id}/leave")
async def leave_guild(
    guild_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Leave a guild"""
    result = await guild_service.leave_guild(
        db=db,
        user=current_user,
        guild_id=guild_id
    )
    return result

@router.get("/guilds/leaderboard", response_model=List[dict])
def get_guild_leaderboard(
    limit: int = Query(default=10, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(deps.get_db)
):
    """Get guild leaderboard"""
    return guild_service.get_guild_leaderboard(
        db=db,
        limit=limit,
        offset=offset
    )

# Friend endpoints

@router.post("/friends/request")
async def send_friend_request(
    request_data: FriendRequestCreate,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Send a friend request"""
    request = await friend_service.send_friend_request(
        db=db,
        sender=current_user,
        receiver_id=request_data.receiver_id,
        message=request_data.message
    )
    
    return FriendRequestResponse(
        id=request.id,
        sender_id=request.sender_id,
        receiver_id=request.receiver_id,
        status=request.status,
        created_at=request.created_at
    )

@router.post("/friends/request/{request_id}/accept")
async def accept_friend_request(
    request_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Accept a friend request"""
    friendship = await friend_service.accept_friend_request(
        db=db,
        user=current_user,
        request_id=request_id
    )
    
    return {
        "message": "Friend request accepted",
        "friendship_id": friendship.id
    }

@router.post("/friends/request/{request_id}/decline")
async def decline_friend_request(
    request_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Decline a friend request"""
    result = await friend_service.decline_friend_request(
        db=db,
        user=current_user,
        request_id=request_id
    )
    return result

@router.delete("/friends/{friend_id}")
async def remove_friend(
    friend_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Remove a friend"""
    result = await friend_service.remove_friend(
        db=db,
        user=current_user,
        friend_id=friend_id
    )
    return result

@router.get("/friends", response_model=List[dict])
def get_friends_list(
    online_only: bool = Query(default=False),
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Get friends list"""
    return friend_service.get_friends_list(
        db=db,
        user=current_user,
        limit=limit,
        offset=offset,
        online_only=online_only
    )

@router.get("/friends/requests", response_model=List[dict])
def get_friend_requests(
    request_type: str = Query(default="received", regex="^(received|sent)$"),
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Get pending friend requests"""
    return friend_service.get_pending_requests(
        db=db,
        user=current_user,
        request_type=request_type
    )

# Chat endpoints

@router.post("/chat/direct/{user_id}")
async def create_direct_chat(
    user_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Create or get direct message chat"""
    room = await chat_service.create_direct_message_room(
        db=db,
        user1=current_user,
        user2_id=user_id
    )
    
    return {
        "room_id": room.id,
        "type": room.type
    }

@router.post("/chat/{room_id}/messages")
async def send_chat_message(
    room_id: int,
    message_data: ChatMessageCreate,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Send a chat message"""
    message = await chat_service.send_message(
        db=db,
        user=current_user,
        room_id=room_id,
        content=message_data.content,
        message_type=message_data.message_type,
        reply_to_id=message_data.reply_to_id,
        attachments=message_data.attachments
    )
    
    return ChatMessageResponse(
        id=message.id,
        room_id=message.room_id,
        sender_id=message.sender_id,
        content=message.content,
        message_type=message.message_type,
        created_at=message.created_at
    )

@router.get("/chat/{room_id}/messages", response_model=List[dict])
async def get_chat_history(
    room_id: int,
    limit: int = Query(default=50, le=100),
    before_id: Optional[int] = None,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Get chat history"""
    messages = await chat_service.get_chat_history(
        db=db,
        user=current_user,
        room_id=room_id,
        limit=limit,
        before_id=before_id
    )
    return messages

@router.put("/chat/messages/{message_id}")
async def edit_message(
    message_id: int,
    new_content: str,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Edit a chat message"""
    message = await chat_service.edit_message(
        db=db,
        user=current_user,
        message_id=message_id,
        new_content=new_content
    )
    
    return {
        "message": "Message edited successfully",
        "edited_at": message.edited_at
    }

@router.delete("/chat/messages/{message_id}")
async def delete_message(
    message_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Delete a chat message"""
    result = await chat_service.delete_message(
        db=db,
        user=current_user,
        message_id=message_id
    )
    return result

@router.post("/chat/messages/{message_id}/reactions/{emoji}")
async def add_reaction(
    message_id: int,
    emoji: str,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Add reaction to message"""
    message = await chat_service.add_reaction(
        db=db,
        user=current_user,
        message_id=message_id,
        emoji=emoji
    )
    
    return {
        "message": "Reaction added",
        "reactions": message.reactions
    }

@router.delete("/chat/messages/{message_id}/reactions/{emoji}")
async def remove_reaction(
    message_id: int,
    emoji: str,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Remove reaction from message"""
    message = await chat_service.remove_reaction(
        db=db,
        user=current_user,
        message_id=message_id,
        emoji=emoji
    )
    
    return {
        "message": "Reaction removed",
        "reactions": message.reactions
    }