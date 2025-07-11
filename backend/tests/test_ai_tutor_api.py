"""
API endpoint tests for AI Tutor
"""
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.learning_analytics import LearningProfile


class TestAITutorAPI:
    """Test AI Tutor API endpoints"""
    
    @pytest.mark.asyncio
    async def test_analyze_learning_style_endpoint(
        self, client: TestClient, normal_user_token: str, db: Session
    ):
        """Test learning style analysis endpoint"""
        with patch('app.services.ai_tutor.AITutorService.analyze_learning_style') as mock_analyze:
            mock_analyze.return_value = AsyncMock(return_value={
                "learning_style": "visual",
                "characteristics": ["prefers diagrams"],
                "recommendations": ["use visual aids"]
            })
            
            response = client.post(
                "/api/v1/ai-tutor/analyze-style",
                headers={"Authorization": f"Bearer {normal_user_token}"},
                json={
                    "session_data": [
                        {
                            "subject": "math",
                            "duration": 30,
                            "score": 85,
                            "interaction_patterns": ["viewed_diagrams"]
                        }
                    ]
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["learning_style"] == "visual"
    
    @pytest.mark.asyncio
    async def test_generate_content_endpoint(
        self, client: TestClient, normal_user_token: str, db: Session
    ):
        """Test personalized content generation endpoint"""
        with patch('app.services.ai_tutor.openai.ChatCompletion.acreate') as mock_openai:
            mock_openai.return_value = {
                "choices": [{
                    "message": {
                        "content": '''{"title": "Math Lesson",
                                      "content": "Let's learn math...",
                                      "learning_objectives": ["understand numbers"],
                                      "estimated_duration": 15}'''
                    }
                }]
            }
            
            response = client.post(
                "/api/v1/ai-tutor/generate-content",
                headers={"Authorization": f"Bearer {normal_user_token}"},
                json={
                    "subject": "math",
                    "topic": "addition",
                    "difficulty": "beginner"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "Math Lesson"
            assert data["estimated_duration"] == 15
    
    @pytest.mark.asyncio
    async def test_provide_feedback_endpoint(
        self, client: TestClient, normal_user_token: str
    ):
        """Test feedback endpoint"""
        with patch('app.services.ai_tutor.openai.ChatCompletion.acreate') as mock_openai:
            mock_openai.return_value = {
                "choices": [{
                    "message": {
                        "content": '''{"is_correct": true,
                                      "feedback": "Great job!",
                                      "hints": [],
                                      "next_steps": ["Try harder problems"]}'''
                    }
                }]
            }
            
            response = client.post(
                "/api/v1/ai-tutor/feedback",
                headers={"Authorization": f"Bearer {normal_user_token}"},
                json={
                    "question": "What is 2 + 2?",
                    "user_answer": "4",
                    "correct_answer": "4",
                    "subject": "math",
                    "topic": "addition"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["is_correct"] is True
            assert "Great" in data["feedback"]
    
    @pytest.mark.asyncio
    async def test_generate_practice_questions_endpoint(
        self, client: TestClient, normal_user_token: str
    ):
        """Test practice question generation endpoint"""
        with patch('app.services.ai_tutor.openai.ChatCompletion.acreate') as mock_openai:
            mock_openai.return_value = {
                "choices": [{
                    "message": {
                        "content": '''{"questions": [
                            {"id": "q1", "question": "What is 5 + 3?", 
                             "type": "short_answer", "correct_answer": "8"}
                        ]}'''
                    }
                }]
            }
            
            response = client.post(
                "/api/v1/ai-tutor/practice-questions",
                headers={"Authorization": f"Bearer {normal_user_token}"},
                json={
                    "subject": "math",
                    "topic": "addition",
                    "difficulty": "easy",
                    "count": 1
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["questions"]) == 1
            assert data["questions"][0]["correct_answer"] == "8"
    
    @pytest.mark.asyncio
    async def test_create_learning_path_endpoint(
        self, client: TestClient, normal_user_token: str
    ):
        """Test learning path creation endpoint"""
        with patch('app.services.ai_tutor.openai.ChatCompletion.acreate') as mock_openai:
            mock_openai.return_value = {
                "choices": [{
                    "message": {
                        "content": '''{"goal": "Master Math",
                                      "duration_weeks": 4,
                                      "milestones": [
                                          {"week": 1, "title": "Basics", "topics": ["numbers"]}
                                      ]}'''
                    }
                }]
            }
            
            response = client.post(
                "/api/v1/ai-tutor/learning-path",
                headers={"Authorization": f"Bearer {normal_user_token}"},
                json={
                    "subject": "math",
                    "goal": "Master Math",
                    "current_level": "beginner",
                    "available_time_per_week": 5
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["goal"] == "Master Math"
            assert data["duration_weeks"] == 4
    
    @pytest.mark.asyncio
    async def test_explain_concept_endpoint(
        self, client: TestClient, normal_user_token: str
    ):
        """Test concept explanation endpoint"""
        with patch('app.services.ai_tutor.openai.ChatCompletion.acreate') as mock_openai:
            mock_openai.return_value = {
                "choices": [{
                    "message": {
                        "content": '''{"concept": "Addition",
                                      "explanation": "Addition is combining numbers...",
                                      "examples": ["2+2=4"],
                                      "analogies": ["Like putting apples together"]}'''
                    }
                }]
            }
            
            response = client.post(
                "/api/v1/ai-tutor/explain",
                headers={"Authorization": f"Bearer {normal_user_token}"},
                json={
                    "concept": "addition",
                    "subject": "math",
                    "detail_level": "beginner"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["concept"] == "Addition"
            assert "combining" in data["explanation"]
    
    @pytest.mark.asyncio
    async def test_provide_hint_endpoint(
        self, client: TestClient, normal_user_token: str
    ):
        """Test hint provision endpoint"""
        with patch('app.services.ai_tutor.openai.ChatCompletion.acreate') as mock_openai:
            mock_openai.return_value = {
                "choices": [{
                    "message": {
                        "content": '''{"hints": [
                            {"level": 1, "hint": "Think about counting"}
                        ],
                        "next_hint_available": true}'''
                    }
                }]
            }
            
            response = client.post(
                "/api/v1/ai-tutor/hint",
                headers={"Authorization": f"Bearer {normal_user_token}"},
                json={
                    "question": "What is 3 + 4?",
                    "current_answer": "6",
                    "hint_level": 1,
                    "subject": "math",
                    "topic": "addition"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["hints"]) >= 1
            assert data["next_hint_available"] is True
    
    @pytest.mark.asyncio
    async def test_chat_with_tutor_endpoint(
        self, client: TestClient, normal_user_token: str, db: Session
    ):
        """Test AI tutor chat endpoint"""
        with patch('app.services.ai_tutor.openai.ChatCompletion.acreate') as mock_openai:
            mock_openai.return_value = {
                "choices": [{
                    "message": {
                        "content": "I'd be happy to help you understand fractions!"
                    }
                }]
            }
            
            response = client.post(
                "/api/v1/ai-tutor/chat",
                headers={"Authorization": f"Bearer {normal_user_token}"},
                json={
                    "message": "Can you help me with fractions?",
                    "context": {"subject": "math"}
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "help" in data["response"]
            assert data["session_id"] is not None
    
    def test_unauthorized_access(self, client: TestClient):
        """Test that endpoints require authentication"""
        response = client.post(
            "/api/v1/ai-tutor/generate-content",
            json={
                "subject": "math",
                "topic": "addition",
                "difficulty": "beginner"
            }
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_rate_limiting(
        self, client: TestClient, normal_user_token: str
    ):
        """Test API rate limiting"""
        # This would test rate limiting if implemented
        # For now, just verify endpoints work
        with patch('app.services.ai_tutor.openai.ChatCompletion.acreate') as mock_openai:
            mock_openai.return_value = {
                "choices": [{
                    "message": {"content": '{"response": "test"}'}
                }]
            }
            
            # Make multiple requests
            for _ in range(5):
                response = client.post(
                    "/api/v1/ai-tutor/chat",
                    headers={"Authorization": f"Bearer {normal_user_token}"},
                    json={"message": "test"}
                )
                assert response.status_code == 200


class TestAITutorErrorHandling:
    """Test error handling in AI Tutor API"""
    
    @pytest.mark.asyncio
    async def test_invalid_subject_error(
        self, client: TestClient, normal_user_token: str
    ):
        """Test handling of invalid subject"""
        response = client.post(
            "/api/v1/ai-tutor/generate-content",
            headers={"Authorization": f"Bearer {normal_user_token}"},
            json={
                "subject": "invalid_subject",
                "topic": "test",
                "difficulty": "beginner"
            }
        )
        
        assert response.status_code == 400
        assert "error" in response.json()
    
    @pytest.mark.asyncio
    async def test_openai_service_error(
        self, client: TestClient, normal_user_token: str
    ):
        """Test handling of OpenAI service errors"""
        with patch('app.services.ai_tutor.openai.ChatCompletion.acreate') as mock_openai:
            mock_openai.side_effect = Exception("OpenAI service unavailable")
            
            response = client.post(
                "/api/v1/ai-tutor/generate-content",
                headers={"Authorization": f"Bearer {normal_user_token}"},
                json={
                    "subject": "math",
                    "topic": "addition",
                    "difficulty": "beginner"
                }
            )
            
            assert response.status_code == 503
            data = response.json()
            assert data["error"]["category"] == "server"