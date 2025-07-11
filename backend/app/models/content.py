from typing import Optional, Dict, Any, List
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Float, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.db.base_class import Base


class ContentType(enum.Enum):
    """Content type enumeration"""
    LESSON = "lesson"
    QUIZ = "quiz"
    EXERCISE = "exercise" 
    VIDEO = "video"
    ARTICLE = "article"
    INTERACTIVE = "interactive"
    GAME = "game"
    ASSESSMENT = "assessment"


class ContentStatus(enum.Enum):
    """Content publishing status"""
    DRAFT = "draft"
    REVIEW = "review"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class DifficultyLevel(enum.Enum):
    """Difficulty level enumeration"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class Content(Base):
    """Base content model"""
    __tablename__ = "contents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    slug = Column(String(250), unique=True, nullable=False, index=True)
    description = Column(Text)
    content_type = Column(SQLEnum(ContentType), nullable=False, index=True)
    
    # Content body and metadata
    body = Column(Text)  # Main content body (HTML, Markdown, etc.)
    metadata = Column(JSON, default={})  # Additional metadata
    assets = Column(JSON, default=[])  # Associated files, images, videos
    
    # Educational properties
    subject_id = Column(Integer, ForeignKey('subjects.id'), nullable=False, index=True)
    difficulty_level = Column(SQLEnum(DifficultyLevel), default=DifficultyLevel.BEGINNER)
    estimated_duration = Column(Integer)  # Duration in minutes
    learning_objectives = Column(JSON, default=[])  # List of learning objectives
    prerequisites = Column(JSON, default=[])  # List of prerequisite content IDs
    tags = Column(JSON, default=[])  # List of tags for categorization
    
    # Publishing and versioning
    status = Column(SQLEnum(ContentStatus), default=ContentStatus.DRAFT, index=True)
    version = Column(String(20), default="1.0")
    is_featured = Column(Boolean, default=False)
    is_premium = Column(Boolean, default=False)
    
    # Analytics and engagement
    view_count = Column(Integer, default=0)
    completion_rate = Column(Float, default=0.0)  # Percentage of users who complete
    average_rating = Column(Float, default=0.0)
    total_ratings = Column(Integer, default=0)
    
    # Content management
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    editor_id = Column(Integer, ForeignKey('users.id'))  # Last editor
    published_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    subject = relationship("Subject", back_populates="contents")
    author = relationship("User", foreign_keys=[author_id])
    editor = relationship("User", foreign_keys=[editor_id])
    versions = relationship("ContentVersion", back_populates="content", cascade="all, delete-orphan")
    comments = relationship("ContentComment", back_populates="content", cascade="all, delete-orphan")
    analytics = relationship("ContentAnalytics", back_populates="content", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Content {self.title} ({self.content_type.value})>"
    
    def publish(self):
        """Publish the content"""
        self.status = ContentStatus.PUBLISHED
        self.published_at = datetime.utcnow()
    
    def archive(self):
        """Archive the content"""
        self.status = ContentStatus.ARCHIVED
    
    def update_rating(self, new_rating: float):
        """Update average rating with new rating"""
        total_score = self.average_rating * self.total_ratings
        self.total_ratings += 1
        self.average_rating = (total_score + new_rating) / self.total_ratings


class ContentVersion(Base):
    """Content version history"""
    __tablename__ = "content_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey('contents.id'), nullable=False)
    version = Column(String(20), nullable=False)
    
    # Snapshot of content at this version
    title = Column(String(200), nullable=False)
    body = Column(Text)
    metadata = Column(JSON, default={})
    learning_objectives = Column(JSON, default=[])
    
    # Version metadata
    change_summary = Column(Text)  # Description of changes
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    content = relationship("Content", back_populates="versions")
    creator = relationship("User")
    
    def __repr__(self):
        return f"<ContentVersion {self.content_id} v{self.version}>"


class ContentComment(Base):
    """Comments and feedback on content"""
    __tablename__ = "content_comments"
    
    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey('contents.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Comment data
    comment = Column(Text, nullable=False)
    rating = Column(Integer)  # 1-5 rating
    is_public = Column(Boolean, default=True)
    is_approved = Column(Boolean, default=False)
    
    # Thread support
    parent_id = Column(Integer, ForeignKey('content_comments.id'))
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    content = relationship("Content", back_populates="comments")
    user = relationship("User")
    parent = relationship("ContentComment", remote_side=[id])
    replies = relationship("ContentComment", back_populates="parent")
    
    def __repr__(self):
        return f"<ContentComment by {self.user.username}>"


class ContentCategory(Base):
    """Content categories for organization"""
    __tablename__ = "content_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(120), unique=True, nullable=False)
    description = Column(Text)
    icon = Column(String(100))  # Icon class or URL
    color = Column(String(7))  # Hex color code
    
    # Hierarchy support
    parent_id = Column(Integer, ForeignKey('content_categories.id'))
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    parent = relationship("ContentCategory", remote_side=[id])
    children = relationship("ContentCategory", back_populates="parent")
    
    def __repr__(self):
        return f"<ContentCategory {self.name}>"


class ContentTemplate(Base):
    """Templates for creating new content"""
    __tablename__ = "content_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    content_type = Column(SQLEnum(ContentType), nullable=False)
    
    # Template data
    template_body = Column(Text)  # HTML/Markdown template
    default_metadata = Column(JSON, default={})
    required_fields = Column(JSON, default=[])
    
    # Template settings
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    creator = relationship("User")
    
    def __repr__(self):
        return f"<ContentTemplate {self.name}>"


class ContentAnalytics(Base):
    """Content analytics and engagement metrics"""
    __tablename__ = "content_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey('contents.id'), nullable=False)
    
    # Date for aggregated metrics
    date = Column(DateTime, nullable=False, index=True)
    
    # Engagement metrics
    views = Column(Integer, default=0)
    unique_views = Column(Integer, default=0)
    completions = Column(Integer, default=0)
    time_spent = Column(Integer, default=0)  # Total seconds spent
    bounce_rate = Column(Float, default=0.0)  # Percentage who leave quickly
    
    # Interaction metrics
    likes = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    downloads = Column(Integer, default=0)
    
    # Performance metrics
    average_score = Column(Float, default=0.0)  # For quizzes/assessments
    completion_time = Column(Integer, default=0)  # Average completion time
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    content = relationship("Content", back_populates="analytics")
    
    def __repr__(self):
        return f"<ContentAnalytics {self.content_id} {self.date.date()}>"


class Curriculum(Base):
    """Learning curriculum composed of content"""
    __tablename__ = "curriculums"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    subject_id = Column(Integer, ForeignKey('subjects.id'), nullable=False)
    
    # Curriculum properties
    difficulty_level = Column(SQLEnum(DifficultyLevel), default=DifficultyLevel.BEGINNER)
    estimated_duration = Column(Integer)  # Total duration in hours
    is_sequential = Column(Boolean, default=True)  # Must complete in order
    
    # Publishing
    status = Column(SQLEnum(ContentStatus), default=ContentStatus.DRAFT)
    is_premium = Column(Boolean, default=False)
    
    # Management
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    subject = relationship("Subject")
    creator = relationship("User")
    items = relationship("CurriculumItem", back_populates="curriculum", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Curriculum {self.title}>"


class CurriculumItem(Base):
    """Individual items in a curriculum"""
    __tablename__ = "curriculum_items"
    
    id = Column(Integer, primary_key=True, index=True)
    curriculum_id = Column(Integer, ForeignKey('curriculums.id'), nullable=False)
    content_id = Column(Integer, ForeignKey('contents.id'), nullable=False)
    
    # Ordering and structure
    sort_order = Column(Integer, nullable=False)
    is_required = Column(Boolean, default=True)
    unlock_criteria = Column(JSON, default={})  # Conditions to unlock this item
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    curriculum = relationship("Curriculum", back_populates="items")
    content = relationship("Content")
    
    def __repr__(self):
        return f"<CurriculumItem {self.curriculum_id}-{self.sort_order}>"


# Note: Subject model relationships will be added to the existing Subject model in subject.py