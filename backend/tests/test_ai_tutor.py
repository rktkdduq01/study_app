"""
Comprehensive unit tests for AI Tutor functionality
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from typing import Dict, List, Any

from sqlalchemy.orm import Session
from app.services.ai_tutor import AITutorService
from app.models.user import User
from app.models.learning_analytics import LearningProfile, LearningSession, SessionAnalytics
from app.models.ai_tutor import PersonalizedContent, ContentEffectiveness
from app.schemas.ai_tutor import (
    LearningStyleAnalysis,
    PersonalizedContentRequest,
    FeedbackRequest,
    PracticeQuestionRequest,
    LearningPathRequest,
    ExplainRequest,
    HintRequest,
    ChatMessage
)


@pytest.fixture
def ai_tutor_service():
    """Create AI tutor service instance"""
    return AITutorService()


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response"""
    return {
        "choices": [{
            "message": {
                "content": "Mocked AI response"
            }
        }]
    }


@pytest.fixture
def sample_user(db: Session):
    """Create a sample user with learning profile"""
    user = User(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        level=5,
        age=15
    )
    db.add(user)
    db.commit()
    
    # Create learning profile
    profile = LearningProfile(
        user_id=user.id,
        learning_style="visual",
        preferred_difficulty="intermediate",
        interests=["science", "technology"],
        strengths=["problem_solving"],
        weaknesses=["memorization"],
        average_session_duration=30,
        best_time_to_learn="morning",
        average_accuracy=75.0,
        average_speed="medium"
    )
    db.add(profile)
    db.commit()
    
    return user


class TestAITutorService:
    """Test AI Tutor service methods"""
    
    @pytest.mark.asyncio
    async def test_analyze_learning_style(self, ai_tutor_service, sample_user, db):
        """Test learning style analysis"""
        with patch('app.services.ai_tutor.openai') as mock_openai:
            # Mock OpenAI response
            mock_openai.ChatCompletion.acreate = AsyncMock(return_value={
                "choices": [{
                    "message": {
                        "content": '''{"learning_style": "visual", 
                                      "characteristics": ["prefers diagrams", "uses color coding"],
                                      "recommendations": ["use mind maps", "watch video tutorials"]}'''
                    }
                }]
            })
            
            # Create session data
            sessions = [
                {
                    "subject": "math",
                    "duration": 30,
                    "score": 85,
                    "interaction_patterns": ["viewed_diagrams", "used_visual_aids"]
                },
                {
                    "subject": "science", 
                    "duration": 25,
                    "score": 90,
                    "interaction_patterns": ["watched_animations", "drew_diagrams"]
                }
            ]
            
            result = await ai_tutor_service.analyze_learning_style(
                user_id=sample_user.id,
                session_data=sessions,
                db=db
            )
            
            assert result.learning_style == "visual"
            assert len(result.characteristics) == 2
            assert len(result.recommendations) == 2
            assert "diagrams" in result.characteristics[0]
    
    @pytest.mark.asyncio
    async def test_generate_personalized_content(self, ai_tutor_service, sample_user, db):
        """Test personalized content generation"""
        with patch('app.services.ai_tutor.openai') as mock_openai:
            # Mock OpenAI response for content generation
            mock_openai.ChatCompletion.acreate = AsyncMock(return_value={
                "choices": [{
                    "message": {
                        "content": '''{"title": "Understanding Fractions Visually",
                                      "content": "Let's explore fractions using visual representations...",
                                      "learning_objectives": ["understand parts of a whole", "compare fractions"],
                                      "estimated_duration": 15,
                                      "interactive_elements": ["fraction bars", "pie charts"],
                                      "practice_problems": [
                                          {"question": "What is 1/2 of 8?", "answer": "4", "explanation": "Half of 8 is 4"}
                                      ]}'''
                    }
                }]
            })
            
            request = PersonalizedContentRequest(
                subject="math",
                topic="fractions",
                difficulty="beginner"
            )
            
            result = await ai_tutor_service.generate_personalized_content(
                user_id=sample_user.id,
                request=request,
                db=db
            )
            
            assert result.title == "Understanding Fractions Visually"
            assert "visual" in result.content.lower()
            assert len(result.learning_objectives) == 2
            assert result.estimated_duration == 15
            assert len(result.practice_problems) == 1
            
            # Check if content was saved to database
            saved_content = db.query(PersonalizedContent).filter(
                PersonalizedContent.user_id == sample_user.id
            ).first()
            assert saved_content is not None
            assert saved_content.subject == "math"
            assert saved_content.topic == "fractions"
    
    @pytest.mark.asyncio
    async def test_provide_feedback(self, ai_tutor_service, sample_user, db):
        """Test AI feedback generation"""
        with patch('app.services.ai_tutor.openai') as mock_openai:
            # Mock OpenAI response for feedback
            mock_openai.ChatCompletion.acreate = AsyncMock(return_value={
                "choices": [{
                    "message": {
                        "content": '''{"is_correct": false,
                                      "feedback": "Good attempt! You're close. Remember that 2+2=4, not 5.",
                                      "hints": ["Count on your fingers", "Think of 2 apples plus 2 more apples"],
                                      "next_steps": ["Practice more addition", "Try problems with smaller numbers"],
                                      "confidence_score": 0.7,
                                      "misconceptions": ["confusion with counting"]}'''
                    }
                }]
            })
            
            request = FeedbackRequest(
                question="What is 2 + 2?",
                user_answer="5",
                correct_answer="4",
                subject="math",
                topic="addition"
            )
            
            result = await ai_tutor_service.provide_feedback(
                user_id=sample_user.id,
                request=request,
                db=db
            )
            
            assert result.is_correct is False
            assert "close" in result.feedback.lower()
            assert len(result.hints) == 2
            assert len(result.next_steps) == 2
            assert result.confidence_score == 0.7
            assert len(result.misconceptions) == 1
    
    @pytest.mark.asyncio
    async def test_generate_practice_questions(self, ai_tutor_service, sample_user, db):
        """Test practice question generation"""
        with patch('app.services.ai_tutor.openai') as mock_openai:
            # Mock OpenAI response for questions
            mock_openai.ChatCompletion.acreate = AsyncMock(return_value={
                "choices": [{
                    "message": {
                        "content": '''{"questions": [
                            {
                                "id": "q1",
                                "question": "If you have 3 apples and get 2 more, how many do you have?",
                                "type": "multiple_choice",
                                "options": ["4", "5", "6", "7"],
                                "correct_answer": "5",
                                "explanation": "3 + 2 = 5",
                                "difficulty": "easy",
                                "estimated_time": 30,
                                "hints": ["Count the total apples"]
                            },
                            {
                                "id": "q2",
                                "question": "What is 7 - 3?",
                                "type": "short_answer",
                                "correct_answer": "4",
                                "explanation": "When you take away 3 from 7, you have 4 left",
                                "difficulty": "easy",
                                "estimated_time": 30
                            }
                        ]}'''
                    }
                }]
            })
            
            request = PracticeQuestionRequest(
                subject="math",
                topic="basic_arithmetic",
                difficulty="easy",
                count=2,
                question_types=["multiple_choice", "short_answer"]
            )
            
            result = await ai_tutor_service.generate_practice_questions(
                user_id=sample_user.id,
                request=request,
                db=db
            )
            
            assert len(result.questions) == 2
            assert result.questions[0].type == "multiple_choice"
            assert len(result.questions[0].options) == 4
            assert result.questions[0].difficulty == "easy"
            assert result.questions[1].type == "short_answer"
    
    @pytest.mark.asyncio
    async def test_create_learning_path(self, ai_tutor_service, sample_user, db):
        """Test learning path creation"""
        with patch('app.services.ai_tutor.openai') as mock_openai:
            # Mock OpenAI response for learning path
            mock_openai.ChatCompletion.acreate = AsyncMock(return_value={
                "choices": [{
                    "message": {
                        "content": '''{"goal": "Master Basic Algebra",
                                      "duration_weeks": 4,
                                      "milestones": [
                                          {
                                              "week": 1,
                                              "title": "Understanding Variables",
                                              "topics": ["what are variables", "simple equations"],
                                              "practice_hours": 3,
                                              "assessments": ["variables quiz"]
                                          },
                                          {
                                              "week": 2,
                                              "title": "Solving Equations",
                                              "topics": ["one-step equations", "two-step equations"],
                                              "practice_hours": 4,
                                              "assessments": ["equation solving test"]
                                          }
                                      ],
                                      "prerequisites": ["basic arithmetic"],
                                      "resources": ["Khan Academy Algebra", "Practice workbook"],
                                      "success_criteria": ["Solve linear equations", "Understand variable manipulation"]}'''
                    }
                }]
            })
            
            request = LearningPathRequest(
                subject="math",
                goal="Master Basic Algebra",
                current_level="beginner",
                available_time_per_week=5,
                target_date="2024-02-01"
            )
            
            result = await ai_tutor_service.create_learning_path(
                user_id=sample_user.id,
                request=request,
                db=db
            )
            
            assert result.goal == "Master Basic Algebra"
            assert result.duration_weeks == 4
            assert len(result.milestones) == 2
            assert result.milestones[0].week == 1
            assert "Variables" in result.milestones[0].title
            assert len(result.prerequisites) == 1
            assert len(result.resources) == 2
    
    @pytest.mark.asyncio
    async def test_explain_concept(self, ai_tutor_service, sample_user, db):
        """Test concept explanation generation"""
        with patch('app.services.ai_tutor.openai') as mock_openai:
            # Mock OpenAI response for explanation
            mock_openai.ChatCompletion.acreate = AsyncMock(return_value={
                "choices": [{
                    "message": {
                        "content": '''{"concept": "Photosynthesis",
                                      "explanation": "Photosynthesis is how plants make their own food using sunlight...",
                                      "examples": [
                                          "A tree using sunlight to grow",
                                          "Grass turning green in spring"
                                      ],
                                      "analogies": [
                                          "Like a solar panel converting sunlight to energy",
                                          "Like a kitchen where ingredients become food"
                                      ],
                                      "visual_aids": ["diagram of chloroplast", "animation of process"],
                                      "related_concepts": ["cellular respiration", "chlorophyll"],
                                      "difficulty_level": "intermediate"}'''
                    }
                }]
            })
            
            request = ExplainRequest(
                concept="photosynthesis",
                subject="science",
                detail_level="intermediate",
                include_examples=True,
                include_visuals=True
            )
            
            result = await ai_tutor_service.explain_concept(
                user_id=sample_user.id,
                request=request,
                db=db
            )
            
            assert result.concept == "Photosynthesis"
            assert "plants" in result.explanation.lower()
            assert len(result.examples) == 2
            assert len(result.analogies) == 2
            assert len(result.visual_aids) == 2
            assert "solar panel" in result.analogies[0]
    
    @pytest.mark.asyncio
    async def test_provide_hint(self, ai_tutor_service, sample_user, db):
        """Test progressive hint generation"""
        with patch('app.services.ai_tutor.openai') as mock_openai:
            # Mock OpenAI response for hints
            mock_openai.ChatCompletion.acreate = AsyncMock(return_value={
                "choices": [{
                    "message": {
                        "content": '''{"hints": [
                            {"level": 1, "hint": "Think about what operation combines numbers"},
                            {"level": 2, "hint": "You need to add the two numbers together"},
                            {"level": 3, "hint": "Calculate 3 + 4 by counting: 3, 4, 5, 6, 7"}
                        ],
                        "next_hint_available": true,
                        "explanation_unlocked": false}'''
                    }
                }]
            })
            
            request = HintRequest(
                question="What is 3 + 4?",
                current_answer="6",
                hint_level=1,
                subject="math",
                topic="addition"
            )
            
            result = await ai_tutor_service.provide_hint(
                user_id=sample_user.id,
                request=request,
                db=db
            )
            
            assert len(result.hints) == 3
            assert result.hints[0].level == 1
            assert "operation" in result.hints[0].hint
            assert result.next_hint_available is True
            assert result.explanation_unlocked is False
    
    @pytest.mark.asyncio
    async def test_chat_interaction(self, ai_tutor_service, sample_user, db):
        """Test AI tutor chat functionality"""
        # Create a session first
        session = LearningSession(
            user_id=sample_user.id,
            subject="math",
            topic="fractions",
            start_time=datetime.utcnow()
        )
        db.add(session)
        db.commit()
        
        with patch('app.services.ai_tutor.openai') as mock_openai:
            # Mock OpenAI response for chat
            mock_openai.ChatCompletion.acreate = AsyncMock(return_value={
                "choices": [{
                    "message": {
                        "content": "Great question! Let me explain fractions using pizza slices..."
                    }
                }]
            })
            
            message = ChatMessage(
                message="I don't understand fractions. Can you help?",
                session_id=session.id,
                context={
                    "current_topic": "fractions",
                    "difficulty": "beginner"
                }
            )
            
            result = await ai_tutor_service.chat(
                user_id=sample_user.id,
                message=message,
                db=db
            )
            
            assert "pizza" in result.response.lower()
            assert result.session_id == session.id
            # Message should be saved in context
            assert len(result.context["chat_history"]) > 0
    
    def test_calculate_content_effectiveness(self, ai_tutor_service, sample_user, db):
        """Test content effectiveness calculation"""
        # Create content and interactions
        content = PersonalizedContent(
            user_id=sample_user.id,
            subject="math",
            topic="fractions",
            difficulty="beginner",
            content_type="lesson",
            content_data={
                "title": "Understanding Fractions",
                "estimated_duration": 15
            }
        )
        db.add(content)
        db.commit()
        
        # Add effectiveness data
        effectiveness = ContentEffectiveness(
            content_id=content.id,
            user_id=sample_user.id,
            time_spent=20,
            score=85,
            engagement_score=0.9,
            completion_rate=1.0,
            user_rating=4,
            led_to_improvement=True
        )
        db.add(effectiveness)
        db.commit()
        
        # Calculate effectiveness
        result = ai_tutor_service._calculate_content_effectiveness(content.id, db)
        
        assert result["average_score"] == 85
        assert result["average_engagement"] == 0.9
        assert result["completion_rate"] == 1.0
        assert result["effectiveness_score"] > 0.8  # High effectiveness
    
    def test_update_learning_profile(self, ai_tutor_service, sample_user, db):
        """Test learning profile updates"""
        # Get existing profile
        profile = db.query(LearningProfile).filter(
            LearningProfile.user_id == sample_user.id
        ).first()
        
        # Create session analytics
        analytics = SessionAnalytics(
            session_id=1,
            total_time=35,
            questions_attempted=10,
            questions_correct=8,
            average_response_time=3.5,
            hints_used=2,
            score=80,
            engagement_score=0.85,
            topics_covered=["fractions", "decimals"],
            weak_areas=["decimal_conversion"],
            strong_areas=["basic_fractions"],
            learning_pace="steady"
        )
        
        # Update profile
        ai_tutor_service._update_learning_profile(sample_user.id, analytics, db)
        
        # Verify updates
        updated_profile = db.query(LearningProfile).filter(
            LearningProfile.user_id == sample_user.id
        ).first()
        
        assert updated_profile.average_accuracy == 80.0  # Updated from analytics
        assert "decimal_conversion" in updated_profile.weaknesses
        assert updated_profile.average_session_duration > 30  # Increased from 30


class TestAITutorErrorHandling:
    """Test error handling in AI Tutor"""
    
    @pytest.mark.asyncio
    async def test_openai_api_error_handling(self, ai_tutor_service, sample_user, db):
        """Test handling of OpenAI API errors"""
        with patch('app.services.ai_tutor.openai') as mock_openai:
            # Mock API error
            mock_openai.ChatCompletion.acreate = AsyncMock(
                side_effect=Exception("OpenAI API Error")
            )
            
            request = ExplainRequest(
                concept="test",
                subject="math"
            )
            
            with pytest.raises(Exception) as exc_info:
                await ai_tutor_service.explain_concept(
                    user_id=sample_user.id,
                    request=request,
                    db=db
                )
            
            assert "External service error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_invalid_json_response_handling(self, ai_tutor_service, sample_user, db):
        """Test handling of invalid JSON in AI response"""
        with patch('app.services.ai_tutor.openai') as mock_openai:
            # Mock invalid JSON response
            mock_openai.ChatCompletion.acreate = AsyncMock(return_value={
                "choices": [{
                    "message": {
                        "content": "This is not valid JSON"
                    }
                }]
            })
            
            request = PersonalizedContentRequest(
                subject="math",
                topic="test"
            )
            
            # Should handle gracefully and return default structure
            result = await ai_tutor_service.generate_personalized_content(
                user_id=sample_user.id,
                request=request,
                db=db
            )
            
            # Should have some default content
            assert result is not None
            assert hasattr(result, 'title')


class TestAITutorCaching:
    """Test caching functionality"""
    
    @pytest.mark.asyncio
    async def test_content_caching(self, ai_tutor_service, sample_user, db):
        """Test that similar content requests use cache"""
        with patch('app.services.ai_tutor.openai') as mock_openai:
            mock_openai.ChatCompletion.acreate = AsyncMock(return_value={
                "choices": [{
                    "message": {
                        "content": '''{"title": "Cached Content", "content": "This is cached"}'''
                    }
                }]
            })
            
            request = PersonalizedContentRequest(
                subject="math",
                topic="fractions",
                difficulty="beginner"
            )
            
            # First request
            result1 = await ai_tutor_service.generate_personalized_content(
                user_id=sample_user.id,
                request=request,
                db=db
            )
            
            # Second identical request (should use cache)
            result2 = await ai_tutor_service.generate_personalized_content(
                user_id=sample_user.id,
                request=request,
                db=db
            )
            
            # Should have called API only once
            assert mock_openai.ChatCompletion.acreate.call_count == 1
            assert result1.title == result2.title


class TestAITutorIntegration:
    """Integration tests for AI Tutor"""
    
    @pytest.mark.asyncio
    async def test_complete_learning_session_flow(self, ai_tutor_service, sample_user, db):
        """Test complete learning session from start to finish"""
        with patch('app.services.ai_tutor.openai') as mock_openai:
            # Mock all AI responses
            mock_openai.ChatCompletion.acreate = AsyncMock(side_effect=[
                # Content generation response
                {
                    "choices": [{
                        "message": {
                            "content": '''{"title": "Learning Fractions", 
                                          "content": "Let's learn about fractions...",
                                          "practice_problems": [
                                              {"question": "What is 1/2 of 4?", "answer": "2"}
                                          ]}'''
                        }
                    }]
                },
                # Feedback response
                {
                    "choices": [{
                        "message": {
                            "content": '''{"is_correct": true,
                                          "feedback": "Excellent work!",
                                          "next_steps": ["Try harder problems"]}'''
                        }
                    }]
                },
                # Session summary response
                {
                    "choices": [{
                        "message": {
                            "content": '''{"summary": "Great session! You mastered basic fractions.",
                                          "achievements": ["First perfect score"],
                                          "recommendations": ["Move to advanced fractions"]}'''
                        }
                    }]
                }
            ])
            
            # 1. Generate content
            content_request = PersonalizedContentRequest(
                subject="math",
                topic="fractions"
            )
            content = await ai_tutor_service.generate_personalized_content(
                user_id=sample_user.id,
                request=content_request,
                db=db
            )
            
            # 2. Answer practice question
            feedback_request = FeedbackRequest(
                question="What is 1/2 of 4?",
                user_answer="2",
                correct_answer="2",
                subject="math",
                topic="fractions"
            )
            feedback = await ai_tutor_service.provide_feedback(
                user_id=sample_user.id,
                request=feedback_request,
                db=db
            )
            
            assert feedback.is_correct is True
            assert "Excellent" in feedback.feedback
            
            # 3. Complete session
            session = db.query(LearningSession).filter(
                LearningSession.user_id == sample_user.id
            ).first()
            
            if session:
                session.end_time = datetime.utcnow()
                db.commit()
            
            # Verify learning profile was updated
            profile = db.query(LearningProfile).filter(
                LearningProfile.user_id == sample_user.id
            ).first()
            assert profile is not None