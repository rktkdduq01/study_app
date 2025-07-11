from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.learning_analytics import LearningSession
from app.services.ai_tutor import ai_tutor_service
from app.websocket.manager import websocket_manager
from app.schemas.user import User as UserSchema

router = APIRouter()


# Request/Response Models
class ContentGenerationRequest(BaseModel):
    subject: str
    topic: str
    difficulty_level: int = 5
    content_type: str = "lesson"


class FeedbackRequest(BaseModel):
    question: str
    user_answer: str
    correct_answer: str
    subject: str


class PracticeQuestionsRequest(BaseModel):
    subject: str
    topic: str
    count: int = 5


class LearningPathRequest(BaseModel):
    goal: str
    timeline_days: int = 30


class ConceptExplanationRequest(BaseModel):
    concept: str
    user_level: str = "intermediate"
    learning_style: str = "balanced"
    examples_count: int = 3


class HintRequest(BaseModel):
    question: str
    user_attempts: List[str]
    hint_level: int = 1


class ChatRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = {}
    session_id: Optional[int] = None


@router.post("/analyze-style")
async def analyze_learning_style(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze user's learning style using AI
    """
    try:
        analysis = await ai_tutor_service.analyze_learning_style(current_user, db)
        return {
            "success": True,
            "analysis": analysis,
            "user_id": current_user.id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-content")
async def generate_personalized_content(
    request: ContentGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate personalized learning content based on user's profile
    """
    try:
        content = await ai_tutor_service.generate_personalized_content(
            user=current_user,
            subject=request.subject,
            topic=request.topic,
            difficulty_level=request.difficulty_level,
            db=db
        )
        
        # Send real-time update via WebSocket
        await websocket_manager.send_to_user(
            str(current_user.id),
            {
                "type": "content_generated",
                "content": content
            }
        )
        
        return {
            "success": True,
            "content": content,
            "user_id": current_user.id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback")
async def provide_real_time_feedback(
    request: FeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Provide real-time AI feedback on user's answer
    """
    try:
        feedback = await ai_tutor_service.provide_real_time_feedback(
            user=current_user,
            question=request.question,
            user_answer=request.user_answer,
            correct_answer=request.correct_answer,
            subject=request.subject,
            db=db
        )
        
        # Send feedback via WebSocket for real-time updates
        await websocket_manager.send_to_user(
            str(current_user.id),
            {
                "type": "ai_feedback",
                "feedback": feedback
            }
        )
        
        return {
            "success": True,
            "feedback": feedback,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/practice-questions")
async def generate_practice_questions(
    request: PracticeQuestionsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate practice questions based on user's level
    """
    try:
        questions = await ai_tutor_service.generate_practice_questions(
            user=current_user,
            subject=request.subject,
            topic=request.topic,
            count=request.count,
            db=db
        )
        
        return {
            "success": True,
            "questions": questions,
            "count": len(questions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/learning-path")
async def create_learning_path(
    request: LearningPathRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create personalized learning path
    """
    try:
        learning_path = await ai_tutor_service.create_learning_path(
            user=current_user,
            goal=request.goal,
            timeline_days=request.timeline_days,
            db=db
        )
        
        return {
            "success": True,
            "learning_path": learning_path,
            "user_id": current_user.id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/explain")
async def explain_concept(
    request: ConceptExplanationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generate AI explanation for a concept
    """
    try:
        explanation = await ai_tutor_service.generate_explanation(
            concept=request.concept,
            user_level=request.user_level,
            learning_style=request.learning_style,
            examples_count=request.examples_count
        )
        
        return {
            "success": True,
            "explanation": explanation
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/hint")
async def provide_hint(
    request: HintRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Provide progressive hints for a question
    """
    try:
        hint = await ai_tutor_service.provide_hint(
            question=request.question,
            user_attempts=request.user_attempts,
            hint_level=request.hint_level
        )
        
        return {
            "success": True,
            "hint": hint
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat")
async def ai_tutor_chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Chat with AI tutor for questions and explanations
    """
    try:
        # Simple response for now - can be enhanced with actual AI chat
        response = {
            "user_message": request.message,
            "ai_response": "I'm here to help you learn! Let me assist you with that.",
            "suggestions": [
                "Would you like me to explain this concept?",
                "Should we practice with some problems?",
                "Do you want to see some examples?"
            ],
            "context_updated": True
        }
        
        # Send via WebSocket for real-time chat
        await websocket_manager.send_to_user(
            str(current_user.id),
            {
                "type": "ai_chat_response",
                "response": response
            }
        )
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}/summary")
async def get_session_summary(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get AI-generated summary of a learning session
    """
    # Get session
    session = db.query(LearningSession).filter(
        LearningSession.id == session_id,
        LearningSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Generate summary
    summary = {
        "session_id": session_id,
        "duration_minutes": session.duration_seconds // 60 if session.duration_seconds else 0,
        "topics_covered": [session.topic],
        "accuracy": session.accuracy_rate if session.accuracy_rate else 0,
        "strengths": ["Good understanding of basics", "Quick response time"],
        "areas_to_improve": ["Practice more complex problems", "Review advanced concepts"],
        "next_recommendations": [
            {
                "topic": f"Advanced {session.topic}",
                "reason": "Build on current knowledge",
                "difficulty": session.difficulty_level + 1 if session.difficulty_level < 10 else 10
            }
        ]
    }
    
    return summary