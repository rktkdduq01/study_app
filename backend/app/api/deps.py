from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_token, decode_access_token
from app.core.permissions import Permission, PermissionChecker, has_permission
from app.models.user import User, UserRole
from app.core.exceptions import (
    TokenError, TokenExpiredError, TokenBlacklistedError, 
    InvalidTokenTypeError, AuthenticationError
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    Get current authenticated user from JWT token.
    
    Args:
        db: Database session
        token: JWT access token
    
    Returns:
        Current user object
    
    Raises:
        TokenError: If token is invalid
        TokenExpiredError: If token has expired
        TokenBlacklistedError: If token is blacklisted
        AuthenticationError: If user not found
    """
    try:
        # Decode token and get user ID
        user_id = decode_access_token(token)
        
        # Get user from database
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user is None:
            raise AuthenticationError(detail=f"User not found: {user_id}")
        
        return user
        
    except TokenExpiredError:
        # Re-raise with proper headers for expired tokens
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except TokenBlacklistedError:
        # Re-raise with proper headers for blacklisted tokens
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (TokenError, InvalidTokenTypeError):
        # Re-raise with proper headers for invalid tokens
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except AuthenticationError:
        # Re-raise for user not found
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user.
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        Current active user
    
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def get_current_parent_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current user who is a parent.
    
    Args:
        current_user: Current active user
    
    Returns:
        Current parent user
    
    Raises:
        HTTPException: If user is not a parent
    """
    if current_user.role != UserRole.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Parent role required."
        )
    return current_user


def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current user who is an admin.
    
    Args:
        current_user: Current active user
    
    Returns:
        Current admin user
    
    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin role required."
        )
    return current_user


def get_user_or_child(
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> User:
    """
    Get a user by ID. Parents can access their children's data.
    
    Args:
        user_id: ID of user to get (optional)
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Requested user or current user
    
    Raises:
        HTTPException: If user not found or no permission
    """
    # If no user_id provided, return current user
    if user_id is None:
        return current_user
    
    # Admin can access any user
    if current_user.role == UserRole.ADMIN:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    
    # User accessing their own data
    if current_user.id == user_id:
        return current_user
    
    # Parent accessing their child's data
    if current_user.role == UserRole.PARENT:
        child = db.query(User).filter(
            User.id == user_id,
            User.parent_id == current_user.id
        ).first()
        if child:
            return child
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not enough permissions to access this user"
    )


def get_current_teacher_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current user who is a teacher.
    
    Args:
        current_user: Current active user
    
    Returns:
        Current teacher user
    
    Raises:
        HTTPException: If user is not a teacher
    """
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Teacher role required."
        )
    return current_user


# Permission dependencies
RequireAdmin = Depends(get_current_admin_user)
RequireTeacher = Depends(get_current_teacher_user)
RequireParent = Depends(get_current_parent_user)

# Create permission checkers for common permission sets
RequireUserRead = Depends(PermissionChecker([Permission.USER_READ]))
RequireUserWrite = Depends(PermissionChecker([Permission.USER_UPDATE]))
RequireContentManage = Depends(PermissionChecker([Permission.CONTENT_CREATE, Permission.CONTENT_UPDATE]))
RequireQuestManage = Depends(PermissionChecker([Permission.QUEST_CREATE, Permission.QUEST_UPDATE]))
RequireAnalyticsAccess = Depends(PermissionChecker([Permission.ANALYTICS_READ]))