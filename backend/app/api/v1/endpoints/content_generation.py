"""
API endpoints for content generation
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.models.learning_analytics import LearningProfile
from app.services.content_generation_engine import ContentGenerationEngine
from app.services.learning_analytics_service import LearningAnalyticsService
from app.schemas.content import ContentGenerationRequest, ContentGenerationResponse
from app.utils.logger import api_logger, log_api_request

router = APIRouter()
content_engine = ContentGenerationEngine()
analytics_service = LearningAnalyticsService()


@router.post("/generate", response_model=ContentGenerationResponse)
@log_api_request
async def generate_content(
    request: ContentGenerationRequest,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    """
    Generate personalized educational content for the user.
    
    Args:
        request: Content generation parameters
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Generated content with metadata
    """
    try:
        # Get user's learning profile for personalization
        learning_profile = analytics_service.get_user_learning_profile(
            db=db,
            user_id=current_user.id
        )
        
        # Build context from learning profile
        user_context = {
            "learning_style": learning_profile.learning_style if learning_profile else "balanced",
            "performance": {
                "accuracy": learning_profile.average_accuracy if learning_profile else 0,
                "speed": learning_profile.average_speed if learning_profile else "medium"
            },
            "preferences": learning_profile.preferences if learning_profile else {},
            "interests": getattr(current_user, 'interests', []),
            "grade_level": getattr(current_user, 'grade_level', None),
            "programming_experience": request.context.get("programming_experience", "none")
        }
        
        # Add any additional context from request
        if request.context:
            user_context.update(request.context)
        
        # Generate content
        content = await content_engine.generate_personalized_content(
            subject=request.subject,
            topic=request.topic,
            difficulty=request.difficulty,
            user_context=user_context
        )
        
        # Log content generation
        api_logger.info(
            "Content generated successfully",
            user_id=current_user.id,
            subject=request.subject,
            topic=request.topic,
            difficulty=request.difficulty
        )
        
        # Track analytics
        await analytics_service.track_content_generation(
            db=db,
            user_id=current_user.id,
            subject=request.subject,
            topic=request.topic,
            difficulty=request.difficulty
        )
        
        return ContentGenerationResponse(
            success=True,
            content=content,
            message="Content generated successfully"
        )
        
    except ValueError as e:
        api_logger.warning(
            "Invalid content generation request",
            error=str(e),
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        api_logger.error(
            "Content generation failed",
            error=str(e),
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to generate content"
        )


@router.get("/topics/{subject}")
async def get_available_topics(
    subject: str,
    difficulty: Optional[str] = Query(None, description="Filter by difficulty"),
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Get available topics for a subject.
    
    Args:
        subject: Subject name
        difficulty: Optional difficulty filter
        current_user: Authenticated user
        
    Returns:
        List of available topics
    """
    # Define available topics per subject
    topics_map = {
        "math": {
            "beginner": ["fractions", "basic_arithmetic", "shapes", "counting"],
            "intermediate": ["fractions", "algebra_basics", "geometry", "decimals", "percentages"],
            "advanced": ["algebra", "trigonometry", "calculus_intro", "statistics"]
        },
        "science": {
            "beginner": ["matter_states", "plants_animals", "weather", "simple_machines"],
            "intermediate": ["matter_states", "photosynthesis", "solar_system", "forces_motion"],
            "advanced": ["chemistry_basics", "physics_principles", "biology_systems", "earth_science"]
        },
        "language": {
            "beginner": ["alphabet", "basic_words", "simple_sentences"],
            "intermediate": ["reading_comprehension", "vocabulary", "grammar", "writing_basics"],
            "advanced": ["essay_writing", "literary_analysis", "advanced_grammar"]
        },
        "history": {
            "beginner": ["community_helpers", "holidays_traditions", "family_history"],
            "intermediate": ["ancient_civilizations", "american_history", "world_cultures"],
            "advanced": ["world_war_2", "american_revolution", "modern_history", "historical_analysis"]
        },
        "geography": {
            "beginner": ["continents_oceans", "my_community", "basic_directions"],
            "intermediate": ["countries_capitals", "climate_zones", "map_skills"],
            "advanced": ["geopolitics", "economic_geography", "environmental_systems"]
        },
        "computer_science": {
            "beginner": ["computer_basics", "internet_safety", "typing_skills"],
            "intermediate": ["programming_basics", "web_development", "digital_creativity"],
            "advanced": ["algorithms", "data_structures", "app_development"]
        },
        "art": {
            "beginner": ["color_theory", "basic_shapes", "craft_projects"],
            "intermediate": ["drawing_basics", "painting_techniques", "digital_art"],
            "advanced": ["composition", "art_history", "mixed_media"]
        }
    }
    
    if subject not in topics_map:
        raise HTTPException(
            status_code=404,
            detail=f"Subject '{subject}' not found"
        )
    
    topics = topics_map[subject]
    
    if difficulty:
        if difficulty not in topics:
            raise HTTPException(
                status_code=400,
                detail=f"Difficulty '{difficulty}' not available for subject '{subject}'"
            )
        return {
            "subject": subject,
            "difficulty": difficulty,
            "topics": topics[difficulty]
        }
    
    # Return all topics grouped by difficulty
    return {
        "subject": subject,
        "topics_by_difficulty": topics
    }


@router.get("/subjects")
async def get_available_subjects(
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Get all available subjects for content generation.
    
    Returns:
        List of available subjects with descriptions
    """
    subjects = [
        {
            "id": "math",
            "name": "Mathematics",
            "description": "Numbers, calculations, problem-solving, and logical thinking",
            "icon": "calculator",
            "color": "#3B82F6"
        },
        {
            "id": "science",
            "name": "Science",
            "description": "Natural world, experiments, and scientific thinking",
            "icon": "flask",
            "color": "#10B981"
        },
        {
            "id": "language",
            "name": "Language Arts",
            "description": "Reading, writing, grammar, and communication",
            "icon": "book-open",
            "color": "#F59E0B"
        },
        {
            "id": "history",
            "name": "History",
            "description": "Past events, civilizations, and historical thinking",
            "icon": "clock",
            "color": "#8B5CF6"
        },
        {
            "id": "geography",
            "name": "Geography",
            "description": "Earth, maps, cultures, and places",
            "icon": "globe",
            "color": "#06B6D4"
        },
        {
            "id": "computer_science",
            "name": "Computer Science",
            "description": "Programming, technology, and computational thinking",
            "icon": "code",
            "color": "#EC4899"
        },
        {
            "id": "art",
            "name": "Art",
            "description": "Creativity, visual arts, and artistic expression",
            "icon": "palette",
            "color": "#F97316"
        }
    ]
    
    return {
        "subjects": subjects,
        "total": len(subjects)
    }


@router.post("/preview")
async def preview_content(
    request: ContentGenerationRequest,
    current_user: User = Depends(deps.get_current_admin_user)
):
    """
    Preview generated content without saving (admin only).
    
    Args:
        request: Content generation parameters
        current_user: Authenticated admin user
        
    Returns:
        Generated content preview
    """
    # Use default context for preview
    preview_context = {
        "learning_style": request.context.get("learning_style", "balanced"),
        "performance": {
            "accuracy": 75,
            "speed": "medium"
        },
        "preferences": {},
        "interests": []
    }
    
    content = await content_engine.generate_personalized_content(
        subject=request.subject,
        topic=request.topic,
        difficulty=request.difficulty,
        user_context=preview_context
    )
    
    return {
        "preview": True,
        "content": content,
        "message": "This is a preview. Content not saved."
    }