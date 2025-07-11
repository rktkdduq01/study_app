from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum

from app.models.content import ContentType, ContentStatus, DifficultyLevel


# Base schemas
class ContentTypeEnum(str, Enum):
    lesson = "lesson"
    quiz = "quiz"
    exercise = "exercise"
    video = "video"
    article = "article"
    interactive = "interactive"
    game = "game"
    assessment = "assessment"


class ContentStatusEnum(str, Enum):
    draft = "draft"
    review = "review"
    published = "published"
    archived = "archived"


class DifficultyLevelEnum(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"
    expert = "expert"


# Content Schemas
class ContentBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=200, description="Content title")
    description: Optional[str] = Field(None, max_length=1000, description="Content description")
    content_type: ContentTypeEnum = Field(..., description="Type of content")
    subject_id: int = Field(..., gt=0, description="Subject ID")
    difficulty_level: DifficultyLevelEnum = Field(DifficultyLevelEnum.beginner, description="Difficulty level")
    estimated_duration: Optional[int] = Field(None, gt=0, description="Estimated duration in minutes")
    learning_objectives: List[str] = Field(default=[], description="Learning objectives")
    prerequisites: List[int] = Field(default=[], description="Prerequisite content IDs")
    tags: List[str] = Field(default=[], description="Content tags")
    is_premium: bool = Field(False, description="Is premium content")


class ContentCreate(ContentBase):
    slug: Optional[str] = Field(None, max_length=250, description="Content slug (auto-generated if not provided)")
    body: str = Field(..., min_length=10, description="Content body")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")
    assets: List[Dict[str, Any]] = Field(default=[], description="Associated assets")

    @validator('slug')
    def validate_slug(cls, v):
        if v is not None:
            import re
            if not re.match(r'^[a-zA-Z0-9_-]+$', v):
                raise ValueError('Slug can only contain letters, numbers, hyphens, and underscores')
        return v

    @validator('tags')
    def validate_tags(cls, v):
        if len(v) > 20:
            raise ValueError('Maximum 20 tags allowed')
        for tag in v:
            if len(tag) > 50:
                raise ValueError('Tag length cannot exceed 50 characters')
        return v


class ContentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    body: Optional[str] = Field(None, min_length=10)
    difficulty_level: Optional[DifficultyLevelEnum] = None
    estimated_duration: Optional[int] = Field(None, gt=0)
    learning_objectives: Optional[List[str]] = None
    prerequisites: Optional[List[int]] = None
    tags: Optional[List[str]] = None
    is_premium: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None
    assets: Optional[List[Dict[str, Any]]] = None
    change_summary: Optional[str] = Field(None, max_length=500, description="Summary of changes")

    @validator('tags')
    def validate_tags(cls, v):
        if v is not None and len(v) > 20:
            raise ValueError('Maximum 20 tags allowed')
        return v


class ContentResponse(BaseModel):
    id: int
    title: str
    slug: str
    description: Optional[str]
    content_type: str
    status: str
    body: Optional[str]
    subject_id: int
    difficulty_level: str
    estimated_duration: Optional[int]
    learning_objectives: List[str]
    prerequisites: List[int]
    tags: List[str]
    is_featured: bool
    is_premium: bool
    view_count: int
    completion_rate: float
    average_rating: float
    total_ratings: int
    version: str
    author_id: int
    editor_id: Optional[int]
    published_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]
    assets: List[Dict[str, Any]]

    class Config:
        from_attributes = True


class ContentListResponse(BaseModel):
    items: List[ContentResponse]
    total: int
    limit: int
    offset: int


class ContentSearchFilters(BaseModel):
    content_type: Optional[ContentTypeEnum] = None
    subject_id: Optional[int] = None
    difficulty_level: Optional[DifficultyLevelEnum] = None
    status: Optional[ContentStatusEnum] = None
    is_premium: Optional[bool] = None
    tags: Optional[List[str]] = None


# Curriculum Schemas
class CurriculumItemCreate(BaseModel):
    content_id: int = Field(..., gt=0, description="Content ID")
    sort_order: int = Field(..., gt=0, description="Sort order")
    is_required: bool = Field(True, description="Is content required")
    unlock_criteria: Dict[str, Any] = Field(default={}, description="Unlock criteria")


class CurriculumBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=200, description="Curriculum title")
    description: Optional[str] = Field(None, max_length=1000, description="Curriculum description")
    subject_id: int = Field(..., gt=0, description="Subject ID")
    difficulty_level: DifficultyLevelEnum = Field(DifficultyLevelEnum.beginner, description="Difficulty level")
    estimated_duration: Optional[int] = Field(None, gt=0, description="Total duration in hours")
    is_sequential: bool = Field(True, description="Must complete in order")
    is_premium: bool = Field(False, description="Is premium curriculum")


class CurriculumCreate(CurriculumBase):
    items: List[CurriculumItemCreate] = Field(default=[], description="Curriculum items")

    @validator('items')
    def validate_items(cls, v):
        if len(v) > 100:
            raise ValueError('Maximum 100 items allowed per curriculum')
        
        # Check for unique sort orders
        orders = [item.sort_order for item in v]
        if len(orders) != len(set(orders)):
            raise ValueError('Sort orders must be unique')
        
        # Check for unique content IDs
        content_ids = [item.content_id for item in v]
        if len(content_ids) != len(set(content_ids)):
            raise ValueError('Content IDs must be unique')
        
        return v


class CurriculumUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    difficulty_level: Optional[DifficultyLevelEnum] = None
    estimated_duration: Optional[int] = Field(None, gt=0)
    is_sequential: Optional[bool] = None
    is_premium: Optional[bool] = None
    items: Optional[List[CurriculumItemCreate]] = None

    @validator('items')
    def validate_items(cls, v):
        if v is not None and len(v) > 100:
            raise ValueError('Maximum 100 items allowed per curriculum')
        return v


class CurriculumItemResponse(BaseModel):
    id: int
    content_id: int
    content_title: str
    sort_order: int
    is_required: bool
    unlock_criteria: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class CurriculumResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    subject_id: int
    difficulty_level: str
    estimated_duration: Optional[int]
    is_sequential: bool
    status: str
    is_premium: bool
    created_by: int
    created_at: datetime
    updated_at: datetime
    items: List[CurriculumItemResponse] = []

    class Config:
        from_attributes = True


class CurriculumSearchFilters(BaseModel):
    subject_id: Optional[int] = None
    difficulty_level: Optional[DifficultyLevelEnum] = None
    status: Optional[ContentStatusEnum] = None
    is_premium: Optional[bool] = None


# Template Schemas
class TemplateBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100, description="Template name")
    description: Optional[str] = Field(None, max_length=1000, description="Template description")
    content_type: ContentTypeEnum = Field(..., description="Content type for this template")


class TemplateCreate(TemplateBase):
    template_body: Optional[str] = Field(None, description="Template body with placeholders")
    default_metadata: Dict[str, Any] = Field(default={}, description="Default metadata")
    required_fields: List[str] = Field(default=[], description="Required template fields")

    @validator('required_fields')
    def validate_required_fields(cls, v):
        if len(v) > 50:
            raise ValueError('Maximum 50 required fields allowed')
        return v


class TemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    template_body: Optional[str] = None
    default_metadata: Optional[Dict[str, Any]] = None
    required_fields: Optional[List[str]] = None

    @validator('required_fields')
    def validate_required_fields(cls, v):
        if v is not None and len(v) > 50:
            raise ValueError('Maximum 50 required fields allowed')
        return v


class TemplateResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    content_type: str
    template_body: Optional[str]
    default_metadata: Dict[str, Any]
    required_fields: List[str]
    is_active: bool
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True


# Content Version Schemas
class ContentVersionResponse(BaseModel):
    id: int
    content_id: int
    version: str
    title: str
    change_summary: Optional[str]
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True


# Content Comment Schemas
class ContentCommentCreate(BaseModel):
    comment: str = Field(..., min_length=1, max_length=1000, description="Comment text")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating (1-5)")
    parent_id: Optional[int] = Field(None, description="Parent comment ID for replies")


class ContentCommentResponse(BaseModel):
    id: int
    content_id: int
    user_id: int
    comment: str
    rating: Optional[int]
    is_public: bool
    is_approved: bool
    parent_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    replies: List['ContentCommentResponse'] = []

    class Config:
        from_attributes = True


# Update forward reference
ContentCommentResponse.model_rebuild()


# Analytics Schemas
class ContentAnalyticsResponse(BaseModel):
    content_id: int
    period_days: int
    total_views: int
    total_completions: int
    completion_rate: float
    average_time_spent: float
    daily_data: List[Dict[str, Union[str, int, float]]]


class DashboardStatsResponse(BaseModel):
    total_content: int
    published_content: int
    draft_content: int
    total_views: int
    total_completions: int
    average_rating: float
    popular_content: List[ContentResponse]
    recent_content: List[ContentResponse]


# Bulk Operations
class BulkContentUpdate(BaseModel):
    content_ids: List[int] = Field(..., min_items=1, max_items=100, description="Content IDs to update")
    updates: Dict[str, Any] = Field(..., description="Updates to apply")


class BulkOperationResponse(BaseModel):
    success_count: int
    error_count: int
    errors: List[Dict[str, str]] = []


# File Upload
class AssetUploadResponse(BaseModel):
    id: str
    filename: str
    url: str
    size: int
    content_type: str
    uploaded_at: datetime