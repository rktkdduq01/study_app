from datetime import timedelta
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import models, schemas
from app.api import deps
from app.core import security
from app.core.config import settings

router = APIRouter()


@router.post("/login", response_model=schemas.TokenResponse)
def login(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login with refresh token.
    """
    user = db.query(models.User).filter(
        models.User.email == form_data.username
    ).first()
    
    if not user or not security.verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create token pair with additional claims
    additional_claims = {
        "email": user.email,
        "roles": [user.role] if user.role else []
    }
    
    return security.create_token_pair(
        subject=user.id,
        additional_claims=additional_claims
    )


@router.post("/refresh", response_model=schemas.TokenResponse)
def refresh_token(
    refresh_token: str = Body(..., embed=True),
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Refresh access token using refresh token.
    """
    token_data = security.refresh_access_token(refresh_token)
    
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    return token_data


@router.post("/logout")
def logout(
    current_user: models.User = Depends(deps.get_current_active_user),
    token: str = Depends(deps.oauth2_scheme),
    refresh_token: Optional[str] = Body(None, embed=True)
) -> Any:
    """
    Logout user by revoking tokens.
    """
    # Revoke access token
    security.revoke_token(token, "access")
    
    # Revoke refresh token if provided
    if refresh_token:
        security.revoke_token(refresh_token, "refresh")
    
    return {"message": "Successfully logged out"}


@router.post("/register", response_model=schemas.User)
def register(
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserCreate
) -> Any:
    """
    Register new user with enhanced security.
    """
    # Check if user exists
    user = db.query(models.User).filter(
        models.User.email == user_in.email
    ).first()
    
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Validate password strength
    is_valid, error_msg = security.validate_password_strength(user_in.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Create new user
    user = models.User(
        email=user_in.email,
        username=user_in.username,
        password=security.get_password_hash(user_in.password),
        role=user_in.role if hasattr(user_in, 'role') else "student",
        is_active=True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


@router.post("/change-password")
def change_password(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    current_password: str = Body(...),
    new_password: str = Body(...)
) -> Any:
    """
    Change user password.
    """
    # Verify current password
    if not security.verify_password(current_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )
    
    # Validate new password strength
    is_valid, error_msg = security.validate_password_strength(new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Update password
    current_user.password = security.get_password_hash(new_password)
    db.commit()
    
    return {"message": "Password updated successfully"}


@router.get("/me", response_model=schemas.User)
def read_users_me(
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Get current user.
    """
    return current_user