"""
User Analytics Service for AI Tutor
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
import json

from app.models.user import User
from app.models.learning_analytics import LearningSession
from app.models.gamification import UserProgress, UserAchievement
from app.core.redis_client import redis_client
from app.core.logger import get_logger

logger = get_logger(__name__)


class UserAnalyticsService:
    """Service for analyzing user learning data"""
    
    async def get_user_performance(self, user_id: int, subject: str) -> Dict[str, Any]:
        """Get user's performance metrics for a subject"""
        # Get from cache first
        cache_key = f"user_performance:{user_id}:{subject}"
        cached = await redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
        
        # Mock data for now - in production, query from database
        performance = {
            "accuracy": 75.5,
            "total_sessions": 24,
            "total_time_hours": 12.5,
            "average_session_duration": 31,
            "topics_mastered": 8,
            "current_streak": 5,
            "improvement_rate": 12.3
        }
        
        # Cache for 1 hour
        await redis_client.setex(cache_key, 3600, json.dumps(performance))
        
        return performance
    
    async def get_detailed_performance(self, user_id: int, subject: str) -> Dict[str, Any]:
        """Get detailed performance breakdown by topics"""
        # Mock implementation
        return {
            "subject": subject,
            "topics": {
                "algebra": {"accuracy": 82, "sessions": 10, "mastery": 0.8},
                "geometry": {"accuracy": 68, "sessions": 8, "mastery": 0.6},
                "trigonometry": {"accuracy": 71, "sessions": 6, "mastery": 0.65}
            },
            "weak_areas": ["geometry", "complex equations"],
            "strong_areas": ["algebra", "basic operations"]
        }
    
    async def get_overall_performance(self, user_id: int) -> Dict[str, Any]:
        """Get overall performance across all subjects"""
        # Mock implementation
        return {
            "subjects": {
                "mathematics": {
                    "accuracy": 75,
                    "topics": ["algebra", "geometry", "trigonometry"],
                    "level": "intermediate"
                },
                "science": {
                    "accuracy": 82,
                    "topics": ["physics", "chemistry"],
                    "level": "advanced"
                },
                "english": {
                    "accuracy": 78,
                    "topics": ["grammar", "vocabulary", "writing"],
                    "level": "intermediate"
                }
            },
            "overall_accuracy": 78.3,
            "total_learning_hours": 45.5,
            "subjects_studied": 3
        }
    
    def get_learning_trends(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get learning trends over time"""
        # Mock implementation
        return {
            "daily_average_minutes": 45,
            "peak_learning_time": "evening",
            "consistency_score": 0.85,
            "trend": "improving",
            "sessions_per_week": 5.2
        }
    
    async def track_learning_event(
        self,
        user_id: int,
        event_type: str,
        event_data: Dict[str, Any]
    ):
        """Track a learning event for analytics"""
        event = {
            "user_id": user_id,
            "type": event_type,
            "data": event_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Store in Redis for real-time analytics
        key = f"learning_events:{user_id}:{datetime.utcnow().strftime('%Y%m%d')}"
        await redis_client.lpush(key, json.dumps(event))
        await redis_client.expire(key, 86400 * 7)  # Keep for 7 days
        
        logger.info(f"Tracked learning event: {event_type} for user {user_id}")