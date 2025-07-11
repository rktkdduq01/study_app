from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, verify_password, get_password_hash
from app.models.user import User, UserRole, UserProfile
from app.models.character import Character, SubjectLevel
from app.schemas.user import UserCreate, UserResponse, Token, UserLogin
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user.
    
    For child accounts:
    - If parent_email is provided, link to parent account
    - Create default character and subject levels
    
    For parent accounts:
    - Simply create the user account
    """
    # Check if email already exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Find parent if parent_email is provided
    parent_id = None
    if user_data.parent_email and user_data.role == UserRole.CHILD:
        parent = db.query(User).filter(
            User.email == user_data.parent_email,
            User.role == UserRole.PARENT
        ).first()
        if parent:
            parent_id = parent.id
    
    # Create new user
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password),
        role=user_data.role,
        parent_id=parent_id
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create user profile
    profile = UserProfile(user_id=new_user.id)
    db.add(profile)
    
    # For child accounts, create character and subject levels
    if new_user.role == UserRole.CHILD:
        # Create character
        character = Character(
            user_id=new_user.id,
            name=new_user.username,
            avatar_type="warrior"
        )
        db.add(character)
        db.commit()
        db.refresh(character)
        
        # Create subject levels
        for subject in settings.SUBJECTS:
            subject_level = SubjectLevel(
                character_id=character.id,
                subject=subject
            )
            db.add(subject_level)
    
    db.commit()
    
    # Prepare response
    response = UserResponse(
        id=new_user.id,
        email=new_user.email,
        username=new_user.username,
        role=new_user.role,
        is_active=new_user.is_active,
        is_verified=new_user.is_verified,
        parent_id=new_user.parent_id,
        created_at=new_user.created_at,
        updated_at=new_user.updated_at,
        has_character=new_user.role == UserRole.CHILD,
        children_count=0
    )
    
    return response


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login.
    
    Returns access token for authentication.
    """
    # Find user by username
    user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id,
        expires_delta=access_token_expires
    )
    
    # Count children if parent
    children_count = 0
    if user.role == UserRole.PARENT:
        children_count = db.query(User).filter(User.parent_id == user.id).count()
    
    # Prepare user response
    user_response = UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        role=user.role,
        is_active=user.is_active,
        is_verified=user.is_verified,
        parent_id=user.parent_id,
        created_at=user.created_at,
        updated_at=user.updated_at,
        has_character=user.character is not None,
        children_count=children_count
    )
    
    return Token(
        access_token=access_token,
        user=user_response
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user information.
    """
    # Count children if parent
    children_count = 0
    if current_user.role == UserRole.PARENT:
        children_count = db.query(User).filter(User.parent_id == current_user.id).count()
    
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        role=current_user.role,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        parent_id=current_user.parent_id,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        has_character=current_user.character is not None,
        children_count=children_count
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Refresh access token.
    """
    # Create new access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=current_user.id,
        expires_delta=access_token_expires
    )
    
    # Count children if parent
    children_count = 0
    if current_user.role == UserRole.PARENT:
        children_count = db.query(User).filter(User.parent_id == current_user.id).count()
    
    # Prepare user response
    user_response = UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        role=current_user.role,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        parent_id=current_user.parent_id,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        has_character=current_user.character is not None,
        children_count=children_count
    )
    
    return Token(
        access_token=access_token,
        user=user_response
    )