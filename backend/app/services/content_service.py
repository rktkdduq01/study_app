from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from datetime import datetime, timedelta
import re
import uuid
from abc import ABC, abstractmethod

from app.models.content import (
    Content, ContentVersion, ContentComment, ContentTemplate,
    ContentAnalytics, ContentType, ContentStatus, DifficultyLevel
)
from app.models.user import User
from app.core.exceptions import BadRequestException, NotFoundException, ForbiddenException
from app.services.websocket_service import manager as ws_manager


class ContentValidator:
    """Validates content data according to business rules"""
    
    @staticmethod
    def validate_title(title: str) -> None:
        """Validate content title"""
        if not title or len(title.strip()) < 3:
            raise BadRequestException("Title must be at least 3 characters long")
        
        if len(title) > 200:
            raise BadRequestException("Title cannot exceed 200 characters")
    
    @staticmethod
    def validate_slug(slug: str) -> None:
        """Validate content slug"""
        if not slug:
            raise BadRequestException("Slug is required")
        
        # Check slug format (alphanumeric, hyphens, underscores only)
        if not re.match(r'^[a-zA-Z0-9_-]+$', slug):
            raise BadRequestException("Slug can only contain letters, numbers, hyphens, and underscores")
        
        if len(slug) > 250:
            raise BadRequestException("Slug cannot exceed 250 characters")
    
    @staticmethod
    def validate_content_body(body: str, content_type: ContentType) -> None:
        """Validate content body based on type"""
        if not body or len(body.strip()) < 10:
            raise BadRequestException("Content body must be at least 10 characters long")
        
        # Type-specific validation
        if content_type == ContentType.QUIZ and not ContentValidator._is_valid_quiz_format(body):
            raise BadRequestException("Quiz content must contain valid question format")
    
    @staticmethod
    def _is_valid_quiz_format(body: str) -> bool:
        """Validate quiz format - simplified check"""
        # Basic check for quiz structure (could be more sophisticated)
        return "question" in body.lower() or "quiz" in body.lower()


class SlugGenerator:
    """Generates unique slugs for content"""
    
    @staticmethod
    def generate_from_title(title: str, db: Session) -> str:
        """Generate unique slug from title"""
        # Create base slug from title
        base_slug = re.sub(r'[^a-zA-Z0-9\s-]', '', title.lower())
        base_slug = re.sub(r'\s+', '-', base_slug.strip())
        base_slug = re.sub(r'-+', '-', base_slug)
        
        # Ensure uniqueness
        slug = base_slug
        counter = 1
        
        while SlugGenerator._slug_exists(slug, db):
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug
    
    @staticmethod
    def _slug_exists(slug: str, db: Session) -> bool:
        """Check if slug already exists"""
        return db.query(Content).filter(Content.slug == slug).first() is not None


class ContentVersionManager:
    """Manages content versioning"""
    
    @staticmethod
    def create_version(
        content: Content,
        user: User,
        change_summary: str,
        db: Session
    ) -> ContentVersion:
        """Create a new version of content"""
        # Generate version number
        version_number = ContentVersionManager._generate_version_number(content, db)
        
        # Create version snapshot
        version = ContentVersion(
            content_id=content.id,
            version=version_number,
            title=content.title,
            body=content.body,
            metadata=content.metadata,
            learning_objectives=content.learning_objectives,
            change_summary=change_summary,
            created_by=user.id
        )
        
        db.add(version)
        
        # Update content version
        content.version = version_number
        
        return version
    
    @staticmethod
    def _generate_version_number(content: Content, db: Session) -> str:
        """Generate next version number"""
        latest_version = db.query(ContentVersion)\
            .filter(ContentVersion.content_id == content.id)\
            .order_by(desc(ContentVersion.created_at))\
            .first()
        
        if not latest_version:
            return "1.0"
        
        # Simple version increment (could be more sophisticated)
        try:
            major, minor = map(int, latest_version.version.split('.'))
            return f"{major}.{minor + 1}"
        except ValueError:
            return "1.0"


class ContentAnalyticsService:
    """Handles content analytics and metrics"""
    
    @staticmethod
    def record_view(content_id: int, user_id: Optional[int], db: Session) -> None:
        """Record a content view"""
        today = datetime.utcnow().date()
        
        # Get or create analytics record for today
        analytics = db.query(ContentAnalytics)\
            .filter(
                and_(
                    ContentAnalytics.content_id == content_id,
                    func.date(ContentAnalytics.date) == today
                )
            ).first()
        
        if not analytics:
            analytics = ContentAnalytics(
                content_id=content_id,
                date=datetime.utcnow()
            )
            db.add(analytics)
        
        # Update metrics
        analytics.views += 1
        
        # Update content view count
        content = db.query(Content).filter(Content.id == content_id).first()
        if content:
            content.view_count += 1
        
        db.commit()
    
    @staticmethod
    def record_completion(content_id: int, user_id: int, time_spent: int, db: Session) -> None:
        """Record content completion"""
        today = datetime.utcnow().date()
        
        analytics = db.query(ContentAnalytics)\
            .filter(
                and_(
                    ContentAnalytics.content_id == content_id,
                    func.date(ContentAnalytics.date) == today
                )
            ).first()
        
        if analytics:
            analytics.completions += 1
            analytics.time_spent += time_spent
            
            # Update completion rate
            content = db.query(Content).filter(Content.id == content_id).first()
            if content and content.view_count > 0:
                total_completions = db.query(func.sum(ContentAnalytics.completions))\
                    .filter(ContentAnalytics.content_id == content_id).scalar() or 0
                content.completion_rate = (total_completions / content.view_count) * 100
        
        db.commit()


class IContentService(ABC):
    """Interface for content service"""
    
    @abstractmethod
    def create_content(self, content_data: Dict[str, Any], author: User, db: Session) -> Content:
        pass
    
    @abstractmethod
    def update_content(self, content_id: int, updates: Dict[str, Any], user: User, db: Session) -> Content:
        pass
    
    @abstractmethod
    def delete_content(self, content_id: int, user: User, db: Session) -> None:
        pass
    
    @abstractmethod
    def publish_content(self, content_id: int, user: User, db: Session) -> Content:
        pass


class ContentService(IContentService):
    """Main content management service"""
    
    def __init__(self):
        self.validator = ContentValidator()
        self.slug_generator = SlugGenerator()
        self.version_manager = ContentVersionManager()
        self.analytics_service = ContentAnalyticsService()
    
    def create_content(
        self,
        content_data: Dict[str, Any],
        author: User,
        db: Session
    ) -> Content:
        """Create new content"""
        # Validate input data
        self._validate_content_data(content_data)
        
        # Generate slug if not provided
        slug = content_data.get('slug')
        if not slug:
            slug = self.slug_generator.generate_from_title(content_data['title'], db)
        else:
            self.validator.validate_slug(slug)
            if self.slug_generator._slug_exists(slug, db):
                raise BadRequestException("Slug already exists")
        
        # Create content
        content = Content(
            title=content_data['title'],
            slug=slug,
            description=content_data.get('description'),
            content_type=ContentType(content_data['content_type']),
            body=content_data.get('body', ''),
            metadata=content_data.get('metadata', {}),
            subject_id=content_data['subject_id'],
            difficulty_level=DifficultyLevel(content_data.get('difficulty_level', 'beginner')),
            estimated_duration=content_data.get('estimated_duration'),
            learning_objectives=content_data.get('learning_objectives', []),
            prerequisites=content_data.get('prerequisites', []),
            tags=content_data.get('tags', []),
            is_premium=content_data.get('is_premium', False),
            author_id=author.id
        )
        
        db.add(content)
        db.flush()
        
        # Create initial version
        self.version_manager.create_version(
            content, author, "Initial version", db
        )
        
        db.commit()
        
        # Send notification
        self._notify_content_created(content, author)
        
        return content
    
    def update_content(
        self,
        content_id: int,
        updates: Dict[str, Any],
        user: User,
        db: Session
    ) -> Content:
        """Update existing content"""
        content = self._get_content_or_404(content_id, db)
        
        # Check permissions
        self._check_edit_permission(content, user)
        
        # Validate updates
        if 'title' in updates:
            self.validator.validate_title(updates['title'])
        
        if 'body' in updates and 'content_type' in updates:
            self.validator.validate_content_body(
                updates['body'], 
                ContentType(updates['content_type'])
            )
        
        # Apply updates
        old_values = {}
        for field, value in updates.items():
            if hasattr(content, field):
                old_values[field] = getattr(content, field)
                setattr(content, field, value)
        
        content.editor_id = user.id
        content.updated_at = datetime.utcnow()
        
        # Create version if significant changes
        if self._has_significant_changes(updates):
            change_summary = updates.get('change_summary', 'Content updated')
            self.version_manager.create_version(content, user, change_summary, db)
        
        db.commit()
        
        # Send notification
        self._notify_content_updated(content, user, old_values)
        
        return content
    
    def delete_content(self, content_id: int, user: User, db: Session) -> None:
        """Delete content (soft delete by archiving)"""
        content = self._get_content_or_404(content_id, db)
        
        # Check permissions
        self._check_delete_permission(content, user)
        
        # Archive instead of delete
        content.status = ContentStatus.ARCHIVED
        content.updated_at = datetime.utcnow()
        
        db.commit()
        
        # Send notification
        self._notify_content_deleted(content, user)
    
    def publish_content(self, content_id: int, user: User, db: Session) -> Content:
        """Publish content"""
        content = self._get_content_or_404(content_id, db)
        
        # Check permissions
        self._check_publish_permission(content, user)
        
        # Validate content is ready for publishing
        self._validate_for_publishing(content)
        
        # Publish
        content.publish()
        content.updated_at = datetime.utcnow()
        
        db.commit()
        
        # Send notification
        self._notify_content_published(content, user)
        
        return content
    
    def get_content_by_id(self, content_id: int, db: Session) -> Optional[Content]:
        """Get content by ID"""
        return db.query(Content).filter(Content.id == content_id).first()
    
    def get_content_by_slug(self, slug: str, db: Session) -> Optional[Content]:
        """Get content by slug"""
        return db.query(Content).filter(Content.slug == slug).first()
    
    def search_content(
        self,
        query: str,
        filters: Dict[str, Any],
        db: Session,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[Content], int]:
        """Search content with filters"""
        base_query = db.query(Content)
        
        # Text search
        if query:
            base_query = base_query.filter(
                or_(
                    Content.title.ilike(f"%{query}%"),
                    Content.description.ilike(f"%{query}%"),
                    Content.body.ilike(f"%{query}%")
                )
            )
        
        # Apply filters
        if filters.get('content_type'):
            base_query = base_query.filter(Content.content_type == filters['content_type'])
        
        if filters.get('subject_id'):
            base_query = base_query.filter(Content.subject_id == filters['subject_id'])
        
        if filters.get('difficulty_level'):
            base_query = base_query.filter(Content.difficulty_level == filters['difficulty_level'])
        
        if filters.get('status'):
            base_query = base_query.filter(Content.status == filters['status'])
        
        if filters.get('is_premium') is not None:
            base_query = base_query.filter(Content.is_premium == filters['is_premium'])
        
        if filters.get('tags'):
            for tag in filters['tags']:
                base_query = base_query.filter(Content.tags.contains([tag]))
        
        # Get total count
        total = base_query.count()
        
        # Apply pagination and ordering
        contents = base_query.order_by(desc(Content.created_at))\
            .limit(limit).offset(offset).all()
        
        return contents, total
    
    def _validate_content_data(self, data: Dict[str, Any]) -> None:
        """Validate content creation data"""
        required_fields = ['title', 'content_type', 'subject_id']
        
        for field in required_fields:
            if field not in data:
                raise BadRequestException(f"Missing required field: {field}")
        
        self.validator.validate_title(data['title'])
        
        if 'body' in data:
            self.validator.validate_content_body(
                data['body'], 
                ContentType(data['content_type'])
            )
    
    def _get_content_or_404(self, content_id: int, db: Session) -> Content:
        """Get content or raise 404"""
        content = db.query(Content).filter(Content.id == content_id).first()
        if not content:
            raise NotFoundException("Content not found")
        return content
    
    def _check_edit_permission(self, content: Content, user: User) -> None:
        """Check if user can edit content"""
        if content.author_id != user.id and user.role.value != "admin":
            raise ForbiddenException("You don't have permission to edit this content")
    
    def _check_delete_permission(self, content: Content, user: User) -> None:
        """Check if user can delete content"""
        if content.author_id != user.id and user.role.value != "admin":
            raise ForbiddenException("You don't have permission to delete this content")
    
    def _check_publish_permission(self, content: Content, user: User) -> None:
        """Check if user can publish content"""
        if content.author_id != user.id and user.role.value not in ["admin", "editor"]:
            raise ForbiddenException("You don't have permission to publish this content")
    
    def _validate_for_publishing(self, content: Content) -> None:
        """Validate content is ready for publishing"""
        if not content.title or not content.body:
            raise BadRequestException("Content must have title and body before publishing")
        
        if len(content.body.strip()) < 50:
            raise BadRequestException("Content body must be at least 50 characters for publishing")
    
    def _has_significant_changes(self, updates: Dict[str, Any]) -> bool:
        """Check if updates warrant a new version"""
        significant_fields = ['title', 'body', 'learning_objectives', 'difficulty_level']
        return any(field in updates for field in significant_fields)
    
    # Notification methods
    async def _notify_content_created(self, content: Content, author: User) -> None:
        """Notify about content creation"""
        await ws_manager.send_notification(
            user_id=author.id,
            notification={
                "type": "content_created",
                "content_id": content.id,
                "title": content.title,
                "message": f"Content '{content.title}' created successfully"
            }
        )
    
    async def _notify_content_updated(self, content: Content, user: User, old_values: Dict) -> None:
        """Notify about content update"""
        await ws_manager.send_notification(
            user_id=user.id,
            notification={
                "type": "content_updated",
                "content_id": content.id,
                "title": content.title,
                "message": f"Content '{content.title}' updated successfully"
            }
        )
    
    async def _notify_content_deleted(self, content: Content, user: User) -> None:
        """Notify about content deletion"""
        await ws_manager.send_notification(
            user_id=user.id,
            notification={
                "type": "content_deleted",
                "content_id": content.id,
                "title": content.title,
                "message": f"Content '{content.title}' archived successfully"
            }
        )
    
    async def _notify_content_published(self, content: Content, user: User) -> None:
        """Notify about content publication"""
        await ws_manager.send_notification(
            user_id=user.id,
            notification={
                "type": "content_published",
                "content_id": content.id,
                "title": content.title,
                "message": f"Content '{content.title}' published successfully"
            }
        )