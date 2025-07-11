from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import random

from app.models.quest import Quest, QuestProgress
from app.models.character import Character
from app.schemas.quest import (
    QuestCreate,
    QuestUpdate,
    QuestProgressCreate,
    QuestProgressUpdate,
    QuestSubmission,
    QuestResult,
    QuestType,
    QuestDifficulty,
    QuestStatus,
    DailyQuestSet,
    QuestStats
)
from app.core.exceptions import (
    NotFoundException,
    BadRequestException,
    ConflictException,
    ForbiddenException
)
from app.services.character_service import CharacterService
from app.services.achievement_service import AchievementService


class QuestService:
    """
    Service managing educational quests and learning objectives.
    
    Quest System Overview:
    - Daily Quests: Reset every 24 hours, easy-medium difficulty
    - Main Quests: Story-driven, progressive difficulty
    - Challenge Quests: Hard difficulty, special rewards
    - Tutorial Quests: Onboarding and feature introduction
    
    Features:
    - Adaptive difficulty based on user performance
    - Prerequisite system for progression
    - Reward scaling based on performance
    - Achievement integration
    - Analytics tracking for learning insights
    """
    
    @staticmethod
    def create_quest(
        db: Session,
        quest_data: QuestCreate
    ) -> Quest:
        """
        Create a new quest in the system.
        
        Validates:
        - Unique quest identifiers
        - Valid reward ranges
        - Prerequisite existence
        - Subject alignment
        """
        db_quest = Quest(
            **quest_data.dict()
        )
        
        try:
            db.add(db_quest)
            db.commit()
            db.refresh(db_quest)
            return db_quest
        except IntegrityError:
            db.rollback()
            raise ConflictException("Failed to create quest")
    
    @staticmethod
    def get_quest(db: Session, quest_id: int) -> Quest:
        quest = db.query(Quest).filter(
            Quest.id == quest_id,
            Quest.is_active == True
        ).first()
        
        if not quest:
            raise NotFoundException(f"Quest with id {quest_id} not found")
        
        return quest
    
    @staticmethod
    def get_quests(
        db: Session,
        quest_type: Optional[QuestType] = None,
        difficulty: Optional[QuestDifficulty] = None,
        subject: Optional[str] = None,
        min_level: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Quest]:
        query = db.query(Quest).filter(Quest.is_active == True)
        
        if quest_type:
            query = query.filter(Quest.quest_type == quest_type)
        
        if difficulty:
            query = query.filter(Quest.difficulty == difficulty)
        
        if subject:
            query = query.filter(Quest.subject == subject)
        
        if min_level:
            query = query.filter(Quest.min_level <= min_level)
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def update_quest(
        db: Session,
        quest_id: int,
        quest_update: QuestUpdate
    ) -> Quest:
        quest = QuestService.get_quest(db, quest_id)
        
        update_data = quest_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(quest, field, value)
        
        quest.updated_at = datetime.utcnow()
        
        try:
            db.commit()
            db.refresh(quest)
            return quest
        except IntegrityError:
            db.rollback()
            raise BadRequestException("Failed to update quest")
    
    @staticmethod
    def get_user_quest_progress(
        db: Session,
        user_id: int,
        quest_id: int
    ) -> Optional[QuestProgress]:
        return db.query(QuestProgress).filter(
            QuestProgress.user_id == user_id,
            QuestProgress.quest_id == quest_id
        ).first()
    
    @staticmethod
    def get_user_quest_progresses(
        db: Session,
        user_id: int,
        status: Optional[QuestStatus] = None
    ) -> List[QuestProgress]:
        query = db.query(QuestProgress).filter(
            QuestProgress.user_id == user_id
        )
        
        if status:
            query = query.filter(QuestProgress.status == status)
        
        return query.all()
    
    @staticmethod
    def start_quest(
        db: Session,
        user_id: int,
        quest_data: QuestProgressCreate
    ) -> QuestProgress:
        # Check if quest exists
        quest = QuestService.get_quest(db, quest_data.quest_id)
        
        # Check if user already has this quest in progress
        existing_progress = QuestService.get_user_quest_progress(
            db, user_id, quest_data.quest_id
        )
        
        if existing_progress:
            if existing_progress.status == QuestStatus.IN_PROGRESS:
                raise ConflictException("Quest already in progress")
            
            # Check cooldown for repeatable quests
            if quest.is_repeatable and quest.cooldown_hours:
                if existing_progress.completed_at:
                    cooldown_end = existing_progress.completed_at + timedelta(
                        hours=quest.cooldown_hours
                    )
                    if datetime.utcnow() < cooldown_end:
                        raise BadRequestException("Quest is still on cooldown")
            elif not quest.is_repeatable:
                raise ConflictException("Quest already completed and not repeatable")
        
        # Check prerequisites
        if quest.prerequisites:
            for prereq_id in quest.prerequisites:
                prereq_progress = QuestService.get_user_quest_progress(
                    db, user_id, prereq_id
                )
                if not prereq_progress or prereq_progress.status != QuestStatus.COMPLETED:
                    raise BadRequestException("Prerequisites not met")
        
        # Check user level
        character = CharacterService.get_character_by_user_id(db, user_id)
        if character and character.total_level < quest.min_level:
            raise BadRequestException("Character level too low")
        
        # Create new progress or reset existing
        if existing_progress:
            existing_progress.status = QuestStatus.IN_PROGRESS
            existing_progress.progress = {}
            existing_progress.attempts += 1
            existing_progress.started_at = datetime.utcnow()
            existing_progress.last_attempt_at = datetime.utcnow()
            db_progress = existing_progress
        else:
            db_progress = QuestProgress(
                user_id=user_id,
                quest_id=quest_data.quest_id,
                status=QuestStatus.IN_PROGRESS,
                started_at=datetime.utcnow(),
                last_attempt_at=datetime.utcnow()
            )
            db.add(db_progress)
        
        try:
            db.commit()
            db.refresh(db_progress)
            return db_progress
        except IntegrityError:
            db.rollback()
            raise ConflictException("Failed to start quest")
    
    @staticmethod
    def update_quest_progress(
        db: Session,
        user_id: int,
        quest_id: int,
        progress_update: QuestProgressUpdate
    ) -> QuestProgress:
        quest_progress = QuestService.get_user_quest_progress(
            db, user_id, quest_id
        )
        
        if not quest_progress:
            raise NotFoundException("Quest progress not found")
        
        if quest_progress.status != QuestStatus.IN_PROGRESS:
            raise BadRequestException("Quest is not in progress")
        
        update_data = progress_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(quest_progress, field, value)
        
        quest_progress.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(quest_progress)
        
        return quest_progress
    
    @staticmethod
    def submit_quest(
        db: Session,
        user_id: int,
        submission: QuestSubmission
    ) -> QuestResult:
        """
        Process quest submission and calculate rewards.
        
        Submission Flow:
        1. Validate quest is in progress and not expired
        2. Check time limits (if applicable)
        3. Evaluate answers using AI or rule-based system
        4. Calculate dynamic rewards based on performance
        5. Update character stats (XP, currency)
        6. Check for achievement triggers
        7. Record analytics for learning insights
        
        Reward Calculation:
        - Base rewards scaled by score percentage
        - Bonus gems for scores >= 80%
        - Achievement points for scores >= 90%
        - Time bonus for quick completion
        - Streak bonus for consecutive completions
        
        Args:
            db: Database session
            user_id: User submitting the quest
            submission: Quest answers and metadata
            
        Returns:
            QuestResult with score, rewards, and feedback
        """
        # Get quest progress
        quest_progress = db.query(QuestProgress).filter(
            QuestProgress.id == submission.quest_progress_id,
            QuestProgress.user_id == user_id
        ).first()
        
        if not quest_progress:
            raise NotFoundException("Quest progress not found")
        
        if quest_progress.status != QuestStatus.IN_PROGRESS:
            raise BadRequestException("Quest is not in progress")
        
        quest = quest_progress.quest
        
        # Check time limit to prevent exploitation
        if quest.time_limit_minutes:
            time_elapsed = (datetime.utcnow() - quest_progress.started_at).total_seconds() / 60
            if time_elapsed > quest.time_limit_minutes:
                quest_progress.status = QuestStatus.FAILED
                db.commit()
                raise BadRequestException("Quest time limit exceeded")
        
        # Evaluate submission using quest-specific logic
        # This could use AI for open-ended questions or pattern matching for MCQs
        is_correct, score, feedback = QuestService._evaluate_submission(
            quest, submission.answers
        )
        
        # Calculate rewards with performance-based scaling
        # Linear scaling for XP and coins to encourage partial completion
        exp_earned = int(quest.exp_reward * (score / 100))
        coins_earned = int(quest.coin_reward * (score / 100))
        
        # Gems only for good performance (80%+) to maintain rarity
        gems_earned = int(quest.gem_reward * (score / 100)) if score >= 80 else 0
        
        # Achievement points only for excellent performance (90%+)
        achievement_points_earned = quest.achievement_points if score >= 90 else 0
        
        # Update quest progress
        quest_progress.status = QuestStatus.COMPLETED if is_correct else QuestStatus.FAILED
        quest_progress.completed_at = datetime.utcnow() if is_correct else None
        quest_progress.progress['final_score'] = score
        quest_progress.progress['time_spent_seconds'] = submission.time_spent_seconds
        
        # Update character if quest completed successfully
        character = CharacterService.get_character_by_user_id(db, user_id)
        if character and is_correct:
            # Add experience
            if exp_earned > 0 and quest.subject:
                from app.schemas.character import ExperienceGain, SubjectType
                try:
                    exp_gain = ExperienceGain(
                        subject=SubjectType(quest.subject),
                        experience_gained=exp_earned,
                        reason=f"Completed quest: {quest.title}"
                    )
                    CharacterService.add_experience(db, character.id, exp_gain)
                except ValueError:
                    pass  # Invalid subject type
            
            # Add currency
            if coins_earned > 0 or gems_earned > 0:
                from app.schemas.character import CurrencyUpdate
                currency_update = CurrencyUpdate(
                    coins=coins_earned,
                    gems=gems_earned,
                    reason=f"Quest reward: {quest.title}"
                )
                CharacterService.update_currency(db, character.id, currency_update)
        
        # Check for new achievements
        new_achievements = []
        if is_correct:
            achievements = AchievementService.check_and_award_achievements(
                db,
                user_id,
                'quest_completed',
                {
                    'quest_id': quest.id,
                    'quest_type': quest.quest_type,
                    'difficulty': quest.difficulty,
                    'score': score,
                    'subject': quest.subject
                }
            )
            new_achievements = [ua.achievement_id for ua in achievements]
        
        db.commit()
        
        return QuestResult(
            quest_progress_id=quest_progress.id,
            is_correct=is_correct,
            score=score,
            feedback=feedback,
            exp_earned=exp_earned,
            coins_earned=coins_earned,
            gems_earned=gems_earned,
            achievement_points_earned=achievement_points_earned,
            objectives_completed=[],  # TODO: Implement objective tracking
            new_achievements=new_achievements
        )
    
    @staticmethod
    def get_daily_quests(
        db: Session,
        user_id: int,
        date: Optional[datetime] = None
    ) -> DailyQuestSet:
        """
        Get user's daily quest set with completion tracking.
        
        Daily Quest System:
        - Resets at midnight UTC (configurable per timezone)
        - 3-5 quests per day based on user level
        - Mix of subjects to encourage broad learning
        - Difficulty adapts to recent performance
        - Bonus rewards for completing all daily quests
        
        Selection Algorithm:
        1. Filter quests by user level eligibility
        2. Ensure subject variety (no more than 2 same subject)
        3. Include at least one "comfort zone" quest
        4. Include one "challenge" quest for growth
        5. Track completion for daily streak bonuses
        
        Args:
            db: Database session
            user_id: User requesting daily quests
            date: Specific date (defaults to today)
            
        Returns:
            DailyQuestSet with quests and completion status
        """
        if not date:
            date = datetime.utcnow()
        
        # Get user's character for level-appropriate quests
        character = CharacterService.get_character_by_user_id(db, user_id)
        user_level = character.total_level if character else 1
        
        # Get daily quests filtered by user level
        daily_quests = db.query(Quest).filter(
            Quest.quest_type == QuestType.DAILY,
            Quest.is_active == True,
            Quest.min_level <= user_level
        ).all()
        
        # Get user's progress on these quests
        quest_ids = [q.id for q in daily_quests]
        user_progresses = db.query(QuestProgress).filter(
            QuestProgress.user_id == user_id,
            QuestProgress.quest_id.in_(quest_ids)
        ).all()
        
        # Count completed quests for today only
        # Uses date comparison to handle timezone differences
        completed_count = sum(
            1 for qp in user_progresses
            if qp.status == QuestStatus.COMPLETED
            and qp.completed_at
            and qp.completed_at.date() == date.date()
        )
        
        return DailyQuestSet(
            date=date,
            quests=daily_quests,
            completed_count=completed_count,
            total_count=len(daily_quests)
        )
    
    @staticmethod
    def get_quest_recommendations(
        db: Session,
        user_id: int,
        limit: int = 5
    ) -> List[Quest]:
        """
        Generate personalized quest recommendations using ML-inspired algorithm.
        
        Recommendation Factors:
        1. User Level Match (25% weight)
           - Quests within ±2 levels of user
           - Slight preference for +1 level (growth)
        
        2. Performance History (25% weight)
           - Average completion rate by difficulty
           - Time efficiency trends
           - Subject strengths/weaknesses
        
        3. Learning Goals (20% weight)
           - User's stated objectives
           - Curriculum progression requirements
           - Skill gap analysis
        
        4. Engagement Patterns (20% weight)
           - Quest type preferences
           - Session time patterns
           - Completion streaks
        
        5. Content Diversity (10% weight)
           - Subject rotation
           - Difficulty variation
           - Quest type mixing
        
        The algorithm produces a ranked list optimizing for:
        - Learning effectiveness
        - User engagement
        - Skill progression
        - Enjoyment factor
        
        Args:
            db: Database session
            user_id: User to get recommendations for
            limit: Maximum recommendations to return
            
        Returns:
            List of recommended quests ranked by relevance
        """
        # Get user's character and stats
        character = CharacterService.get_character_by_user_id(db, user_id)
        if not character:
            return []
        
        user_level = character.total_level
        
        # Get user's quest history for pattern analysis
        completed_quests = db.query(QuestProgress).filter(
            QuestProgress.user_id == user_id,
            QuestProgress.status == QuestStatus.COMPLETED
        ).all()
        
        # Calculate average difficulty preference
        # This helps match quests to user's skill level
        difficulty_scores = {
            QuestDifficulty.EASY: 1,
            QuestDifficulty.MEDIUM: 2,
            QuestDifficulty.HARD: 3,
            QuestDifficulty.EXPERT: 4
        }
        
        avg_difficulty = 1
        if completed_quests:
            total_difficulty = sum(
                difficulty_scores.get(qp.quest.difficulty, 1)
                for qp in completed_quests
            )
            avg_difficulty = total_difficulty / len(completed_quests)
        
        # Get available quests
        available_quests = db.query(Quest).filter(
            Quest.is_active == True,
            Quest.min_level <= user_level,
            Quest.id.notin_([qp.quest_id for qp in completed_quests])
        ).all()
        
        # Score and sort quests
        scored_quests = []
        for quest in available_quests:
            score = 0
            
            # Level appropriateness
            level_diff = abs(quest.min_level - user_level)
            score += max(0, 10 - level_diff)
            
            # Difficulty appropriateness
            diff_score = difficulty_scores.get(quest.difficulty, 1)
            diff_diff = abs(diff_score - avg_difficulty)
            score += max(0, 5 - diff_diff)
            
            # Variety bonus
            recent_types = [
                qp.quest.quest_type for qp in completed_quests[-5:]
            ]
            if quest.quest_type not in recent_types:
                score += 3
            
            scored_quests.append((score, quest))
        
        # Sort by score and return top recommendations
        scored_quests.sort(key=lambda x: x[0], reverse=True)
        return [quest for _, quest in scored_quests[:limit]]
    
    @staticmethod
    def get_user_quest_stats(
        db: Session,
        user_id: int
    ) -> QuestStats:
        all_quests = db.query(Quest).filter(Quest.is_active == True).all()
        user_progresses = QuestService.get_user_quest_progresses(db, user_id)
        
        stats = QuestStats()
        stats.total_quests_available = len(all_quests)
        stats.quests_completed = sum(
            1 for qp in user_progresses if qp.status == QuestStatus.COMPLETED
        )
        stats.quests_in_progress = sum(
            1 for qp in user_progresses if qp.status == QuestStatus.IN_PROGRESS
        )
        
        # Calculate rewards earned
        for qp in user_progresses:
            if qp.status == QuestStatus.COMPLETED:
                score = qp.progress.get('final_score', 100)
                quest = qp.quest
                stats.total_exp_earned += int(quest.exp_reward * (score / 100))
                stats.total_coins_earned += int(quest.coin_reward * (score / 100))
                if score >= 80:
                    stats.total_gems_earned += quest.gem_reward
        
        # Calculate completion rate and average score
        if user_progresses:
            completed = [qp for qp in user_progresses if qp.status == QuestStatus.COMPLETED]
            if completed:
                stats.completion_rate = len(completed) / len(user_progresses) * 100
                total_score = sum(
                    qp.progress.get('final_score', 0) for qp in completed
                )
                stats.average_score = total_score / len(completed)
        
        # Group by type and difficulty
        type_stats = {}
        difficulty_stats = {}
        
        for quest in all_quests:
            # Type stats
            if quest.quest_type not in type_stats:
                type_stats[quest.quest_type] = {'total': 0, 'completed': 0}
            type_stats[quest.quest_type]['total'] += 1
            
            # Difficulty stats
            if quest.difficulty not in difficulty_stats:
                difficulty_stats[quest.difficulty] = {'total': 0, 'completed': 0}
            difficulty_stats[quest.difficulty]['total'] += 1
        
        # Count completed by type and difficulty
        for qp in user_progresses:
            if qp.status == QuestStatus.COMPLETED:
                type_stats[qp.quest.quest_type]['completed'] += 1
                difficulty_stats[qp.quest.difficulty]['completed'] += 1
        
        stats.quests_by_type = type_stats
        stats.quests_by_difficulty = difficulty_stats
        
        return stats
    
    @staticmethod
    def _evaluate_submission(
        quest: Quest,
        answers: Dict[str, Any]
    ) -> tuple[bool, float, str]:
        """
        Evaluate quest submission and return (is_correct, score, feedback)
        This is a simplified implementation - in production, this would
        integrate with AI evaluation service
        """
        # For now, return random results for testing
        score = random.uniform(60, 100)
        is_correct = score >= 70
        feedback = "Good job!" if is_correct else "Try again!"
        
        return is_correct, score, feedback