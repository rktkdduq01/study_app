"""
Personalized Content model for AI-generated learning materials
"""
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class PersonalizedContent(Base):
    """Model for storing AI-generated personalized content"""
    __tablename__ = "personalized_content"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Content details
    subject = Column(String(100), nullable=False)
    topic = Column(String(200), nullable=False)
    content_type = Column(String(50), nullable=False)  # lesson, practice, explanation, etc.
    difficulty_level = Column(Integer, default=5)
    
    # Generated content
    content = Column(JSON, nullable=False)  # Structured content data
    adaptation_reason = Column(Text)  # Why this content was generated this way
    
    # Metadata
    generation_model = Column(String(50), default="gpt-4")
    generation_params = Column(JSON)  # Parameters used for generation
    
    # Usage tracking
    views = Column(Integer, default=0)
    completion_rate = Column(Float, default=0.0)
    effectiveness_score = Column(Float)  # Based on user performance
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="personalized_contents")