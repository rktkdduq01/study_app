from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from datetime import datetime

from app.models.content import (
    Curriculum, CurriculumItem, Content, 
    ContentStatus, DifficultyLevel
)
from app.models.user import User
from app.core.exceptions import BadRequestException, NotFoundException, ForbiddenException
from app.services.websocket_service import manager as ws_manager


class CurriculumValidator:
    """Validates curriculum data and business rules"""
    
    @staticmethod
    def validate_curriculum_data(data: Dict[str, Any]) -> None:
        """Validate curriculum creation/update data"""
        if not data.get('title') or len(data['title'].strip()) < 3:
            raise BadRequestException("Title must be at least 3 characters long")
        
        if len(data['title']) > 200:
            raise BadRequestException("Title cannot exceed 200 characters")
        
        if not data.get('subject_id'):
            raise BadRequestException("Subject ID is required")
    
    @staticmethod
    def validate_curriculum_items(items: List[Dict[str, Any]], db: Session) -> None:
        """Validate curriculum items"""
        if not items:
            raise BadRequestException("Curriculum must have at least one item")
        
        # Check for duplicate content
        content_ids = [item['content_id'] for item in items]
        if len(content_ids) != len(set(content_ids)):
            raise BadRequestException("Curriculum cannot contain duplicate content")
        
        # Validate content exists and is published
        for item in items:
            content = db.query(Content).filter(Content.id == item['content_id']).first()
            if not content:
                raise BadRequestException(f"Content {item['content_id']} not found")
            
            if content.status != ContentStatus.PUBLISHED:
                raise BadRequestException(f"Content '{content.title}' must be published to be added to curriculum")
    
    @staticmethod
    def validate_sequential_order(items: List[Dict[str, Any]]) -> None:
        """Validate sequential ordering of items"""
        orders = [item.get('sort_order', 0) for item in items]
        
        # Check for gaps or duplicates in ordering
        expected_orders = list(range(1, len(orders) + 1))
        sorted_orders = sorted(orders)
        
        if sorted_orders != expected_orders:
            raise BadRequestException("Curriculum items must have sequential ordering starting from 1")


class CurriculumProgressTracker:
    """Tracks user progress through curriculum"""
    
    @staticmethod
    def calculate_progress(curriculum_id: int, user_id: int, db: Session) -> Dict[str, Any]:
        """Calculate user's progress through curriculum"""
        from app.models.quest import QuestProgress  # Import here to avoid circular imports
        
        # Get curriculum items
        items = db.query(CurriculumItem)\
            .filter(CurriculumItem.curriculum_id == curriculum_id)\
            .order_by(CurriculumItem.sort_order)\
            .all()
        
        if not items:
            return {"total_items": 0, "completed_items": 0, "progress_percentage": 0}
        
        # Count completed items (simplified - could be more sophisticated)
        completed_count = 0
        for item in items:
            # Check if user has completed this content
            # This would need integration with your completion tracking system
            # For now, using placeholder logic
            completed_count += 1 if CurriculumProgressTracker._is_content_completed(
                item.content_id, user_id, db
            ) else 0
        
        progress_percentage = (completed_count / len(items)) * 100 if items else 0
        
        return {
            "total_items": len(items),
            "completed_items": completed_count,
            "progress_percentage": round(progress_percentage, 2),
            "current_item": CurriculumProgressTracker._get_current_item(items, user_id, db)
        }
    
    @staticmethod
    def _is_content_completed(content_id: int, user_id: int, db: Session) -> bool:
        """Check if user has completed specific content"""
        # This would integrate with your completion tracking system
        # Placeholder implementation
        return False
    
    @staticmethod
    def _get_current_item(items: List[CurriculumItem], user_id: int, db: Session) -> Optional[Dict]:
        """Get the current item user should work on"""
        for item in items:
            if not CurriculumProgressTracker._is_content_completed(item.content_id, user_id, db):
                return {
                    "content_id": item.content_id,
                    "content_title": item.content.title,
                    "sort_order": item.sort_order
                }
        return None


class CurriculumService:
    """Service for managing curricula"""
    
    def __init__(self):
        self.validator = CurriculumValidator()
        self.progress_tracker = CurriculumProgressTracker()
    
    def create_curriculum(
        self,
        curriculum_data: Dict[str, Any],
        creator: User,
        db: Session
    ) -> Curriculum:
        """Create a new curriculum"""
        # Validate data
        self.validator.validate_curriculum_data(curriculum_data)
        
        # Create curriculum
        curriculum = Curriculum(
            title=curriculum_data['title'],
            description=curriculum_data.get('description'),
            subject_id=curriculum_data['subject_id'],
            difficulty_level=DifficultyLevel(curriculum_data.get('difficulty_level', 'beginner')),
            estimated_duration=curriculum_data.get('estimated_duration'),
            is_sequential=curriculum_data.get('is_sequential', True),
            is_premium=curriculum_data.get('is_premium', False),
            created_by=creator.id
        )
        
        db.add(curriculum)
        db.flush()
        
        # Add items if provided
        if 'items' in curriculum_data:
            self._add_curriculum_items(curriculum, curriculum_data['items'], db)
        
        db.commit()
        
        # Send notification
        self._notify_curriculum_created(curriculum, creator)
        
        return curriculum
    
    def update_curriculum(
        self,
        curriculum_id: int,
        updates: Dict[str, Any],
        user: User,
        db: Session
    ) -> Curriculum:
        """Update existing curriculum"""
        curriculum = self._get_curriculum_or_404(curriculum_id, db)
        
        # Check permissions
        self._check_edit_permission(curriculum, user)
        
        # Validate updates
        if any(field in updates for field in ['title', 'subject_id']):
            self.validator.validate_curriculum_data({**curriculum.__dict__, **updates})
        
        # Apply updates
        for field, value in updates.items():
            if field != 'items' and hasattr(curriculum, field):
                setattr(curriculum, field, value)
        
        curriculum.updated_at = datetime.utcnow()
        
        # Update items if provided
        if 'items' in updates:
            self._update_curriculum_items(curriculum, updates['items'], db)
        
        db.commit()
        
        # Send notification
        self._notify_curriculum_updated(curriculum, user)
        
        return curriculum
    
    def delete_curriculum(self, curriculum_id: int, user: User, db: Session) -> None:
        """Delete curriculum"""
        curriculum = self._get_curriculum_or_404(curriculum_id, db)
        
        # Check permissions
        self._check_delete_permission(curriculum, user)
        
        # Archive instead of hard delete
        curriculum.status = ContentStatus.ARCHIVED
        curriculum.updated_at = datetime.utcnow()
        
        db.commit()
        
        # Send notification
        self._notify_curriculum_deleted(curriculum, user)
    
    def add_content_to_curriculum(
        self,
        curriculum_id: int,
        content_id: int,
        sort_order: int,
        is_required: bool,
        user: User,
        db: Session
    ) -> CurriculumItem:
        """Add content to curriculum"""
        curriculum = self._get_curriculum_or_404(curriculum_id, db)
        
        # Check permissions
        self._check_edit_permission(curriculum, user)
        
        # Validate content
        content = db.query(Content).filter(Content.id == content_id).first()
        if not content:
            raise NotFoundException("Content not found")
        
        if content.status != ContentStatus.PUBLISHED:
            raise BadRequestException("Only published content can be added to curriculum")
        
        # Check if content already in curriculum
        existing = db.query(CurriculumItem)\
            .filter(
                and_(
                    CurriculumItem.curriculum_id == curriculum_id,
                    CurriculumItem.content_id == content_id
                )
            ).first()
        
        if existing:
            raise BadRequestException("Content already exists in curriculum")
        
        # Adjust sort orders if necessary
        self._adjust_sort_orders(curriculum_id, sort_order, db)
        
        # Create curriculum item
        item = CurriculumItem(
            curriculum_id=curriculum_id,
            content_id=content_id,
            sort_order=sort_order,
            is_required=is_required
        )
        
        db.add(item)
        db.commit()
        
        return item
    
    def remove_content_from_curriculum(
        self,
        curriculum_id: int,
        content_id: int,
        user: User,
        db: Session
    ) -> None:
        """Remove content from curriculum"""
        curriculum = self._get_curriculum_or_404(curriculum_id, db)
        
        # Check permissions
        self._check_edit_permission(curriculum, user)
        
        # Find and remove item
        item = db.query(CurriculumItem)\
            .filter(
                and_(
                    CurriculumItem.curriculum_id == curriculum_id,
                    CurriculumItem.content_id == content_id
                )
            ).first()
        
        if not item:
            raise NotFoundException("Content not found in curriculum")
        
        db.delete(item)
        
        # Reorder remaining items
        self._reorder_items_after_removal(curriculum_id, item.sort_order, db)
        
        db.commit()
    
    def reorder_curriculum_items(
        self,
        curriculum_id: int,
        item_orders: List[Dict[str, int]],  # [{"content_id": 1, "sort_order": 1}, ...]
        user: User,
        db: Session
    ) -> None:
        """Reorder curriculum items"""
        curriculum = self._get_curriculum_or_404(curriculum_id, db)
        
        # Check permissions
        self._check_edit_permission(curriculum, user)
        
        # Validate new ordering
        orders = [item['sort_order'] for item in item_orders]
        if sorted(orders) != list(range(1, len(orders) + 1)):
            raise BadRequestException("Invalid ordering: must be sequential starting from 1")
        
        # Update orders
        for item_data in item_orders:
            item = db.query(CurriculumItem)\
                .filter(
                    and_(
                        CurriculumItem.curriculum_id == curriculum_id,
                        CurriculumItem.content_id == item_data['content_id']
                    )
                ).first()
            
            if item:
                item.sort_order = item_data['sort_order']
        
        db.commit()
    
    def get_curriculum_progress(
        self,
        curriculum_id: int,
        user_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """Get user's progress through curriculum"""
        curriculum = self._get_curriculum_or_404(curriculum_id, db)
        
        return self.progress_tracker.calculate_progress(curriculum_id, user_id, db)
    
    def search_curricula(
        self,
        query: str,
        filters: Dict[str, Any],
        db: Session,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[Curriculum], int]:
        """Search curricula with filters"""
        base_query = db.query(Curriculum)
        
        # Text search
        if query:
            base_query = base_query.filter(
                or_(
                    Curriculum.title.ilike(f"%{query}%"),
                    Curriculum.description.ilike(f"%{query}%")
                )
            )
        
        # Apply filters
        if filters.get('subject_id'):
            base_query = base_query.filter(Curriculum.subject_id == filters['subject_id'])
        
        if filters.get('difficulty_level'):
            base_query = base_query.filter(Curriculum.difficulty_level == filters['difficulty_level'])
        
        if filters.get('status'):
            base_query = base_query.filter(Curriculum.status == filters['status'])
        
        if filters.get('is_premium') is not None:
            base_query = base_query.filter(Curriculum.is_premium == filters['is_premium'])
        
        # Get total count
        total = base_query.count()
        
        # Apply pagination and ordering
        curricula = base_query.order_by(desc(Curriculum.created_at))\
            .limit(limit).offset(offset).all()
        
        return curricula, total
    
    def _add_curriculum_items(
        self,
        curriculum: Curriculum,
        items_data: List[Dict[str, Any]],
        db: Session
    ) -> None:
        """Add items to curriculum"""
        self.validator.validate_curriculum_items(items_data, db)
        self.validator.validate_sequential_order(items_data)
        
        for item_data in items_data:
            item = CurriculumItem(
                curriculum_id=curriculum.id,
                content_id=item_data['content_id'],
                sort_order=item_data['sort_order'],
                is_required=item_data.get('is_required', True),
                unlock_criteria=item_data.get('unlock_criteria', {})
            )
            db.add(item)
    
    def _update_curriculum_items(
        self,
        curriculum: Curriculum,
        items_data: List[Dict[str, Any]],
        db: Session
    ) -> None:
        """Update curriculum items (replace all)"""
        # Remove existing items
        db.query(CurriculumItem)\
            .filter(CurriculumItem.curriculum_id == curriculum.id)\
            .delete()
        
        # Add new items
        self._add_curriculum_items(curriculum, items_data, db)
    
    def _adjust_sort_orders(self, curriculum_id: int, new_order: int, db: Session) -> None:
        """Adjust sort orders when inserting new item"""
        # Increment orders for items at or after the new position
        db.query(CurriculumItem)\
            .filter(
                and_(
                    CurriculumItem.curriculum_id == curriculum_id,
                    CurriculumItem.sort_order >= new_order
                )
            )\
            .update({CurriculumItem.sort_order: CurriculumItem.sort_order + 1})
    
    def _reorder_items_after_removal(self, curriculum_id: int, removed_order: int, db: Session) -> None:
        """Reorder items after removing one"""
        # Decrement orders for items after the removed position
        db.query(CurriculumItem)\
            .filter(
                and_(
                    CurriculumItem.curriculum_id == curriculum_id,
                    CurriculumItem.sort_order > removed_order
                )
            )\
            .update({CurriculumItem.sort_order: CurriculumItem.sort_order - 1})
    
    def _get_curriculum_or_404(self, curriculum_id: int, db: Session) -> Curriculum:
        """Get curriculum or raise 404"""
        curriculum = db.query(Curriculum).filter(Curriculum.id == curriculum_id).first()
        if not curriculum:
            raise NotFoundException("Curriculum not found")
        return curriculum
    
    def _check_edit_permission(self, curriculum: Curriculum, user: User) -> None:
        """Check if user can edit curriculum"""
        if curriculum.created_by != user.id and user.role.value != "admin":
            raise ForbiddenException("You don't have permission to edit this curriculum")
    
    def _check_delete_permission(self, curriculum: Curriculum, user: User) -> None:
        """Check if user can delete curriculum"""
        if curriculum.created_by != user.id and user.role.value != "admin":
            raise ForbiddenException("You don't have permission to delete this curriculum")
    
    # Notification methods
    async def _notify_curriculum_created(self, curriculum: Curriculum, creator: User) -> None:
        """Notify about curriculum creation"""
        await ws_manager.send_notification(
            user_id=creator.id,
            notification={
                "type": "curriculum_created",
                "curriculum_id": curriculum.id,
                "title": curriculum.title,
                "message": f"Curriculum '{curriculum.title}' created successfully"
            }
        )
    
    async def _notify_curriculum_updated(self, curriculum: Curriculum, user: User) -> None:
        """Notify about curriculum update"""
        await ws_manager.send_notification(
            user_id=user.id,
            notification={
                "type": "curriculum_updated",
                "curriculum_id": curriculum.id,
                "title": curriculum.title,
                "message": f"Curriculum '{curriculum.title}' updated successfully"
            }
        )
    
    async def _notify_curriculum_deleted(self, curriculum: Curriculum, user: User) -> None:
        """Notify about curriculum deletion"""
        await ws_manager.send_notification(
            user_id=user.id,
            notification={
                "type": "curriculum_deleted",
                "curriculum_id": curriculum.id,
                "title": curriculum.title,
                "message": f"Curriculum '{curriculum.title}' archived successfully"
            }
        )