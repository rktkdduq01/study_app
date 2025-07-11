from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.models.content import ContentType, ContentStatus, DifficultyLevel
from app.services.content_service import ContentService
from app.services.curriculum_service import CurriculumService
from app.services.template_service import TemplateService
from app.services.content_service import ContentAnalyticsService
from app.schemas.cms import (
    ContentCreate, ContentUpdate, ContentResponse, ContentListResponse,
    CurriculumCreate, CurriculumUpdate, CurriculumResponse,
    TemplateCreate, TemplateUpdate, TemplateResponse,
    ContentSearchFilters, CurriculumSearchFilters
)
from app.core.exceptions import BadRequestException, NotFoundException

router = APIRouter()

# Initialize services
content_service = ContentService()
curriculum_service = CurriculumService()
template_service = TemplateService()
analytics_service = ContentAnalyticsService()


# Content Management Endpoints

@router.post("/content", response_model=ContentResponse)
async def create_content(
    content_data: ContentCreate,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Create new educational content"""
    content = content_service.create_content(
        content_data=content_data.dict(),
        author=current_user,
        db=db
    )
    
    return ContentResponse.from_orm(content)


@router.get("/content/{content_id}", response_model=ContentResponse)
def get_content(
    content_id: int = Path(..., gt=0),
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Get content by ID"""
    content = content_service.get_content_by_id(content_id, db)
    if not content:
        raise NotFoundException("Content not found")
    
    # Record view for analytics
    analytics_service.record_view(content_id, current_user.id, db)
    
    return ContentResponse.from_orm(content)


@router.get("/content/slug/{slug}", response_model=ContentResponse)
def get_content_by_slug(
    slug: str = Path(..., min_length=1),
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Get content by slug"""
    content = content_service.get_content_by_slug(slug, db)
    if not content:
        raise NotFoundException("Content not found")
    
    # Record view for analytics
    analytics_service.record_view(content.id, current_user.id, db)
    
    return ContentResponse.from_orm(content)


@router.put("/content/{content_id}", response_model=ContentResponse)
async def update_content(
    content_id: int = Path(..., gt=0),
    content_updates: ContentUpdate = Body(...),
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Update existing content"""
    content = content_service.update_content(
        content_id=content_id,
        updates=content_updates.dict(exclude_unset=True),
        user=current_user,
        db=db
    )
    
    return ContentResponse.from_orm(content)


@router.delete("/content/{content_id}")
async def delete_content(
    content_id: int = Path(..., gt=0),
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Archive content"""
    content_service.delete_content(content_id, current_user, db)
    return {"message": "Content archived successfully"}


@router.post("/content/{content_id}/publish", response_model=ContentResponse)
async def publish_content(
    content_id: int = Path(..., gt=0),
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Publish content"""
    content = content_service.publish_content(content_id, current_user, db)
    return ContentResponse.from_orm(content)


@router.get("/content", response_model=ContentListResponse)
def search_content(
    q: Optional[str] = Query(None, description="Search query"),
    content_type: Optional[ContentType] = Query(None, description="Filter by content type"),
    subject_id: Optional[int] = Query(None, description="Filter by subject"),
    difficulty_level: Optional[DifficultyLevel] = Query(None, description="Filter by difficulty"),
    status: Optional[ContentStatus] = Query(None, description="Filter by status"),
    is_premium: Optional[bool] = Query(None, description="Filter by premium status"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    limit: int = Query(20, ge=1, le=100, description="Number of items per page"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Search and filter content"""
    filters = {
        "content_type": content_type,
        "subject_id": subject_id,
        "difficulty_level": difficulty_level,
        "status": status,
        "is_premium": is_premium,
        "tags": tags
    }
    
    # Remove None values
    filters = {k: v for k, v in filters.items() if v is not None}
    
    contents, total = content_service.search_content(
        query=q or "",
        filters=filters,
        db=db,
        limit=limit,
        offset=offset
    )
    
    return ContentListResponse(
        items=[ContentResponse.from_orm(content) for content in contents],
        total=total,
        limit=limit,
        offset=offset
    )


@router.post("/content/{content_id}/complete")
async def mark_content_complete(
    content_id: int = Path(..., gt=0),
    time_spent: int = Body(..., embed=True, description="Time spent in seconds"),
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Mark content as completed by user"""
    # Verify content exists
    content = content_service.get_content_by_id(content_id, db)
    if not content:
        raise NotFoundException("Content not found")
    
    # Record completion
    analytics_service.record_completion(content_id, current_user.id, time_spent, db)
    
    return {"message": "Content completion recorded"}


# Curriculum Management Endpoints

@router.post("/curriculum", response_model=CurriculumResponse)
async def create_curriculum(
    curriculum_data: CurriculumCreate,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Create new curriculum"""
    curriculum = curriculum_service.create_curriculum(
        curriculum_data=curriculum_data.dict(),
        creator=current_user,
        db=db
    )
    
    return CurriculumResponse.from_orm(curriculum)


@router.get("/curriculum/{curriculum_id}", response_model=CurriculumResponse)
def get_curriculum(
    curriculum_id: int = Path(..., gt=0),
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Get curriculum by ID"""
    curriculum = curriculum_service._get_curriculum_or_404(curriculum_id, db)
    return CurriculumResponse.from_orm(curriculum)


@router.put("/curriculum/{curriculum_id}", response_model=CurriculumResponse)
async def update_curriculum(
    curriculum_id: int = Path(..., gt=0),
    curriculum_updates: CurriculumUpdate = Body(...),
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Update existing curriculum"""
    curriculum = curriculum_service.update_curriculum(
        curriculum_id=curriculum_id,
        updates=curriculum_updates.dict(exclude_unset=True),
        user=current_user,
        db=db
    )
    
    return CurriculumResponse.from_orm(curriculum)


@router.delete("/curriculum/{curriculum_id}")
async def delete_curriculum(
    curriculum_id: int = Path(..., gt=0),
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Archive curriculum"""
    curriculum_service.delete_curriculum(curriculum_id, current_user, db)
    return {"message": "Curriculum archived successfully"}


@router.post("/curriculum/{curriculum_id}/content/{content_id}")
async def add_content_to_curriculum(
    curriculum_id: int = Path(..., gt=0),
    content_id: int = Path(..., gt=0),
    sort_order: int = Body(..., embed=True, description="Sort order"),
    is_required: bool = Body(True, embed=True, description="Is content required"),
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Add content to curriculum"""
    curriculum_service.add_content_to_curriculum(
        curriculum_id=curriculum_id,
        content_id=content_id,
        sort_order=sort_order,
        is_required=is_required,
        user=current_user,
        db=db
    )
    
    return {"message": "Content added to curriculum successfully"}


@router.delete("/curriculum/{curriculum_id}/content/{content_id}")
async def remove_content_from_curriculum(
    curriculum_id: int = Path(..., gt=0),
    content_id: int = Path(..., gt=0),
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Remove content from curriculum"""
    curriculum_service.remove_content_from_curriculum(
        curriculum_id=curriculum_id,
        content_id=content_id,
        user=current_user,
        db=db
    )
    
    return {"message": "Content removed from curriculum successfully"}


@router.put("/curriculum/{curriculum_id}/reorder")
async def reorder_curriculum_items(
    curriculum_id: int = Path(..., gt=0),
    item_orders: List[Dict[str, int]] = Body(..., description="New ordering of items"),
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Reorder curriculum items"""
    curriculum_service.reorder_curriculum_items(
        curriculum_id=curriculum_id,
        item_orders=item_orders,
        user=current_user,
        db=db
    )
    
    return {"message": "Curriculum items reordered successfully"}


@router.get("/curriculum/{curriculum_id}/progress")
def get_curriculum_progress(
    curriculum_id: int = Path(..., gt=0),
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Get user's progress through curriculum"""
    progress = curriculum_service.get_curriculum_progress(
        curriculum_id=curriculum_id,
        user_id=current_user.id,
        db=db
    )
    
    return progress


@router.get("/curriculum")
def search_curricula(
    q: Optional[str] = Query(None, description="Search query"),
    subject_id: Optional[int] = Query(None, description="Filter by subject"),
    difficulty_level: Optional[DifficultyLevel] = Query(None, description="Filter by difficulty"),
    status: Optional[ContentStatus] = Query(None, description="Filter by status"),
    is_premium: Optional[bool] = Query(None, description="Filter by premium status"),
    limit: int = Query(20, ge=1, le=100, description="Number of items per page"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Search and filter curricula"""
    filters = {
        "subject_id": subject_id,
        "difficulty_level": difficulty_level,
        "status": status,
        "is_premium": is_premium
    }
    
    # Remove None values
    filters = {k: v for k, v in filters.items() if v is not None}
    
    curricula, total = curriculum_service.search_curricula(
        query=q or "",
        filters=filters,
        db=db,
        limit=limit,
        offset=offset
    )
    
    return {
        "items": [CurriculumResponse.from_orm(curriculum) for curriculum in curricula],
        "total": total,
        "limit": limit,
        "offset": offset
    }


# Template Management Endpoints

@router.post("/templates", response_model=TemplateResponse)
async def create_template(
    template_data: TemplateCreate,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Create new content template"""
    template = template_service.create_template(
        template_data=template_data.dict(),
        creator=current_user,
        db=db
    )
    
    return TemplateResponse.from_orm(template)


@router.get("/templates/{template_id}", response_model=TemplateResponse)
def get_template(
    template_id: int = Path(..., gt=0),
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Get template by ID"""
    template = template_service.get_template_by_id(template_id, db)
    if not template:
        raise NotFoundException("Template not found")
    
    return TemplateResponse.from_orm(template)


@router.put("/templates/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: int = Path(..., gt=0),
    template_updates: TemplateUpdate = Body(...),
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Update existing template"""
    template = template_service.update_template(
        template_id=template_id,
        updates=template_updates.dict(exclude_unset=True),
        user=current_user,
        db=db
    )
    
    return TemplateResponse.from_orm(template)


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: int = Path(..., gt=0),
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Delete template"""
    template_service.delete_template(template_id, current_user, db)
    return {"message": "Template deleted successfully"}


@router.get("/templates")
def search_templates(
    q: Optional[str] = Query(None, description="Search query"),
    content_type: Optional[ContentType] = Query(None, description="Filter by content type"),
    limit: int = Query(20, ge=1, le=100, description="Number of items per page"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Search and filter templates"""
    filters = {
        "content_type": content_type
    }
    
    # Remove None values
    filters = {k: v for k, v in filters.items() if v is not None}
    
    templates, total = template_service.search_templates(
        query=q or "",
        filters=filters,
        db=db,
        limit=limit,
        offset=offset
    )
    
    return {
        "items": [TemplateResponse.from_orm(template) for template in templates],
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/templates/type/{content_type}")
def get_templates_by_type(
    content_type: ContentType = Path(...),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Get templates by content type"""
    templates, total = template_service.get_templates_by_type(
        content_type=content_type,
        db=db,
        limit=limit,
        offset=offset
    )
    
    return {
        "items": [TemplateResponse.from_orm(template) for template in templates],
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.post("/templates/{template_id}/content")
async def create_content_from_template(
    template_id: int = Path(..., gt=0),
    variables: Dict[str, Any] = Body(..., description="Template variables"),
    content_data: Dict[str, Any] = Body(..., description="Additional content data"),
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Create content using a template"""
    merged_data = template_service.create_content_from_template(
        template_id=template_id,
        variables=variables,
        content_data=content_data,
        user=current_user,
        db=db
    )
    
    # Create the actual content
    content = content_service.create_content(
        content_data=merged_data,
        author=current_user,
        db=db
    )
    
    return ContentResponse.from_orm(content)


@router.get("/templates/{template_id}/variables")
def get_template_variables(
    template_id: int = Path(..., gt=0),
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Get list of variables used in template"""
    variables = template_service.get_template_variables(template_id, db)
    return {"variables": variables}


@router.post("/templates/{template_id}/preview")
def preview_template(
    template_id: int = Path(..., gt=0),
    variables: Dict[str, Any] = Body(..., description="Template variables"),
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Preview rendered template with variables"""
    rendered = template_service.preview_template(
        template_id=template_id,
        variables=variables,
        db=db
    )
    
    return {"rendered": rendered}


@router.post("/templates/{template_id}/duplicate")
async def duplicate_template(
    template_id: int = Path(..., gt=0),
    new_name: str = Body(..., embed=True, description="Name for the new template"),
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Create a copy of existing template"""
    template = template_service.duplicate_template(
        template_id=template_id,
        new_name=new_name,
        user=current_user,
        db=db
    )
    
    return TemplateResponse.from_orm(template)


# Analytics Endpoints

@router.get("/content/{content_id}/analytics")
def get_content_analytics(
    content_id: int = Path(..., gt=0),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """Get content analytics data"""
    # Verify content exists and user has permission
    content = content_service.get_content_by_id(content_id, db)
    if not content:
        raise NotFoundException("Content not found")
    
    if content.author_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # This would query analytics data - simplified implementation
    from datetime import datetime, timedelta
    from app.models.content import ContentAnalytics
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    analytics = db.query(ContentAnalytics)\
        .filter(
            ContentAnalytics.content_id == content_id,
            ContentAnalytics.date >= start_date,
            ContentAnalytics.date <= end_date
        )\
        .all()
    
    # Aggregate data
    total_views = sum(a.views for a in analytics)
    total_completions = sum(a.completions for a in analytics)
    avg_time_spent = sum(a.time_spent for a in analytics) / len(analytics) if analytics else 0
    
    return {
        "content_id": content_id,
        "period_days": days,
        "total_views": total_views,
        "total_completions": total_completions,
        "completion_rate": (total_completions / total_views * 100) if total_views > 0 else 0,
        "average_time_spent": avg_time_spent,
        "daily_data": [
            {
                "date": a.date.date().isoformat(),
                "views": a.views,
                "completions": a.completions,
                "time_spent": a.time_spent
            }
            for a in analytics
        ]
    }