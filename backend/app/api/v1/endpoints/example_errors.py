"""
Example API endpoints demonstrating user-friendly error handling
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    BusinessLogicError,
    RateLimitError,
    NotFoundError
)
from app.models.user import User
from app.utils.logger import api_logger

router = APIRouter()


@router.post("/purchase-item/{item_id}")
async def purchase_item(
    item_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """
    Example: Purchase an item with user-friendly error handling
    """
    # Check if item exists
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise NotFoundError("Item", item_id)
    
    # Check if user has enough points
    if current_user.points < item.price:
        api_logger.info(
            "Purchase failed - insufficient points",
            user_id=current_user.id,
            item_id=item_id,
            user_points=current_user.points,
            item_price=item.price
        )
        raise BusinessLogicError(
            error_code="BIZ003",
            detail=f"User has {current_user.points} points but needs {item.price}"
        )
    
    # Check if item is already owned
    if db.query(UserItem).filter(
        UserItem.user_id == current_user.id,
        UserItem.item_id == item_id
    ).first():
        raise BusinessLogicError(
            error_code="BIZ004",
            detail="User already owns this item"
        )
    
    # Process purchase...
    return {"success": True, "message": "아이템을 구매했습니다"}


@router.post("/join-quest/{quest_id}")
async def join_quest(
    quest_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """
    Example: Join a quest with validation errors
    """
    quest = db.query(Quest).filter(Quest.id == quest_id).first()
    if not quest:
        raise NotFoundError("Quest", quest_id)
    
    # Multiple validation checks
    errors = []
    
    # Check level requirement
    if current_user.level < quest.min_level:
        errors.append({
            "field": "level",
            "message": f"Level {quest.min_level} required",
            "user_message": f"레벨 {quest.min_level} 이상이 필요합니다"
        })
    
    # Check if quest is full
    participant_count = db.query(QuestParticipant).filter(
        QuestParticipant.quest_id == quest_id
    ).count()
    
    if participant_count >= quest.max_participants:
        errors.append({
            "field": "participants",
            "message": "Quest is full",
            "user_message": "퀘스트 인원이 가득 찼습니다"
        })
    
    # Check prerequisites
    if quest.prerequisite_quest_id:
        completed = db.query(UserQuestCompletion).filter(
            UserQuestCompletion.user_id == current_user.id,
            UserQuestCompletion.quest_id == quest.prerequisite_quest_id
        ).first()
        
        if not completed:
            errors.append({
                "field": "prerequisites",
                "message": "Prerequisite quest not completed",
                "user_message": "선행 퀘스트를 먼저 완료해주세요"
            })
    
    if errors:
        raise ValidationError(
            detail="Quest join validation failed",
            error_code="BIZ002",
            data={"errors": errors, "user_errors": errors}
        )
    
    # Join quest...
    return {"success": True, "message": "퀘스트에 참여했습니다"}


@router.post("/send-message")
async def send_message(
    content: str,
    recipient_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """
    Example: Send message with rate limiting
    """
    # Check rate limit (e.g., 10 messages per minute)
    recent_messages = db.query(Message).filter(
        Message.sender_id == current_user.id,
        Message.created_at > datetime.now() - timedelta(minutes=1)
    ).count()
    
    if recent_messages >= 10:
        raise RateLimitError(
            error_code="RATE001",
            retry_after=60,
            detail="Message rate limit exceeded"
        )
    
    # Send message...
    return {"success": True, "message": "메시지를 전송했습니다"}


@router.get("/premium-content/{content_id}")
async def get_premium_content(
    content_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """
    Example: Access premium content with authorization error
    """
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise NotFoundError("Content", content_id)
    
    # Check if content is premium
    if content.is_premium and not current_user.is_premium:
        raise AuthorizationError(
            error_code="PERM002",
            detail="Premium subscription required",
            required_role="premium"
        )
    
    # Check age restriction
    if content.age_rating > current_user.age:
        raise AuthorizationError(
            error_code="PERM003",
            detail=f"Content requires age {content.age_rating}+"
        )
    
    return {"content": content}


@router.post("/verify-email")
async def verify_email(
    token: str,
    db: Session = Depends(deps.get_db)
):
    """
    Example: Email verification with authentication error
    """
    # Verify token
    try:
        payload = decode_email_verification_token(token)
        email = payload.get("email")
    except:
        raise AuthenticationError(
            error_code="AUTH005",
            detail="Invalid or expired verification token"
        )
    
    # Find user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise NotFoundError("User", f"email={email}")
    
    if user.is_verified:
        return {"success": True, "message": "이미 인증된 계정입니다"}
    
    # Verify user...
    return {"success": True, "message": "이메일 인증이 완료되었습니다"}


@router.post("/register")
async def register(
    email: str,
    password: str,
    username: str,
    age: int,
    db: Session = Depends(deps.get_db)
):
    """
    Example: User registration with various validation errors
    """
    # Check email format
    if not is_valid_email(email):
        raise ValidationError(
            error_code="VAL003",
            detail="Invalid email format",
            field="email"
        )
    
    # Check password strength
    if len(password) < 8 or not any(c.isupper() for c in password):
        raise ValidationError(
            error_code="VAL004",
            detail="Password too weak",
            field="password"
        )
    
    # Check duplicate email
    if db.query(User).filter(User.email == email).first():
        raise BusinessLogicError(
            error_code="BIZ001",
            detail=f"Email {email} already registered"
        )
    
    # Check username
    if len(username) < 3:
        raise ValidationError(
            detail="Username too short",
            field="username",
            error_code="VAL001",
            data={
                "user_errors": [{
                    "field": "username",
                    "message": "사용자명은 3자 이상이어야 합니다"
                }]
            }
        )
    
    # Check age
    if age < 13:
        raise ValidationError(
            detail="User too young",
            field="age",
            error_code="VAL001",
            data={
                "user_errors": [{
                    "field": "age",
                    "message": "13세 이상만 가입할 수 있습니다"
                }]
            }
        )
    
    # Register user...
    return {"success": True, "message": "회원가입이 완료되었습니다"}