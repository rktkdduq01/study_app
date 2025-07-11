"""
Schemas for content-related operations
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class DifficultyLevel(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class ContentType(str, Enum):
    lesson = "lesson"
    quiz = "quiz"
    exercise = "exercise"
    video = "video"
    interactive = "interactive"
    reading = "reading"


class ContentGenerationRequest(BaseModel):
    """Request model for content generation"""
    subject: str = Field(..., description="Subject for content generation")
    topic: str = Field(..., description="Specific topic within the subject")
    difficulty: DifficultyLevel = Field(..., description="Difficulty level")
    context: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional context for personalization"
    )
    
    @validator('subject')
    def validate_subject(cls, v):
        allowed_subjects = [
            "math", "science", "language", "reading", 
            "history", "geography", "computer_science", "art"
        ]
        if v not in allowed_subjects:
            raise ValueError(f"Subject must be one of: {', '.join(allowed_subjects)}")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "subject": "math",
                "topic": "fractions",
                "difficulty": "beginner",
                "context": {
                    "learning_style": "visual",
                    "previous_score": 85
                }
            }
        }


class ContentSection(BaseModel):
    """Model for a content section"""
    type: str
    title: str
    content: Optional[str] = None
    visual: Optional[Any] = None
    interactive: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class GeneratedContent(BaseModel):
    """Model for generated content"""
    topic: str
    difficulty: str
    sections: List[ContentSection]
    practice_problems: Optional[List[Dict[str, Any]]] = None
    experiments: Optional[List[Dict[str, Any]]] = None
    timeline: Optional[Dict[str, Any]] = None
    interactive_features: Optional[Dict[str, Any]] = None
    coding_environment: Optional[Dict[str, Any]] = None
    digital_tools: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any]
    adaptive_features: Dict[str, Any]


class ContentGenerationResponse(BaseModel):
    """Response model for content generation"""
    success: bool
    content: Dict[str, Any]
    message: str
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "content": {
                    "topic": "fractions",
                    "difficulty": "beginner",
                    "sections": [
                        {
                            "type": "concept",
                            "title": "What are Fractions?",
                            "content": "A fraction represents a part of a whole..."
                        }
                    ],
                    "metadata": {
                        "generated_at": "2024-01-20T10:30:00Z",
                        "estimated_completion_time": 15
                    }
                },
                "message": "Content generated successfully"
            }
        }


class ContentCreate(BaseModel):
    """Schema for creating content"""
    title: str = Field(..., min_length=1, max_length=200)
    slug: Optional[str] = Field(None, regex="^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: Optional[str] = Field(None, max_length=500)
    content_type: ContentType
    body: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    subject_id: int
    difficulty_level: DifficultyLevel = DifficultyLevel.beginner
    estimated_duration: Optional[int] = Field(None, ge=1, le=300)
    learning_objectives: Optional[List[str]] = Field(default_factory=list)
    prerequisites: Optional[List[str]] = Field(default_factory=list)
    tags: Optional[List[str]] = Field(default_factory=list)
    is_premium: bool = False


class ContentUpdate(BaseModel):
    """Schema for updating content"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    body: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    difficulty_level: Optional[DifficultyLevel] = None
    estimated_duration: Optional[int] = Field(None, ge=1, le=300)
    learning_objectives: Optional[List[str]] = None
    prerequisites: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    is_premium: Optional[bool] = None
    change_summary: Optional[str] = Field(None, description="Summary of changes for version history")


class ContentResponse(BaseModel):
    """Schema for content response"""
    id: int
    title: str
    slug: str
    description: Optional[str]
    content_type: ContentType
    body: str
    metadata: Dict[str, Any]
    subject_id: int
    subject_name: Optional[str]
    difficulty_level: DifficultyLevel
    estimated_duration: Optional[int]
    learning_objectives: List[str]
    prerequisites: List[str]
    tags: List[str]
    is_premium: bool
    status: str
    author_id: int
    author_name: Optional[str]
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]
    view_count: int
    average_rating: Optional[float]
    
    class Config:
        orm_mode = True


class ContentListResponse(BaseModel):
    """Schema for content list response"""
    items: List[ContentResponse]
    total: int
    page: int
    page_size: int
    
    class Config:
        orm_mode = True


class ContentSearchRequest(BaseModel):
    """Schema for content search request"""
    query: Optional[str] = Field(None, description="Search query")
    content_type: Optional[ContentType] = None
    subject_id: Optional[int] = None
    difficulty_level: Optional[DifficultyLevel] = None
    tags: Optional[List[str]] = None
    is_premium: Optional[bool] = None
    status: Optional[str] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)