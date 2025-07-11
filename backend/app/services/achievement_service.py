from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from datetime import datetime

from app.models.achievement import Achievement, UserAchievement
from app.models.user import User
from app.schemas.achievement import (
    AchievementCreate,
    AchievementUpdate,
    UserAchievementCreate,
    UserAchievementProgressUpdate,
    AchievementCategory,
    AchievementRarity,
    AchievementStats
)
from app.core.exceptions import (
    NotFoundException,
    BadRequestException,
    ConflictException
)


class AchievementService:
    @staticmethod
    def create_achievement(
        db: Session,
        achievement_data: AchievementCreate
    ) -> Achievement:
        db_achievement = Achievement(
            **achievement_data.dict()
        )
        
        try:
            db.add(db_achievement)
            db.commit()
            db.refresh(db_achievement)
            return db_achievement
        except IntegrityError:
            db.rollback()
            raise ConflictException("Failed to create achievement")
    
    @staticmethod
    def get_achievement(db: Session, achievement_id: int) -> Achievement:
        achievement = db.query(Achievement).filter(
            Achievement.id == achievement_id,
            Achievement.is_active == True
        ).first()
        
        if not achievement:
            raise NotFoundException(f"Achievement with id {achievement_id} not found")
        
        return achievement
    
    @staticmethod
    def get_achievements(
        db: Session,
        category: Optional[AchievementCategory] = None,
        rarity: Optional[AchievementRarity] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Achievement]:
        query = db.query(Achievement).filter(Achievement.is_active == True)
        
        if category:
            query = query.filter(Achievement.category == category)
        
        if rarity:
            query = query.filter(Achievement.rarity == rarity)
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def update_achievement(
        db: Session,
        achievement_id: int,
        achievement_update: AchievementUpdate
    ) -> Achievement:
        achievement = AchievementService.get_achievement(db, achievement_id)
        
        update_data = achievement_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(achievement, field, value)
        
        achievement.updated_at = datetime.utcnow()
        
        try:
            db.commit()
            db.refresh(achievement)
            return achievement
        except IntegrityError:
            db.rollback()
            raise BadRequestException("Failed to update achievement")
    
    @staticmethod
    def get_user_achievement(
        db: Session,
        user_id: int,
        achievement_id: int
    ) -> Optional[UserAchievement]:
        return db.query(UserAchievement).filter(
            UserAchievement.user_id == user_id,
            UserAchievement.achievement_id == achievement_id
        ).first()
    
    @staticmethod
    def get_user_achievements(
        db: Session,
        user_id: int,
        completed_only: bool = False
    ) -> List[UserAchievement]:
        query = db.query(UserAchievement).filter(
            UserAchievement.user_id == user_id
        )
        
        if completed_only:
            query = query.filter(UserAchievement.is_completed == True)
        
        return query.all()
    
    @staticmethod
    def create_user_achievement(
        db: Session,
        user_id: int,
        achievement_data: UserAchievementCreate
    ) -> UserAchievement:
        # Check if achievement exists
        achievement = AchievementService.get_achievement(
            db, achievement_data.achievement_id
        )
        
        # Check if user already has this achievement
        existing = AchievementService.get_user_achievement(
            db, user_id, achievement_data.achievement_id
        )
        
        if existing:
            raise ConflictException("User already has this achievement")
        
        db_user_achievement = UserAchievement(
            user_id=user_id,
            achievement_id=achievement_data.achievement_id
        )
        
        try:
            db.add(db_user_achievement)
            db.commit()
            db.refresh(db_user_achievement)
            return db_user_achievement
        except IntegrityError:
            db.rollback()
            raise ConflictException("Failed to create user achievement")
    
    @staticmethod
    def update_user_achievement_progress(
        db: Session,
        user_id: int,
        achievement_id: int,
        progress_update: UserAchievementProgressUpdate
    ) -> UserAchievement:
        user_achievement = AchievementService.get_user_achievement(
            db, user_id, achievement_id
        )
        
        if not user_achievement:
            # Create new user achievement if doesn't exist
            user_achievement = AchievementService.create_user_achievement(
                db,
                user_id,
                UserAchievementCreate(achievement_id=achievement_id)
            )
        
        # Update progress
        user_achievement.current_progress = progress_update.progress
        
        # Check if completed
        achievement = user_achievement.achievement
        if user_achievement.current_progress >= achievement.max_progress:
            user_achievement.is_completed = True
            user_achievement.earned_at = datetime.utcnow()
        
        user_achievement.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(user_achievement)
        
        return user_achievement
    
    @staticmethod
    def check_and_award_achievements(
        db: Session,
        user_id: int,
        trigger_type: str,
        trigger_data: Dict[str, Any]
    ) -> List[UserAchievement]:
        """
        Check if user has earned any achievements based on trigger
        """
        awarded_achievements = []
        
        # Get all achievements that match trigger type
        achievements = db.query(Achievement).filter(
            Achievement.is_active == True,
            Achievement.requirements.op('->>')('trigger_type') == trigger_type
        ).all()
        
        for achievement in achievements:
            # Check if user already has this achievement
            user_achievement = AchievementService.get_user_achievement(
                db, user_id, achievement.id
            )
            
            if user_achievement and user_achievement.is_completed:
                continue
            
            # Check requirements
            if AchievementService._check_requirements(
                achievement.requirements,
                trigger_data
            ):
                # Award achievement
                if not user_achievement:
                    user_achievement = AchievementService.create_user_achievement(
                        db,
                        user_id,
                        UserAchievementCreate(achievement_id=achievement.id)
                    )
                
                user_achievement.is_completed = True
                user_achievement.earned_at = datetime.utcnow()
                user_achievement.current_progress = achievement.max_progress
                
                awarded_achievements.append(user_achievement)
        
        db.commit()
        
        return awarded_achievements
    
    @staticmethod
    def get_user_achievement_stats(
        db: Session,
        user_id: int
    ) -> AchievementStats:
        user_achievements = AchievementService.get_user_achievements(db, user_id)
        all_achievements = db.query(Achievement).filter(
            Achievement.is_active == True
        ).all()
        
        stats = AchievementStats(
            total_achievements=len(all_achievements),
            completed_achievements=sum(1 for ua in user_achievements if ua.is_completed),
            total_points=0,
            earned_points=0,
            completion_percentage=0.0,
            achievements_by_category={},
            achievements_by_rarity={}
        )
        
        # Calculate points
        for achievement in all_achievements:
            stats.total_points += achievement.points
            
        for ua in user_achievements:
            if ua.is_completed:
                stats.earned_points += ua.achievement.points
        
        # Calculate completion percentage
        if stats.total_achievements > 0:
            stats.completion_percentage = (
                stats.completed_achievements / stats.total_achievements * 100
            )
        
        # Group by category and rarity
        category_stats = {}
        rarity_stats = {}
        
        for achievement in all_achievements:
            # Category stats
            if achievement.category not in category_stats:
                category_stats[achievement.category] = {
                    'total': 0,
                    'completed': 0
                }
            category_stats[achievement.category]['total'] += 1
            
            # Rarity stats
            if achievement.rarity not in rarity_stats:
                rarity_stats[achievement.rarity] = {
                    'total': 0,
                    'completed': 0
                }
            rarity_stats[achievement.rarity]['total'] += 1
        
        # Count completed by category and rarity
        for ua in user_achievements:
            if ua.is_completed:
                category_stats[ua.achievement.category]['completed'] += 1
                rarity_stats[ua.achievement.rarity]['completed'] += 1
        
        stats.achievements_by_category = category_stats
        stats.achievements_by_rarity = rarity_stats
        
        return stats
    
    @staticmethod
    def get_achievement_leaderboard(
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get achievement leaderboard sorted by total achievement points
        """
        # Query users with their achievement stats
        leaderboard_query = db.query(
            User.id,
            User.username,
            User.avatar_url,
            func.count(UserAchievement.id).filter(
                UserAchievement.is_completed == True
            ).label('completed_achievements'),
            func.sum(Achievement.points).filter(
                UserAchievement.is_completed == True
            ).label('total_points')
        ).join(
            UserAchievement, User.id == UserAchievement.user_id
        ).join(
            Achievement, UserAchievement.achievement_id == Achievement.id
        ).group_by(
            User.id, User.username, User.avatar_url
        ).order_by(
            func.sum(Achievement.points).desc()
        ).offset(skip).limit(limit)
        
        leaderboard = []
        rank = skip + 1
        
        for row in leaderboard_query:
            leaderboard.append({
                'rank': rank,
                'user_id': row.id,
                'username': row.username,
                'avatar_url': row.avatar_url,
                'total_points': row.total_points or 0,
                'completed_achievements': row.completed_achievements or 0
            })
            rank += 1
        
        return leaderboard
    
    @staticmethod
    def _check_requirements(
        requirements: Dict[str, Any],
        trigger_data: Dict[str, Any]
    ) -> bool:
        """
        Check if trigger data meets achievement requirements
        """
        if not requirements:
            return True
        
        for key, required_value in requirements.items():
            if key == 'trigger_type':
                continue
                
            if key not in trigger_data:
                return False
            
            # Handle different comparison types
            if isinstance(required_value, dict):
                if 'min' in required_value:
                    if trigger_data[key] < required_value['min']:
                        return False
                if 'max' in required_value:
                    if trigger_data[key] > required_value['max']:
                        return False
                if 'equals' in required_value:
                    if trigger_data[key] != required_value['equals']:
                        return False
            else:
                if trigger_data[key] != required_value:
                    return False
        
        return True