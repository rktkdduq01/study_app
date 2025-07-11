from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User, UserRole, UserProfile
from app.schemas.user import UserResponse, UserUpdate, UserWithProfile
from app.api.deps import (
    get_current_active_user,
    get_current_parent_user,
    get_user_or_child
)

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get list of users.
    
    - Admin: Can see all users
    - Parent: Can see their children
    - Child: Can only see themselves
    """
    if current_user.role == UserRole.ADMIN:
        users = db.query(User).offset(skip).limit(limit).all()
    elif current_user.role == UserRole.PARENT:
        # Get parent and their children
        user_ids = [current_user.id]
        children = db.query(User).filter(User.parent_id == current_user.id).all()
        user_ids.extend([child.id for child in children])
        users = db.query(User).filter(User.id.in_(user_ids)).all()
    else:
        # Child can only see themselves
        users = [current_user]
    
    # Convert to response format
    responses = []
    for user in users:
        children_count = 0
        if user.role == UserRole.PARENT:
            children_count = db.query(User).filter(User.parent_id == user.id).count()
        
        responses.append(UserResponse(
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
        ))
    
    return responses


@router.get("/{user_id}", response_model=UserWithProfile)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    requested_user: User = Depends(get_user_or_child),
    db: Session = Depends(get_db)
):
    """
    Get user by ID with profile information.
    
    Parents can access their children's data.
    """
    # Get profile data
    profile = requested_user.profile
    
    # Count children if parent
    children_count = 0
    if requested_user.role == UserRole.PARENT:
        children_count = db.query(User).filter(User.parent_id == requested_user.id).count()
    
    return UserWithProfile(
        id=requested_user.id,
        email=requested_user.email,
        username=requested_user.username,
        role=requested_user.role,
        is_active=requested_user.is_active,
        is_verified=requested_user.is_verified,
        parent_id=requested_user.parent_id,
        created_at=requested_user.created_at,
        updated_at=requested_user.updated_at,
        has_character=requested_user.character is not None,
        children_count=children_count,
        first_name=profile.first_name if profile else None,
        last_name=profile.last_name if profile else None,
        age=profile.age if profile else None,
        grade=profile.grade if profile else None,
        avatar_url=profile.avatar_url if profile else None
    )


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    requested_user: User = Depends(get_user_or_child),
    db: Session = Depends(get_db)
):
    """
    Update user information.
    
    Users can update their own info.
    Parents can update their children's info.
    """
    # Update fields if provided
    if user_update.email is not None:
        # Check if email already exists
        existing = db.query(User).filter(
            User.email == user_update.email,
            User.id != requested_user.id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        requested_user.email = user_update.email
    
    if user_update.username is not None:
        # Check if username already exists
        existing = db.query(User).filter(
            User.username == user_update.username,
            User.id != requested_user.id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        requested_user.username = user_update.username
    
    if user_update.password is not None:
        from app.core.security import get_password_hash
        requested_user.hashed_password = get_password_hash(user_update.password)
    
    if user_update.is_active is not None and current_user.role == UserRole.ADMIN:
        requested_user.is_active = user_update.is_active
    
    db.commit()
    db.refresh(requested_user)
    
    # Count children if parent
    children_count = 0
    if requested_user.role == UserRole.PARENT:
        children_count = db.query(User).filter(User.parent_id == requested_user.id).count()
    
    return UserResponse(
        id=requested_user.id,
        email=requested_user.email,
        username=requested_user.username,
        role=requested_user.role,
        is_active=requested_user.is_active,
        is_verified=requested_user.is_verified,
        parent_id=requested_user.parent_id,
        created_at=requested_user.created_at,
        updated_at=requested_user.updated_at,
        has_character=requested_user.character is not None,
        children_count=children_count
    )


@router.get("/parent/children", response_model=List[UserResponse])
async def get_parent_children(
    current_parent: User = Depends(get_current_parent_user),
    db: Session = Depends(get_db)
):
    """
    Get all children of the current parent user.
    """
    children = db.query(User).filter(User.parent_id == current_parent.id).all()
    
    responses = []
    for child in children:
        responses.append(UserResponse(
            id=child.id,
            email=child.email,
            username=child.username,
            role=child.role,
            is_active=child.is_active,
            is_verified=child.is_verified,
            parent_id=child.parent_id,
            created_at=child.created_at,
            updated_at=child.updated_at,
            has_character=child.character is not None,
            children_count=0
        ))
    
    return responses


@router.post("/parent/link-child/{child_username}")
async def link_child_to_parent(
    child_username: str,
    current_parent: User = Depends(get_current_parent_user),
    db: Session = Depends(get_db)
):
    """
    Link an existing child account to a parent.
    """
    # Find child by username
    child = db.query(User).filter(
        User.username == child_username,
        User.role == UserRole.CHILD
    ).first()
    
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child user not found"
        )
    
    if child.parent_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Child already linked to a parent"
        )
    
    # Link child to parent
    child.parent_id = current_parent.id
    db.commit()
    
    return {"message": f"Successfully linked {child_username} to your account"}