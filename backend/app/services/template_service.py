from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from datetime import datetime

from app.models.content import ContentTemplate, ContentType
from app.models.user import User
from app.core.exceptions import BadRequestException, NotFoundException, ForbiddenException
from app.services.websocket_service import manager as ws_manager


class TemplateValidator:
    """Validates template data"""
    
    @staticmethod
    def validate_template_data(data: Dict[str, Any]) -> None:
        """Validate template creation/update data"""
        if not data.get('name') or len(data['name'].strip()) < 3:
            raise BadRequestException("Template name must be at least 3 characters long")
        
        if len(data['name']) > 100:
            raise BadRequestException("Template name cannot exceed 100 characters")
        
        if not data.get('content_type'):
            raise BadRequestException("Content type is required")
        
        try:
            ContentType(data['content_type'])
        except ValueError:
            raise BadRequestException("Invalid content type")
    
    @staticmethod
    def validate_template_body(template_body: str, content_type: ContentType) -> None:
        """Validate template body based on content type"""
        if not template_body:
            return  # Empty template is allowed
        
        # Type-specific validation
        if content_type == ContentType.QUIZ:
            TemplateValidator._validate_quiz_template(template_body)
        elif content_type == ContentType.LESSON:
            TemplateValidator._validate_lesson_template(template_body)
    
    @staticmethod
    def _validate_quiz_template(template_body: str) -> None:
        """Validate quiz template structure"""
        # Check for basic quiz structure placeholders
        required_placeholders = ['{{question}}', '{{options}}', '{{answer}}']
        for placeholder in required_placeholders:
            if placeholder not in template_body:
                raise BadRequestException(f"Quiz template must contain {placeholder} placeholder")
    
    @staticmethod
    def _validate_lesson_template(template_body: str) -> None:
        """Validate lesson template structure"""
        # Check for basic lesson structure
        if '{{content}}' not in template_body:
            raise BadRequestException("Lesson template must contain {{content}} placeholder")


class TemplateEngine:
    """Handles template rendering and processing"""
    
    @staticmethod
    def render_template(template: ContentTemplate, variables: Dict[str, Any]) -> str:
        """Render template with provided variables"""
        if not template.template_body:
            return ""
        
        rendered = template.template_body
        
        # Simple variable substitution (could be enhanced with proper template engine)
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            rendered = rendered.replace(placeholder, str(value))
        
        return rendered
    
    @staticmethod
    def extract_variables(template_body: str) -> List[str]:
        """Extract variable placeholders from template"""
        import re
        
        # Find all {{variable}} patterns
        pattern = r'\{\{(\w+)\}\}'
        matches = re.findall(pattern, template_body)
        
        return list(set(matches))  # Remove duplicates
    
    @staticmethod
    def validate_variables(template: ContentTemplate, variables: Dict[str, Any]) -> None:
        """Validate that all required variables are provided"""
        required_vars = TemplateEngine.extract_variables(template.template_body)
        
        # Check required fields from template metadata
        if template.required_fields:
            required_vars.extend(template.required_fields)
        
        missing_vars = [var for var in required_vars if var not in variables]
        
        if missing_vars:
            raise BadRequestException(f"Missing required variables: {', '.join(missing_vars)}")


class TemplateService:
    """Service for managing content templates"""
    
    def __init__(self):
        self.validator = TemplateValidator()
        self.engine = TemplateEngine()
    
    def create_template(
        self,
        template_data: Dict[str, Any],
        creator: User,
        db: Session
    ) -> ContentTemplate:
        """Create a new content template"""
        # Validate data
        self.validator.validate_template_data(template_data)
        
        content_type = ContentType(template_data['content_type'])
        template_body = template_data.get('template_body', '')
        
        if template_body:
            self.validator.validate_template_body(template_body, content_type)
        
        # Create template
        template = ContentTemplate(
            name=template_data['name'],
            description=template_data.get('description'),
            content_type=content_type,
            template_body=template_body,
            default_metadata=template_data.get('default_metadata', {}),
            required_fields=template_data.get('required_fields', []),
            created_by=creator.id
        )
        
        db.add(template)
        db.commit()
        
        # Send notification
        self._notify_template_created(template, creator)
        
        return template
    
    def update_template(
        self,
        template_id: int,
        updates: Dict[str, Any],
        user: User,
        db: Session
    ) -> ContentTemplate:
        """Update existing template"""
        template = self._get_template_or_404(template_id, db)
        
        # Check permissions
        self._check_edit_permission(template, user)
        
        # Validate updates
        if any(field in updates for field in ['name', 'content_type']):
            self.validator.validate_template_data({**template.__dict__, **updates})
        
        if 'template_body' in updates:
            content_type = ContentType(updates.get('content_type', template.content_type.value))
            self.validator.validate_template_body(updates['template_body'], content_type)
        
        # Apply updates
        for field, value in updates.items():
            if hasattr(template, field):
                setattr(template, field, value)
        
        db.commit()
        
        # Send notification
        self._notify_template_updated(template, user)
        
        return template
    
    def delete_template(self, template_id: int, user: User, db: Session) -> None:
        """Delete template"""
        template = self._get_template_or_404(template_id, db)
        
        # Check permissions
        self._check_delete_permission(template, user)
        
        # Soft delete by deactivating
        template.is_active = False
        
        db.commit()
        
        # Send notification
        self._notify_template_deleted(template, user)
    
    def get_template_by_id(self, template_id: int, db: Session) -> Optional[ContentTemplate]:
        """Get template by ID"""
        return db.query(ContentTemplate)\
            .filter(
                and_(
                    ContentTemplate.id == template_id,
                    ContentTemplate.is_active == True
                )
            ).first()
    
    def get_templates_by_type(
        self,
        content_type: ContentType,
        db: Session,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[ContentTemplate], int]:
        """Get templates by content type"""
        base_query = db.query(ContentTemplate)\
            .filter(
                and_(
                    ContentTemplate.content_type == content_type,
                    ContentTemplate.is_active == True
                )
            )
        
        total = base_query.count()
        
        templates = base_query.order_by(desc(ContentTemplate.created_at))\
            .limit(limit).offset(offset).all()
        
        return templates, total
    
    def search_templates(
        self,
        query: str,
        filters: Dict[str, Any],
        db: Session,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[ContentTemplate], int]:
        """Search templates with filters"""
        base_query = db.query(ContentTemplate)\
            .filter(ContentTemplate.is_active == True)
        
        # Text search
        if query:
            base_query = base_query.filter(
                or_(
                    ContentTemplate.name.ilike(f"%{query}%"),
                    ContentTemplate.description.ilike(f"%{query}%")
                )
            )
        
        # Apply filters
        if filters.get('content_type'):
            base_query = base_query.filter(ContentTemplate.content_type == filters['content_type'])
        
        if filters.get('created_by'):
            base_query = base_query.filter(ContentTemplate.created_by == filters['created_by'])
        
        # Get total count
        total = base_query.count()
        
        # Apply pagination and ordering
        templates = base_query.order_by(desc(ContentTemplate.created_at))\
            .limit(limit).offset(offset).all()
        
        return templates, total
    
    def create_content_from_template(
        self,
        template_id: int,
        variables: Dict[str, Any],
        content_data: Dict[str, Any],
        user: User,
        db: Session
    ) -> Dict[str, Any]:
        """Create content using a template"""
        template = self._get_template_or_404(template_id, db)
        
        # Validate variables
        self.engine.validate_variables(template, variables)
        
        # Render template
        rendered_body = self.engine.render_template(template, variables)
        
        # Merge template defaults with provided data
        merged_data = {
            'content_type': template.content_type.value,
            'body': rendered_body,
            'metadata': {**template.default_metadata, **content_data.get('metadata', {})},
            **content_data
        }
        
        return merged_data
    
    def get_template_variables(self, template_id: int, db: Session) -> List[str]:
        """Get list of variables used in template"""
        template = self._get_template_or_404(template_id, db)
        
        if not template.template_body:
            return []
        
        return self.engine.extract_variables(template.template_body)
    
    def preview_template(
        self,
        template_id: int,
        variables: Dict[str, Any],
        db: Session
    ) -> str:
        """Preview rendered template with variables"""
        template = self._get_template_or_404(template_id, db)
        
        # Don't validate variables for preview (allow partial rendering)
        return self.engine.render_template(template, variables)
    
    def duplicate_template(
        self,
        template_id: int,
        new_name: str,
        user: User,
        db: Session
    ) -> ContentTemplate:
        """Create a copy of existing template"""
        original = self._get_template_or_404(template_id, db)
        
        # Check if new name is unique
        existing = db.query(ContentTemplate)\
            .filter(
                and_(
                    ContentTemplate.name == new_name,
                    ContentTemplate.is_active == True
                )
            ).first()
        
        if existing:
            raise BadRequestException("Template name already exists")
        
        # Create duplicate
        duplicate = ContentTemplate(
            name=new_name,
            description=f"Copy of {original.name}",
            content_type=original.content_type,
            template_body=original.template_body,
            default_metadata=original.default_metadata.copy(),
            required_fields=original.required_fields.copy(),
            created_by=user.id
        )
        
        db.add(duplicate)
        db.commit()
        
        return duplicate
    
    def get_user_templates(
        self,
        user_id: int,
        db: Session,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[ContentTemplate], int]:
        """Get templates created by specific user"""
        base_query = db.query(ContentTemplate)\
            .filter(
                and_(
                    ContentTemplate.created_by == user_id,
                    ContentTemplate.is_active == True
                )
            )
        
        total = base_query.count()
        
        templates = base_query.order_by(desc(ContentTemplate.created_at))\
            .limit(limit).offset(offset).all()
        
        return templates, total
    
    def _get_template_or_404(self, template_id: int, db: Session) -> ContentTemplate:
        """Get template or raise 404"""
        template = self.get_template_by_id(template_id, db)
        if not template:
            raise NotFoundException("Template not found")
        return template
    
    def _check_edit_permission(self, template: ContentTemplate, user: User) -> None:
        """Check if user can edit template"""
        if template.created_by != user.id and user.role.value != "admin":
            raise ForbiddenException("You don't have permission to edit this template")
    
    def _check_delete_permission(self, template: ContentTemplate, user: User) -> None:
        """Check if user can delete template"""
        if template.created_by != user.id and user.role.value != "admin":
            raise ForbiddenException("You don't have permission to delete this template")
    
    # Notification methods
    async def _notify_template_created(self, template: ContentTemplate, creator: User) -> None:
        """Notify about template creation"""
        await ws_manager.send_notification(
            user_id=creator.id,
            notification={
                "type": "template_created",
                "template_id": template.id,
                "name": template.name,
                "message": f"Template '{template.name}' created successfully"
            }
        )
    
    async def _notify_template_updated(self, template: ContentTemplate, user: User) -> None:
        """Notify about template update"""
        await ws_manager.send_notification(
            user_id=user.id,
            notification={
                "type": "template_updated",
                "template_id": template.id,
                "name": template.name,
                "message": f"Template '{template.name}' updated successfully"
            }
        )
    
    async def _notify_template_deleted(self, template: ContentTemplate, user: User) -> None:
        """Notify about template deletion"""
        await ws_manager.send_notification(
            user_id=user.id,
            notification={
                "type": "template_deleted",
                "template_id": template.id,
                "name": template.name,
                "message": f"Template '{template.name}' deleted successfully"
            }
        )