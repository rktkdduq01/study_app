"""
Parent Quest Service
Service for creating and managing parent-assigned quests for children
"""

from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.core.logger import get_logger
from app.models.family import (
    Family, FamilyMember, ParentQuest, QuestProgressLog,
    FamilyRole, RelationshipStatus
)
from app.models.user import User
from app.models.gamification import Quest, UserQuest, QuestStatus
from app.schemas.family import ParentQuestCreate, ParentQuestUpdate

logger = get_logger(__name__)

class ParentQuestService:
    """Service for managing parent-created quests"""
    
    def __init__(self, db: Session):
        self.db = db
        
    def create_parent_quest(self, parent_id: int, quest_data: ParentQuestCreate) -> ParentQuest:
        """Create a new parent quest for a child"""
        try:
            # Verify parent-child relationship
            if not self._verify_parent_child_relationship(parent_id, quest_data.assigned_to_id):
                raise ValueError("Invalid parent-child relationship")
                
            # Get family
            family_member = self.db.query(FamilyMember).filter(
                and_(
                    FamilyMember.user_id == parent_id,
                    FamilyMember.status == RelationshipStatus.ACTIVE
                )
            ).first()
            
            if not family_member or not family_member.can_create_quests:
                raise ValueError("Parent does not have permission to create quests")
                
            # Create parent quest
            parent_quest = ParentQuest(
                family_id=family_member.family_id,
                created_by_id=parent_id,
                assigned_to_id=quest_data.assigned_to_id,
                title=quest_data.title,
                description=quest_data.description,
                quest_type=quest_data.quest_type,
                requirements=quest_data.requirements,
                rewards=quest_data.rewards,
                start_date=quest_data.start_date or datetime.utcnow(),
                end_date=quest_data.end_date,
                is_recurring=quest_data.is_recurring,
                recurrence_pattern=quest_data.recurrence_pattern,
                status="active"
            )
            
            self.db.add(parent_quest)
            
            # Create corresponding game quest for the child
            game_quest = self._create_game_quest_from_parent(parent_quest)
            
            self.db.commit()
            
            logger.info(f"Parent {parent_id} created quest {parent_quest.id} for child {quest_data.assigned_to_id}")
            
            return parent_quest
            
        except Exception as e:
            logger.error(f"Failed to create parent quest: {e}")
            self.db.rollback()
            raise
            
    def _verify_parent_child_relationship(self, parent_id: int, child_id: int) -> bool:
        """Verify that parent has permission to create quests for child"""
        # Get parent's families
        parent_families = self.db.query(FamilyMember).filter(
            and_(
                FamilyMember.user_id == parent_id,
                FamilyMember.role.in_([FamilyRole.PARENT, FamilyRole.GUARDIAN]),
                FamilyMember.status == RelationshipStatus.ACTIVE
            )
        ).all()
        
        if not parent_families:
            return False
            
        # Check if child is in any of parent's families
        for family_member in parent_families:
            child_member = self.db.query(FamilyMember).filter(
                and_(
                    FamilyMember.family_id == family_member.family_id,
                    FamilyMember.user_id == child_id,
                    FamilyMember.role == FamilyRole.CHILD,
                    FamilyMember.status == RelationshipStatus.ACTIVE
                )
            ).first()
            
            if child_member:
                return True
                
        return False
        
    def _create_game_quest_from_parent(self, parent_quest: ParentQuest) -> UserQuest:
        """Create a game quest from parent quest"""
        # Map parent quest to game quest
        quest_title = f"Parent Quest: {parent_quest.title}"
        quest_description = parent_quest.description or "Complete this quest assigned by your parent!"
        
        # Calculate XP based on requirements
        base_xp = 100
        if parent_quest.requirements:
            req_type = parent_quest.requirements.get("type")
            if req_type == "study_time":
                minutes = parent_quest.requirements.get("duration_minutes", 30)
                base_xp = min(500, minutes * 5)  # 5 XP per minute, max 500
            elif req_type == "problems_solved":
                problems = parent_quest.requirements.get("count", 10)
                base_xp = min(500, problems * 10)  # 10 XP per problem, max 500
            elif req_type == "chapters_read":
                chapters = parent_quest.requirements.get("count", 1)
                base_xp = min(500, chapters * 100)  # 100 XP per chapter, max 500
                
        # Create user quest
        user_quest = UserQuest(
            user_id=parent_quest.assigned_to_id,
            quest_id=None,  # Custom quest, no predefined quest
            parent_quest_id=parent_quest.id,
            status=QuestStatus.ACTIVE,
            progress=0,
            started_at=parent_quest.start_date,
            custom_data={
                "title": quest_title,
                "description": quest_description,
                "xp_reward": base_xp,
                "coin_reward": parent_quest.rewards.get("coins", 0) if parent_quest.rewards else 0,
                "requirements": parent_quest.requirements,
                "parent_rewards": parent_quest.rewards
            }
        )
        
        self.db.add(user_quest)
        
        return user_quest
        
    def update_parent_quest(self, parent_id: int, quest_id: int, 
                          update_data: ParentQuestUpdate) -> ParentQuest:
        """Update an existing parent quest"""
        try:
            # Get quest
            quest = self.db.query(ParentQuest).filter(
                and_(
                    ParentQuest.id == quest_id,
                    ParentQuest.created_by_id == parent_id
                )
            ).first()
            
            if not quest:
                raise ValueError("Quest not found or not owned by parent")
                
            # Update fields
            if update_data.title is not None:
                quest.title = update_data.title
            if update_data.description is not None:
                quest.description = update_data.description
            if update_data.requirements is not None:
                quest.requirements = update_data.requirements
            if update_data.rewards is not None:
                quest.rewards = update_data.rewards
            if update_data.end_date is not None:
                quest.end_date = update_data.end_date
            if update_data.is_recurring is not None:
                quest.is_recurring = update_data.is_recurring
            if update_data.recurrence_pattern is not None:
                quest.recurrence_pattern = update_data.recurrence_pattern
                
            quest.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            return quest
            
        except Exception as e:
            logger.error(f"Failed to update parent quest: {e}")
            self.db.rollback()
            raise
            
    def cancel_parent_quest(self, parent_id: int, quest_id: int) -> bool:
        """Cancel a parent quest"""
        try:
            quest = self.db.query(ParentQuest).filter(
                and_(
                    ParentQuest.id == quest_id,
                    ParentQuest.created_by_id == parent_id
                )
            ).first()
            
            if not quest:
                return False
                
            quest.status = "cancelled"
            quest.updated_at = datetime.utcnow()
            
            # Cancel corresponding user quest
            user_quest = self.db.query(UserQuest).filter(
                UserQuest.parent_quest_id == quest_id
            ).first()
            
            if user_quest:
                user_quest.status = QuestStatus.CANCELLED
                user_quest.completed_at = datetime.utcnow()
                
            self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel parent quest: {e}")
            self.db.rollback()
            return False
            
    def record_quest_progress(self, child_id: int, quest_id: int, 
                            progress_data: Dict[str, Any]) -> bool:
        """Record progress on a parent quest"""
        try:
            # Verify quest belongs to child
            quest = self.db.query(ParentQuest).filter(
                and_(
                    ParentQuest.id == quest_id,
                    ParentQuest.assigned_to_id == child_id,
                    ParentQuest.status == "active"
                )
            ).first()
            
            if not quest:
                return False
                
            # Create progress log
            progress_log = QuestProgressLog(
                parent_quest_id=quest_id,
                user_id=child_id,
                progress_type=progress_data.get("type"),
                progress_value=progress_data.get("value"),
                progress_metadata=progress_data.get("metadata", {})
            )
            
            self.db.add(progress_log)
            
            # Update quest completion rate
            completion_rate = self._calculate_quest_completion(quest, progress_data)
            quest.completion_rate = completion_rate
            
            # Check if quest is completed
            if completion_rate >= 100:
                quest.status = "completed"
                quest.completed_at = datetime.utcnow()
                
                # Complete corresponding user quest
                user_quest = self.db.query(UserQuest).filter(
                    UserQuest.parent_quest_id == quest_id
                ).first()
                
                if user_quest:
                    user_quest.status = QuestStatus.COMPLETED
                    user_quest.progress = 100
                    user_quest.completed_at = datetime.utcnow()
                    
                    # Award rewards
                    self._award_quest_rewards(child_id, quest)
                    
            self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to record quest progress: {e}")
            self.db.rollback()
            return False
            
    def _calculate_quest_completion(self, quest: ParentQuest, 
                                  progress_data: Dict[str, Any]) -> int:
        """Calculate quest completion percentage"""
        if not quest.requirements:
            return 0
            
        req_type = quest.requirements.get("type")
        
        # Get all progress logs for this quest
        progress_logs = self.db.query(QuestProgressLog).filter(
            QuestProgressLog.parent_quest_id == quest.id
        ).all()
        
        if req_type == "study_time":
            total_minutes = sum(log.progress_value for log in progress_logs 
                              if log.progress_type == "time_spent")
            required_minutes = quest.requirements.get("duration_minutes", 30)
            return min(100, int(total_minutes / required_minutes * 100))
            
        elif req_type == "problems_solved":
            total_problems = sum(log.progress_value for log in progress_logs 
                               if log.progress_type == "problems_solved")
            required_problems = quest.requirements.get("count", 10)
            return min(100, int(total_problems / required_problems * 100))
            
        elif req_type == "chapters_read":
            chapters_read = sum(log.progress_value for log in progress_logs 
                              if log.progress_type == "chapters_read")
            required_chapters = quest.requirements.get("count", 1)
            return min(100, int(chapters_read / required_chapters * 100))
            
        elif req_type == "consecutive_days":
            # Check consecutive days logic
            unique_days = set()
            for log in progress_logs:
                if log.progress_type == "daily_progress":
                    unique_days.add(log.logged_at.date())
                    
            # Check if days are consecutive
            if unique_days:
                sorted_days = sorted(unique_days)
                consecutive_count = 1
                
                for i in range(1, len(sorted_days)):
                    if (sorted_days[i] - sorted_days[i-1]).days == 1:
                        consecutive_count += 1
                    else:
                        consecutive_count = 1  # Reset if not consecutive
                        
                required_days = quest.requirements.get("target_days", 7)
                return min(100, int(consecutive_count / required_days * 100))
                
        return 0
        
    def _award_quest_rewards(self, child_id: int, quest: ParentQuest):
        """Award rewards for completing a parent quest"""
        try:
            # Get child user
            child = self.db.query(User).filter(User.id == child_id).first()
            if not child:
                return
                
            rewards = quest.rewards or {}
            
            # Award XP
            if "xp" in rewards:
                from app.services.gamification_service import GamificationService
                gamification_service = GamificationService(self.db)
                gamification_service.add_experience(child_id, rewards["xp"], "parent_quest_completion")
                
            # Award coins
            if "coins" in rewards:
                # This would integrate with your economy system
                pass
                
            # Award badges
            if "badges" in rewards:
                # This would integrate with your achievement system
                pass
                
            # Record real-world rewards for parent notification
            if "real_world" in rewards:
                # Notify parent about real-world reward to give
                from app.core.family_monitoring import monitoring_service
                if monitoring_service:
                    asyncio.create_task(
                        monitoring_service._create_alert(
                            AlertType.GOAL_ACHIEVED,
                            child_id,
                            f"Quest completed! Real-world reward: {rewards['real_world']}",
                            "success",
                            {"quest_title": quest.title, "reward": rewards['real_world']}
                        )
                    )
                    
        except Exception as e:
            logger.error(f"Failed to award quest rewards: {e}")
            
    def get_child_quests(self, child_id: int, status: Optional[str] = None) -> List[ParentQuest]:
        """Get all quests assigned to a child"""
        query = self.db.query(ParentQuest).filter(
            ParentQuest.assigned_to_id == child_id
        )
        
        if status:
            query = query.filter(ParentQuest.status == status)
            
        return query.order_by(ParentQuest.created_at.desc()).all()
        
    def get_parent_created_quests(self, parent_id: int, 
                                child_id: Optional[int] = None) -> List[ParentQuest]:
        """Get all quests created by a parent"""
        query = self.db.query(ParentQuest).filter(
            ParentQuest.created_by_id == parent_id
        )
        
        if child_id:
            query = query.filter(ParentQuest.assigned_to_id == child_id)
            
        return query.order_by(ParentQuest.created_at.desc()).all()
        
    def process_recurring_quests(self):
        """Process recurring quests and create new instances"""
        try:
            # Get all active recurring quests
            recurring_quests = self.db.query(ParentQuest).filter(
                and_(
                    ParentQuest.is_recurring == True,
                    ParentQuest.status == "active",
                    ParentQuest.end_date <= datetime.utcnow()
                )
            ).all()
            
            for quest in recurring_quests:
                # Check recurrence pattern
                pattern = quest.recurrence_pattern or {}
                
                if pattern.get("type") == "daily":
                    # Create new quest for tomorrow
                    new_quest = ParentQuest(
                        family_id=quest.family_id,
                        created_by_id=quest.created_by_id,
                        assigned_to_id=quest.assigned_to_id,
                        title=quest.title,
                        description=quest.description,
                        quest_type=quest.quest_type,
                        requirements=quest.requirements,
                        rewards=quest.rewards,
                        start_date=quest.end_date + timedelta(days=1),
                        end_date=quest.end_date + timedelta(days=2),
                        is_recurring=True,
                        recurrence_pattern=quest.recurrence_pattern,
                        status="active"
                    )
                    
                    self.db.add(new_quest)
                    
                    # Create game quest
                    self._create_game_quest_from_parent(new_quest)
                    
                elif pattern.get("type") == "weekly":
                    # Create new quest for next week
                    new_quest = ParentQuest(
                        family_id=quest.family_id,
                        created_by_id=quest.created_by_id,
                        assigned_to_id=quest.assigned_to_id,
                        title=quest.title,
                        description=quest.description,
                        quest_type=quest.quest_type,
                        requirements=quest.requirements,
                        rewards=quest.rewards,
                        start_date=quest.end_date + timedelta(days=1),
                        end_date=quest.end_date + timedelta(days=8),
                        is_recurring=True,
                        recurrence_pattern=quest.recurrence_pattern,
                        status="active"
                    )
                    
                    self.db.add(new_quest)
                    
                    # Create game quest
                    self._create_game_quest_from_parent(new_quest)
                    
                # Mark old quest as completed
                quest.status = "expired"
                
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to process recurring quests: {e}")
            self.db.rollback()