from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_active_user, get_current_admin_user
from app.models.user import User
from app.services.achievement_service import AchievementService
from app.schemas.achievement import (
    AchievementCreate,
    AchievementUpdate,
    AchievementResponse,
    UserAchievementResponse,
    UserAchievementProgressUpdate,
    AchievementStats,
    AchievementCategory,
    AchievementRarity,
    AchievementLeaderboardEntry
)
from app.core.exceptions import NotFoundException, BadRequestException, ConflictException

router = APIRouter()


@router.get("/", response_model=List[AchievementResponse])
async def get_achievements(
    category: Optional[AchievementCategory] = Query(None, description="Filter by category"),
    rarity: Optional[AchievementRarity] = Query(None, description="Filter by rarity"),
    skip: int = Query(0, ge=0, description="Number of achievements to skip"),
    limit: int = Query(100, ge=1, le=100, description="Number of achievements to return"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all available achievements with optional filters"""
    achievements = AchievementService.get_achievements(
        db=db,
        category=category,
        rarity=rarity,
        skip=skip,
        limit=limit
    )
    return achievements


@router.get("/user", response_model=List[UserAchievementResponse])
async def get_user_achievements(
    completed_only: bool = Query(False, description="Show only completed achievements"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's achievements"""
    user_achievements = AchievementService.get_user_achievements(
        db=db,
        user_id=current_user.id,
        completed_only=completed_only
    )
    return user_achievements


@router.get("/user/stats", response_model=AchievementStats)
async def get_user_achievement_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's achievement statistics"""
    stats = AchievementService.get_user_achievement_stats(
        db=db,
        user_id=current_user.id
    )
    return stats


@router.get("/leaderboard", response_model=List[AchievementLeaderboardEntry])
async def get_achievement_leaderboard(
    skip: int = Query(0, ge=0, description="Number of entries to skip"),
    limit: int = Query(100, ge=1, le=100, description="Number of entries to return"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get achievement leaderboard"""
    leaderboard_data = AchievementService.get_achievement_leaderboard(
        db=db,
        skip=skip,
        limit=limit
    )
    
    # Convert to response model
    leaderboard = []
    for entry in leaderboard_data:
        leaderboard.append(AchievementLeaderboardEntry(**entry))
    
    return leaderboard


@router.get("/{achievement_id}", response_model=AchievementResponse)
async def get_achievement(
    achievement_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific achievement by ID"""
    try:
        achievement = AchievementService.get_achievement(db, achievement_id)
        return achievement
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/{achievement_id}/progress", response_model=UserAchievementResponse)
async def update_achievement_progress(
    achievement_id: int,
    progress_update: UserAchievementProgressUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user's progress on an achievement"""
    try:
        user_achievement = AchievementService.update_user_achievement_progress(
            db=db,
            user_id=current_user.id,
            achievement_id=achievement_id,
            progress_update=progress_update
        )
        return user_achievement
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except BadRequestException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Admin endpoints
@router.post("/admin", response_model=AchievementResponse)
async def create_achievement(
    achievement_data: AchievementCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Create a new achievement (Admin only)"""
    try:
        achievement = AchievementService.create_achievement(db, achievement_data)
        return achievement
    except ConflictException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.put("/admin/{achievement_id}", response_model=AchievementResponse)
async def update_achievement(
    achievement_id: int,
    achievement_update: AchievementUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update an achievement (Admin only)"""
    try:
        achievement = AchievementService.update_achievement(
            db, achievement_id, achievement_update
        )
        return achievement
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except BadRequestException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )