from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class LearningSession(Base):
    __tablename__ = "learning_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content_id = Column(String, nullable=False)
    content_type = Column(String, nullable=False)  # video, interactive, quiz, reading
    subject = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    difficulty_level = Column(String, nullable=False)
    
    # Session metrics
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    duration_seconds = Column(Integer, default=0)
    completion_rate = Column(Float, default=0.0)
    engagement_score = Column(Float, default=0.0)
    
    # Performance metrics
    questions_attempted = Column(Integer, default=0)
    questions_correct = Column(Integer, default=0)
    accuracy_rate = Column(Float, default=0.0)
    average_response_time = Column(Float, default=0.0)
    
    # Interaction data
    pause_count = Column(Integer, default=0)
    replay_count = Column(Integer, default=0)
    notes_taken = Column(Integer, default=0)
    help_requests = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User", back_populates="learning_sessions")
    analytics = relationship("SessionAnalytics", back_populates="session", uselist=False)


class SessionAnalytics(Base):
    __tablename__ = "session_analytics"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("learning_sessions.id"), unique=True)
    
    # Learning patterns
    focus_areas = Column(JSON)  # Topics where user spent most time
    struggle_points = Column(JSON)  # Topics with low accuracy
    mastery_indicators = Column(JSON)  # Topics with high performance
    
    # Behavioral analytics
    learning_style = Column(String)  # visual, auditory, kinesthetic, reading
    optimal_session_length = Column(Integer)  # in minutes
    peak_performance_time = Column(String)  # morning, afternoon, evening
    attention_span_pattern = Column(JSON)
    
    # Recommendations
    recommended_topics = Column(JSON)
    suggested_difficulty = Column(String)
    personalized_tips = Column(JSON)
    
    # Emotional/Engagement metrics
    frustration_indicators = Column(Integer, default=0)
    confidence_score = Column(Float, default=0.0)
    motivation_level = Column(Float, default=0.0)
    
    session = relationship("LearningSession", back_populates="analytics")


class LearningProfile(Base):
    __tablename__ = "learning_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    
    # Overall learning metrics
    total_learning_time = Column(Integer, default=0)
    average_session_duration = Column(Float, default=0.0)
    preferred_content_types = Column(JSON)
    strongest_subjects = Column(JSON)
    improvement_areas = Column(JSON)
    
    # Learning preferences
    preferred_difficulty = Column(String, default="medium")
    learning_pace = Column(String, default="moderate")  # slow, moderate, fast
    preferred_session_time = Column(String)
    learning_goals = Column(JSON)
    
    # Cognitive profile
    problem_solving_ability = Column(Float, default=0.0)
    critical_thinking_score = Column(Float, default=0.0)
    creativity_index = Column(Float, default=0.0)
    memory_retention_score = Column(Float, default=0.0)
    
    # Progress tracking
    skill_levels = Column(JSON)  # {subject: {topic: level}}
    milestone_achievements = Column(JSON)
    learning_streaks = Column(JSON)
    
    user = relationship("User", back_populates="learning_profile")


class ContentEffectiveness(Base):
    __tablename__ = "content_effectiveness"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(String, unique=True, index=True)
    content_type = Column(String)
    subject = Column(String)
    topic = Column(String)
    
    # Effectiveness metrics
    average_completion_rate = Column(Float, default=0.0)
    average_accuracy = Column(Float, default=0.0)
    engagement_score = Column(Float, default=0.0)
    difficulty_rating = Column(Float, default=0.0)
    
    # User feedback
    total_views = Column(Integer, default=0)
    positive_feedback_count = Column(Integer, default=0)
    negative_feedback_count = Column(Integer, default=0)
    improvement_suggestions = Column(JSON)
    
    # Performance distribution
    performance_distribution = Column(JSON)  # {excellent: %, good: %, needs_improvement: %}
    common_mistakes = Column(JSON)
    average_time_to_complete = Column(Float, default=0.0)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PersonalizedContent(Base):
    __tablename__ = "personalized_content"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    content_type = Column(String)  # question, explanation, example, exercise
    subject = Column(String)
    topic = Column(String)
    difficulty = Column(String)
    
    # Content details
    content_data = Column(JSON)  # Actual content (question, explanation, etc.)
    generation_context = Column(JSON)  # Why this content was generated
    learning_objective = Column(String)
    prerequisite_topics = Column(JSON)
    
    # Personalization parameters
    adaptation_reasons = Column(JSON)
    user_performance_context = Column(JSON)
    effectiveness_prediction = Column(Float)
    
    # Tracking
    presented_at = Column(DateTime)
    user_response = Column(JSON)
    effectiveness_score = Column(Float)
    feedback = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="personalized_content")