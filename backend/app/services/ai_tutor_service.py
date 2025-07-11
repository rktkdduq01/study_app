from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import numpy as np
from dataclasses import dataclass
import json

from app.models.learning_analytics import (
    LearningSession, SessionAnalytics, LearningProfile,
    ContentEffectiveness, PersonalizedContent
)
from app.models.user import User
from app.models.quest import Quest, QuestProgress
from app.core.exceptions import APIException


@dataclass
class LearningAnalysis:
    """Data class for learning analysis results"""
    strengths: List[Dict[str, Any]]
    weaknesses: List[Dict[str, Any]]
    learning_style: str
    recommendations: List[Dict[str, Any]]
    progress_summary: Dict[str, Any]


@dataclass
class ContentRecommendation:
    """Data class for content recommendations"""
    content_id: str
    content_type: str
    subject: str
    topic: str
    difficulty: str
    relevance_score: float
    reason: str


class AITutorService:
    """Service for AI-powered tutoring and personalized learning"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def analyze_learning_patterns(self, user_id: int) -> LearningAnalysis:
        """
        Analyze user's learning patterns using AI to provide personalized insights.
        
        Analysis Process:
        1. Collect 30 days of learning session data
        2. Analyze performance metrics by subject
        3. Identify dominant learning style (visual, auditory, kinesthetic, reading/writing)
        4. Calculate strengths/weaknesses based on success rates and time efficiency
        5. Generate AI-powered recommendations for improvement
        6. Create comprehensive progress summary
        
        The analysis considers:
        - Accuracy rates per subject/topic
        - Time spent vs. average completion times
        - Question difficulty progression
        - Mistake patterns and recovery rates
        - Engagement metrics (hints used, retries, etc.)
        
        Args:
            user_id: ID of user to analyze
            
        Returns:
            LearningAnalysis with actionable insights and recommendations
        """
        # Get recent learning sessions (30-day window for meaningful patterns)
        recent_sessions = self.db.query(LearningSession).filter(
            LearningSession.user_id == user_id,
            LearningSession.start_time >= datetime.utcnow() - timedelta(days=30)
        ).all()
        
        if not recent_sessions:
            # Return default analysis for new users
            return self._create_default_analysis()
        
        # Analyze performance by subject - calculates accuracy, speed, consistency
        subject_performance = self._analyze_subject_performance(recent_sessions)
        
        # Identify learning style based on interaction patterns
        # Uses click patterns, resource preferences, and success rates
        learning_style = self._identify_learning_style(recent_sessions)
        
        # Find strengths (>80% success rate with consistent performance)
        strengths = self._identify_strengths(subject_performance)
        
        # Find weaknesses (<60% success rate or high time-to-complete)
        weaknesses = self._identify_weaknesses(subject_performance)
        
        # Generate AI recommendations based on pattern analysis
        # Considers learning style, current level, and goal alignment
        recommendations = await self._generate_recommendations(
            user_id, strengths, weaknesses, learning_style
        )
        
        # Create progress summary with trend analysis
        progress_summary = self._create_progress_summary(recent_sessions)
        
        return LearningAnalysis(
            strengths=strengths,
            weaknesses=weaknesses,
            learning_style=learning_style,
            recommendations=recommendations,
            progress_summary=progress_summary
        )
    
    async def generate_personalized_content(
        self,
        user_id: int,
        subject: str,
        topic: str,
        content_type: str = "explanation"
    ) -> Dict[str, Any]:
        """
        Generate AI-powered personalized learning content tailored to user's needs.
        
        Content Personalization Strategy:
        1. Analyze user's learning profile (style, pace, preferences)
        2. Assess current skill level in the topic
        3. Determine optimal difficulty (zone of proximal development)
        4. Generate content adapted to learning style
        5. Include personalized examples based on interests
        6. Predict and optimize for content effectiveness
        
        Content Types:
        - explanation: Conceptual understanding with examples
        - practice: Exercises with adaptive difficulty
        - summary: Condensed review materials
        - visual: Diagrams and interactive visualizations
        - story: Narrative-based learning for engagement
        
        Args:
            user_id: ID of user receiving content
            subject: Subject area (math, science, etc.)
            topic: Specific topic within subject
            content_type: Type of content to generate
            
        Returns:
            Dictionary with personalized content and metadata
        """
        # Get user's learning profile with historical performance data
        profile = self._get_or_create_learning_profile(user_id)
        
        # Determine appropriate difficulty using adaptive algorithm
        # Considers: success rate, time efficiency, frustration indicators
        difficulty = self._determine_content_difficulty(profile, subject, topic)
        
        # Get user's recent performance on this topic
        # Includes: accuracy, common mistakes, time patterns
        recent_performance = self._get_topic_performance(user_id, subject, topic)
        
        # Generate content using AI with personalization context
        content = await self._generate_content(
            content_type=content_type,
            subject=subject,
            topic=topic,
            difficulty=difficulty,
            user_context={
                "learning_style": profile.get("learning_style", "balanced"),
                "performance": recent_performance,
                "preferences": profile.get("preferences", {})
            }
        )
        
        # Store personalized content for tracking
        personalized = PersonalizedContent(
            user_id=user_id,
            content_type=content_type,
            subject=subject,
            topic=topic,
            difficulty=difficulty,
            content_data=content,
            generation_context={
                "profile": profile,
                "performance": recent_performance
            },
            learning_objective=content.get("objective"),
            effectiveness_prediction=self._predict_effectiveness(profile, content)
        )
        self.db.add(personalized)
        self.db.commit()
        
        return {
            "content_id": personalized.id,
            "content": content,
            "metadata": {
                "difficulty": difficulty,
                "estimated_time": content.get("estimated_time", 10),
                "learning_objective": content.get("objective"),
                "personalization_notes": content.get("personalization_notes", [])
            }
        }
    
    async def provide_real_time_feedback(
        self,
        user_id: int,
        session_id: int,
        interaction_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Provide intelligent real-time feedback during active learning sessions.
        
        Feedback Types and Strategies:
        
        1. question_attempt: Analyzes answer correctness and approach
           - Correct: Reinforcement + challenge extension
           - Incorrect: Targeted hints without giving away answer
           - Partial: Acknowledge progress + guide to completion
        
        2. concept_confusion: Detects struggle patterns
           - Simplifies explanation
           - Provides alternative examples
           - Suggests prerequisite review if needed
        
        3. progress_check: Mid-session performance analysis
           - Pace adjustment recommendations
           - Motivation based on achievement
           - Difficulty calibration
        
        4. help_request: Context-aware assistance
           - Analyzes specific struggle point
           - Provides scaffolded support
           - Tracks help patterns for profile updates
        
        Args:
            user_id: ID of user in session
            session_id: Active learning session ID
            interaction_data: Details of user interaction
            
        Returns:
            Contextual feedback with guidance and encouragement
        """
        session = self.db.query(LearningSession).filter_by(
            id=session_id,
            user_id=user_id
        ).first()
        
        if not session:
            raise APIException(status_code=404, detail="Learning session not found")
        
        # Analyze current interaction type to provide appropriate feedback
        feedback_type = interaction_data.get("type")
        
        if feedback_type == "question_attempt":
            # Analyze correctness, approach, and common misconceptions
            return await self._analyze_question_attempt(session, interaction_data)
        elif feedback_type == "concept_confusion":
            # Detect confusion patterns and provide clarification
            return await self._handle_concept_confusion(session, interaction_data)
        elif feedback_type == "progress_check":
            # Evaluate session progress and adjust strategy
            return await self._provide_progress_feedback(session, interaction_data)
        elif feedback_type == "help_request":
            # Provide scaffolded help based on struggle context
            return await self._provide_contextual_help(session, interaction_data)
        else:
            # Default encouraging feedback
            return self._provide_general_encouragement(session)
    
    async def recommend_next_content(
        self,
        user_id: int,
        current_content_id: Optional[str] = None
    ) -> List[ContentRecommendation]:
        """
        Generate intelligent content recommendations using multi-factor analysis.
        
        Recommendation Algorithm:
        
        1. Knowledge Gap Priority (40% weight):
           - Identifies weak areas needing reinforcement
           - Prerequisites for advanced topics
           - Common misconception areas
        
        2. Strength Building (30% weight):
           - Advances in areas of demonstrated competence
           - Provides appropriate challenges
           - Maintains engagement through success
        
        3. Interest Exploration (20% weight):
           - Introduces related topics
           - Cross-curricular connections
           - Expands learning horizons
        
        4. Spaced Repetition (10% weight):
           - Reviews previously learned material
           - Optimizes long-term retention
           - Based on forgetting curve model
        
        Scoring Factors:
        - User's learning style match
        - Historical content effectiveness
        - Current motivation level
        - Time since last exposure
        - Difficulty progression curve
        
        Args:
            user_id: ID of user for recommendations
            current_content_id: Optional current content for context
            
        Returns:
            Top 5 content recommendations ranked by relevance
        """
        profile = self._get_or_create_learning_profile(user_id)
        
        # Get comprehensive progress including mastery levels
        current_progress = self._get_user_progress(user_id)
        
        # Identify knowledge gaps using prerequisite mapping
        knowledge_gaps = self._identify_knowledge_gaps(user_id, current_progress)
        
        # Get historically effective content for this user profile
        effective_content = self._get_effective_content_for_user(profile)
        
        recommendations = []
        
        # Priority 1: Address immediate knowledge gaps (max 3)
        # These are critical for continued progress
        for gap in knowledge_gaps[:3]:
            rec = self._find_content_for_gap(gap, profile, effective_content)
            if rec:
                recommendations.append(rec)
        
        # Priority 2: Build on current strengths (max 2)
        # Maintains momentum and confidence
        strength_content = self._find_strength_building_content(
            profile, current_progress, effective_content
        )
        recommendations.extend(strength_content[:2])
        
        # Priority 3: Introduce new related topics
        # Prevents learning plateau and maintains interest
        if len(recommendations) < 5:
            new_topics = self._find_related_new_topics(
                user_id, current_content_id, effective_content
            )
            recommendations.extend(new_topics[:(5 - len(recommendations))])
        
        # Sort by composite relevance score
        recommendations.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return recommendations[:5]
    
    def update_learning_profile(
        self,
        user_id: int,
        session_data: Dict[str, Any]
    ) -> None:
        """Update user's learning profile based on session data"""
        profile = self.db.query(LearningProfile).filter_by(user_id=user_id).first()
        
        if not profile:
            profile = LearningProfile(user_id=user_id)
            self.db.add(profile)
        
        # Update total learning time
        profile.total_learning_time += session_data.get("duration", 0)
        
        # Update average session duration
        sessions_count = self.db.query(func.count(LearningSession.id)).filter_by(
            user_id=user_id
        ).scalar()
        
        profile.average_session_duration = (
            profile.total_learning_time / sessions_count if sessions_count > 0 else 0
        )
        
        # Update subject performance
        subject = session_data.get("subject")
        if subject:
            current_subjects = profile.strongest_subjects or []
            subject_scores = self._calculate_subject_scores(user_id)
            profile.strongest_subjects = [
                s[0] for s in sorted(
                    subject_scores.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:3]
            ]
        
        # Update learning pace
        profile.learning_pace = self._determine_learning_pace(user_id)
        
        # Update skill levels
        self._update_skill_levels(profile, session_data)
        
        self.db.commit()
    
    # Private helper methods
    
    def _analyze_subject_performance(
        self, 
        sessions: List[LearningSession]
    ) -> Dict[str, Dict[str, float]]:
        """Analyze performance metrics by subject"""
        subject_metrics = {}
        
        for session in sessions:
            if session.subject not in subject_metrics:
                subject_metrics[session.subject] = {
                    "accuracy": [],
                    "completion": [],
                    "engagement": [],
                    "time_spent": 0
                }
            
            metrics = subject_metrics[session.subject]
            if session.accuracy_rate is not None:
                metrics["accuracy"].append(session.accuracy_rate)
            metrics["completion"].append(session.completion_rate)
            metrics["engagement"].append(session.engagement_score)
            metrics["time_spent"] += session.duration_seconds
        
        # Calculate averages
        for subject, metrics in subject_metrics.items():
            metrics["avg_accuracy"] = np.mean(metrics["accuracy"]) if metrics["accuracy"] else 0
            metrics["avg_completion"] = np.mean(metrics["completion"])
            metrics["avg_engagement"] = np.mean(metrics["engagement"])
            
        return subject_metrics
    
    def _identify_learning_style(self, sessions: List[LearningSession]) -> str:
        """Identify user's preferred learning style"""
        content_type_engagement = {}
        
        for session in sessions:
            content_type = session.content_type
            if content_type not in content_type_engagement:
                content_type_engagement[content_type] = []
            content_type_engagement[content_type].append(session.engagement_score)
        
        # Calculate average engagement by content type
        avg_engagement = {
            ct: np.mean(scores) 
            for ct, scores in content_type_engagement.items()
        }
        
        # Map content types to learning styles
        style_mapping = {
            "video": "visual",
            "interactive": "kinesthetic",
            "reading": "reading",
            "audio": "auditory"
        }
        
        # Find dominant style
        if not avg_engagement:
            return "balanced"
        
        best_content_type = max(avg_engagement, key=avg_engagement.get)
        return style_mapping.get(best_content_type, "balanced")
    
    def _identify_strengths(
        self, 
        subject_performance: Dict[str, Dict[str, float]]
    ) -> List[Dict[str, Any]]:
        """Identify user's academic strengths"""
        strengths = []
        
        for subject, metrics in subject_performance.items():
            if (metrics.get("avg_accuracy", 0) > 0.8 and 
                metrics.get("avg_completion", 0) > 0.7):
                strengths.append({
                    "subject": subject,
                    "accuracy": metrics["avg_accuracy"],
                    "engagement": metrics["avg_engagement"],
                    "description": f"Excellent performance in {subject}"
                })
        
        return sorted(strengths, key=lambda x: x["accuracy"], reverse=True)[:3]
    
    def _identify_weaknesses(
        self, 
        subject_performance: Dict[str, Dict[str, float]]
    ) -> List[Dict[str, Any]]:
        """Identify areas needing improvement"""
        weaknesses = []
        
        for subject, metrics in subject_performance.items():
            if (metrics.get("avg_accuracy", 0) < 0.6 or 
                metrics.get("avg_completion", 0) < 0.5):
                weaknesses.append({
                    "subject": subject,
                    "accuracy": metrics["avg_accuracy"],
                    "completion": metrics["avg_completion"],
                    "description": f"Needs improvement in {subject}",
                    "recommendation": self._get_improvement_recommendation(metrics)
                })
        
        return sorted(weaknesses, key=lambda x: x["accuracy"])[:3]
    
    def _get_improvement_recommendation(self, metrics: Dict[str, float]) -> str:
        """Generate specific improvement recommendations"""
        if metrics.get("avg_accuracy", 0) < 0.5:
            return "Focus on understanding fundamental concepts"
        elif metrics.get("avg_completion", 0) < 0.5:
            return "Try shorter learning sessions to maintain focus"
        elif metrics.get("avg_engagement", 0) < 0.5:
            return "Explore different content types for better engagement"
        else:
            return "Practice more problems to reinforce learning"
    
    async def _generate_recommendations(
        self,
        user_id: int,
        strengths: List[Dict[str, Any]],
        weaknesses: List[Dict[str, Any]],
        learning_style: str
    ) -> List[Dict[str, Any]]:
        """Generate personalized learning recommendations"""
        recommendations = []
        
        # Recommendations for weaknesses
        for weakness in weaknesses[:2]:
            recommendations.append({
                "type": "improvement",
                "subject": weakness["subject"],
                "priority": "high",
                "action": weakness["recommendation"],
                "resources": await self._find_resources(
                    weakness["subject"], 
                    learning_style, 
                    "beginner"
                )
            })
        
        # Recommendations for strengths
        for strength in strengths[:1]:
            recommendations.append({
                "type": "advancement",
                "subject": strength["subject"],
                "priority": "medium",
                "action": "Challenge yourself with advanced topics",
                "resources": await self._find_resources(
                    strength["subject"], 
                    learning_style, 
                    "advanced"
                )
            })
        
        # General recommendations based on learning style
        recommendations.append({
            "type": "optimization",
            "priority": "low",
            "action": f"Your learning style is {learning_style}. "
                     f"Try more {self._get_content_type_for_style(learning_style)} content.",
            "resources": []
        })
        
        return recommendations
    
    def _get_content_type_for_style(self, style: str) -> str:
        """Map learning style to content type"""
        mapping = {
            "visual": "video and diagram",
            "auditory": "audio explanation",
            "kinesthetic": "interactive simulation",
            "reading": "detailed text",
            "balanced": "mixed media"
        }
        return mapping.get(style, "varied")
    
    async def _find_resources(
        self, 
        subject: str, 
        learning_style: str, 
        difficulty: str
    ) -> List[Dict[str, str]]:
        """Find learning resources matching criteria"""
        # This would connect to a content database
        # For now, return mock data
        return [
            {
                "id": f"{subject}_{difficulty}_1",
                "title": f"{difficulty.title()} {subject} Guide",
                "type": self._get_content_type_for_style(learning_style),
                "estimated_time": "20 minutes"
            }
        ]
    
    def _create_progress_summary(
        self, 
        sessions: List[LearningSession]
    ) -> Dict[str, Any]:
        """Create a summary of learning progress"""
        total_time = sum(s.duration_seconds for s in sessions)
        total_questions = sum(s.questions_attempted for s in sessions)
        correct_questions = sum(s.questions_correct for s in sessions)
        
        return {
            "total_learning_time": total_time,
            "sessions_completed": len(sessions),
            "questions_attempted": total_questions,
            "overall_accuracy": (
                correct_questions / total_questions if total_questions > 0 else 0
            ),
            "average_engagement": np.mean([s.engagement_score for s in sessions]),
            "topics_covered": len(set(s.topic for s in sessions)),
            "streak_days": self._calculate_streak_days(sessions)
        }
    
    def _calculate_streak_days(self, sessions: List[LearningSession]) -> int:
        """Calculate consecutive learning days"""
        if not sessions:
            return 0
        
        dates = sorted(set(s.start_time.date() for s in sessions))
        streak = 1
        
        for i in range(1, len(dates)):
            if (dates[i] - dates[i-1]).days == 1:
                streak += 1
            else:
                streak = 1
        
        return streak
    
    def _create_default_analysis(self) -> LearningAnalysis:
        """Create default analysis for new users"""
        return LearningAnalysis(
            strengths=[],
            weaknesses=[],
            learning_style="balanced",
            recommendations=[
                {
                    "type": "getting_started",
                    "priority": "high",
                    "action": "Complete your first learning session to get personalized recommendations",
                    "resources": []
                }
            ],
            progress_summary={
                "total_learning_time": 0,
                "sessions_completed": 0,
                "questions_attempted": 0,
                "overall_accuracy": 0,
                "average_engagement": 0,
                "topics_covered": 0,
                "streak_days": 0
            }
        )
    
    def _get_or_create_learning_profile(self, user_id: int) -> Dict[str, Any]:
        """Get or create user's learning profile"""
        profile = self.db.query(LearningProfile).filter_by(user_id=user_id).first()
        
        if not profile:
            profile = LearningProfile(
                user_id=user_id,
                preferred_content_types=["interactive", "video"],
                skill_levels={},
                learning_goals=[]
            )
            self.db.add(profile)
            self.db.commit()
        
        return {
            "learning_style": self._identify_user_learning_style(user_id),
            "preferences": profile.preferred_content_types or [],
            "skill_levels": profile.skill_levels or {},
            "pace": profile.learning_pace or "moderate"
        }
    
    def _identify_user_learning_style(self, user_id: int) -> str:
        """Identify user's learning style from historical data"""
        recent_sessions = self.db.query(LearningSession).filter(
            LearningSession.user_id == user_id
        ).order_by(LearningSession.start_time.desc()).limit(20).all()
        
        if not recent_sessions:
            return "balanced"
        
        return self._identify_learning_style(recent_sessions)
    
    def _determine_content_difficulty(
        self, 
        profile: Dict[str, Any], 
        subject: str, 
        topic: str
    ) -> str:
        """Determine appropriate content difficulty for user"""
        skill_levels = profile.get("skill_levels", {})
        subject_skills = skill_levels.get(subject, {})
        topic_level = subject_skills.get(topic, 0)
        
        if topic_level < 3:
            return "beginner"
        elif topic_level < 7:
            return "intermediate"
        else:
            return "advanced"
    
    def _get_topic_performance(
        self, 
        user_id: int, 
        subject: str, 
        topic: str
    ) -> Dict[str, float]:
        """Get user's performance metrics for a specific topic"""
        sessions = self.db.query(LearningSession).filter(
            and_(
                LearningSession.user_id == user_id,
                LearningSession.subject == subject,
                LearningSession.topic == topic
            )
        ).all()
        
        if not sessions:
            return {"accuracy": 0, "completion": 0, "attempts": 0}
        
        return {
            "accuracy": np.mean([s.accuracy_rate for s in sessions if s.accuracy_rate]),
            "completion": np.mean([s.completion_rate for s in sessions]),
            "attempts": len(sessions),
            "avg_time": np.mean([s.duration_seconds for s in sessions])
        }
    
    async def _generate_content(
        self,
        content_type: str,
        subject: str,
        topic: str,
        difficulty: str,
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate personalized content based on parameters"""
        # This would integrate with an AI content generation service
        # For now, return structured mock content
        
        if content_type == "explanation":
            return self._generate_explanation(subject, topic, difficulty, user_context)
        elif content_type == "question":
            return self._generate_question(subject, topic, difficulty, user_context)
        elif content_type == "example":
            return self._generate_example(subject, topic, difficulty, user_context)
        elif content_type == "exercise":
            return self._generate_exercise(subject, topic, difficulty, user_context)
        else:
            return self._generate_explanation(subject, topic, difficulty, user_context)
    
    def _generate_explanation(
        self, 
        subject: str, 
        topic: str, 
        difficulty: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate personalized explanation"""
        learning_style = context.get("learning_style", "balanced")
        
        base_explanation = {
            "type": "explanation",
            "subject": subject,
            "topic": topic,
            "difficulty": difficulty,
            "objective": f"Understand {topic} in {subject}",
            "estimated_time": 10 if difficulty == "beginner" else 15,
            "sections": []
        }
        
        # Add sections based on learning style
        if learning_style in ["visual", "balanced"]:
            base_explanation["sections"].append({
                "type": "visual",
                "content": f"Visual diagram explaining {topic}",
                "media_url": f"/media/{subject}/{topic}/diagram.svg"
            })
        
        if learning_style in ["reading", "balanced"]:
            base_explanation["sections"].append({
                "type": "text",
                "content": f"Detailed explanation of {topic} concepts...",
                "highlights": ["key concept 1", "key concept 2"]
            })
        
        if learning_style == "kinesthetic":
            base_explanation["sections"].append({
                "type": "interactive",
                "content": f"Interactive simulation for {topic}",
                "simulation_url": f"/simulations/{subject}/{topic}"
            })
        
        # Add personalization notes
        base_explanation["personalization_notes"] = [
            f"Content adapted for {learning_style} learning style",
            f"Difficulty set to {difficulty} based on your progress"
        ]
        
        return base_explanation
    
    def _generate_question(
        self, 
        subject: str, 
        topic: str, 
        difficulty: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate personalized question"""
        performance = context.get("performance", {})
        
        # Adjust question type based on performance
        if performance.get("accuracy", 0) < 0.5:
            question_type = "multiple_choice"
        elif performance.get("accuracy", 0) < 0.7:
            question_type = "fill_blank"
        else:
            question_type = "open_ended"
        
        return {
            "type": "question",
            "question_type": question_type,
            "subject": subject,
            "topic": topic,
            "difficulty": difficulty,
            "objective": f"Test understanding of {topic}",
            "estimated_time": 5,
            "question": f"Sample {difficulty} question about {topic}",
            "options": ["Option A", "Option B", "Option C", "Option D"] if question_type == "multiple_choice" else None,
            "hints": [
                f"Think about the key concept of {topic}",
                "Review the previous explanation if needed"
            ],
            "personalization_notes": [
                f"Question type ({question_type}) selected based on your performance"
            ]
        }
    
    def _generate_example(
        self, 
        subject: str, 
        topic: str, 
        difficulty: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate personalized example"""
        return {
            "type": "example",
            "subject": subject,
            "topic": topic,
            "difficulty": difficulty,
            "objective": f"See {topic} applied in practice",
            "estimated_time": 8,
            "scenario": f"Real-world application of {topic}",
            "step_by_step": [
                {"step": 1, "description": "First, we identify...", "visual": True},
                {"step": 2, "description": "Then, we apply...", "visual": False},
                {"step": 3, "description": "Finally, we conclude...", "visual": True}
            ],
            "practice_problems": [
                {"id": 1, "description": "Try a similar problem", "difficulty": "easy"},
                {"id": 2, "description": "Challenge yourself", "difficulty": "medium"}
            ]
        }
    
    def _generate_exercise(
        self, 
        subject: str, 
        topic: str, 
        difficulty: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate personalized exercise set"""
        num_problems = 3 if difficulty == "beginner" else 5
        
        return {
            "type": "exercise",
            "subject": subject,
            "topic": topic,
            "difficulty": difficulty,
            "objective": f"Practice {topic} skills",
            "estimated_time": num_problems * 5,
            "problems": [
                {
                    "id": i + 1,
                    "type": "problem",
                    "description": f"Problem {i + 1} for {topic}",
                    "difficulty": difficulty,
                    "hints_available": True,
                    "solution_steps": True
                }
                for i in range(num_problems)
            ],
            "adaptive": True,
            "personalization_notes": [
                f"Exercise set contains {num_problems} problems based on {difficulty} level",
                "Problems will adapt based on your performance"
            ]
        }
    
    def _predict_effectiveness(
        self, 
        profile: Dict[str, Any], 
        content: Dict[str, Any]
    ) -> float:
        """Predict how effective the content will be for the user"""
        # Simple prediction based on alignment with learning style
        effectiveness = 0.5
        
        learning_style = profile.get("learning_style", "balanced")
        content_sections = content.get("sections", [])
        
        style_content_match = {
            "visual": ["visual", "diagram", "video"],
            "auditory": ["audio", "explanation"],
            "kinesthetic": ["interactive", "simulation"],
            "reading": ["text", "detailed"]
        }
        
        if learning_style in style_content_match:
            preferred_types = style_content_match[learning_style]
            for section in content_sections:
                if any(pref in str(section).lower() for pref in preferred_types):
                    effectiveness += 0.1
        
        # Adjust based on difficulty match
        if content.get("difficulty") == profile.get("preferred_difficulty", "medium"):
            effectiveness += 0.2
        
        return min(effectiveness, 1.0)
    
    async def _analyze_question_attempt(
        self, 
        session: LearningSession, 
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze a question attempt and provide feedback"""
        is_correct = data.get("is_correct", False)
        time_taken = data.get("time_taken", 0)
        attempt_number = data.get("attempt_number", 1)
        
        feedback = {
            "immediate_feedback": "",
            "explanation": "",
            "next_steps": [],
            "encouragement": ""
        }
        
        if is_correct:
            if time_taken < 30:  # Quick and correct
                feedback["immediate_feedback"] = "Excellent! You got it right quickly."
                feedback["encouragement"] = "You're mastering this concept!"
            else:
                feedback["immediate_feedback"] = "Correct! Well done."
                feedback["encouragement"] = "Keep up the good work!"
            
            feedback["next_steps"] = ["Try a more challenging problem", "Move to the next topic"]
        else:
            if attempt_number == 1:
                feedback["immediate_feedback"] = "Not quite right. Let's try again."
                feedback["explanation"] = "Review the key concept and think about..."
                feedback["next_steps"] = ["Use a hint", "Review the explanation"]
            else:
                feedback["immediate_feedback"] = "Still not correct. Let's break it down."
                feedback["explanation"] = "Here's a step-by-step approach..."
                feedback["next_steps"] = ["See worked example", "Try a simpler problem first"]
            
            feedback["encouragement"] = "Learning takes practice. You're doing great!"
        
        return feedback
    
    async def _handle_concept_confusion(
        self, 
        session: LearningSession, 
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle when user indicates confusion about a concept"""
        concept = data.get("concept", "current topic")
        confusion_level = data.get("level", "moderate")
        
        response = {
            "clarification": "",
            "alternative_explanation": "",
            "examples": [],
            "resources": []
        }
        
        if confusion_level == "high":
            response["clarification"] = f"Let's start with the basics of {concept}..."
            response["alternative_explanation"] = "Think of it this way..."
            response["examples"] = [
                {"type": "simple", "description": "Basic example"},
                {"type": "real_world", "description": "Everyday application"}
            ]
        else:
            response["clarification"] = f"Here's another way to look at {concept}..."
            response["examples"] = [
                {"type": "standard", "description": "Common example"}
            ]
        
        response["resources"] = [
            {"type": "video", "title": f"Visual explanation of {concept}"},
            {"type": "interactive", "title": f"Practice {concept} interactively"}
        ]
        
        return response
    
    async def _provide_progress_feedback(
        self, 
        session: LearningSession, 
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Provide feedback on learning progress"""
        current_accuracy = session.accuracy_rate or 0
        completion_rate = session.completion_rate or 0
        
        feedback = {
            "progress_summary": f"You're {int(completion_rate * 100)}% through this session",
            "performance": "",
            "suggestions": [],
            "motivation": ""
        }
        
        if current_accuracy > 0.8:
            feedback["performance"] = "Outstanding performance!"
            feedback["suggestions"] = ["Challenge yourself with harder problems"]
            feedback["motivation"] = "You're really getting this!"
        elif current_accuracy > 0.6:
            feedback["performance"] = "Good progress!"
            feedback["suggestions"] = ["Focus on the topics you missed", "Take your time"]
            feedback["motivation"] = "Keep going, you're doing well!"
        else:
            feedback["performance"] = "Room for improvement"
            feedback["suggestions"] = ["Review the basics", "Don't hesitate to use hints"]
            feedback["motivation"] = "Every expert was once a beginner!"
        
        return feedback
    
    async def _provide_contextual_help(
        self, 
        session: LearningSession, 
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Provide help based on current context"""
        help_type = data.get("help_type", "general")
        current_topic = session.topic
        
        help_response = {
            "help_content": "",
            "examples": [],
            "tips": [],
            "related_concepts": []
        }
        
        if help_type == "problem_solving":
            help_response["help_content"] = "Here's how to approach this type of problem..."
            help_response["tips"] = [
                "Break down the problem into smaller parts",
                "Identify what you know and what you need to find",
                "Look for patterns from similar problems"
            ]
        elif help_type == "concept":
            help_response["help_content"] = f"Let me explain {current_topic} differently..."
            help_response["related_concepts"] = ["Prerequisite concept", "Related topic"]
        else:
            help_response["help_content"] = "Here are some general study tips..."
            help_response["tips"] = [
                "Take regular breaks",
                "Practice active recall",
                "Teach the concept to someone else"
            ]
        
        return help_response
    
    def _provide_general_encouragement(self, session: LearningSession) -> Dict[str, Any]:
        """Provide general encouragement"""
        encouragements = [
            "You're making progress! Keep it up!",
            "Learning is a journey, not a race.",
            "Every mistake is a learning opportunity!",
            "Your dedication is admirable!",
            "Stay curious and keep exploring!"
        ]
        
        return {
            "message": np.random.choice(encouragements),
            "tip": "Remember to take breaks and stay hydrated!",
            "progress_note": f"You've been learning for {session.duration_seconds // 60} minutes"
        }
    
    def _get_user_progress(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive user progress data"""
        # Get all completed quests
        completed_quests = self.db.query(QuestProgress).filter(
            QuestProgress.user_id == user_id,
            QuestProgress.status == "completed"
        ).all()
        
        # Get learning sessions
        sessions = self.db.query(LearningSession).filter(
            LearningSession.user_id == user_id
        ).all()
        
        # Compile progress data
        progress = {
            "completed_topics": set(),
            "mastered_topics": set(),
            "current_level": {},
            "time_invested": {}
        }
        
        for session in sessions:
            key = f"{session.subject}:{session.topic}"
            progress["completed_topics"].add(key)
            
            if session.accuracy_rate and session.accuracy_rate > 0.9:
                progress["mastered_topics"].add(key)
            
            if session.subject not in progress["time_invested"]:
                progress["time_invested"][session.subject] = 0
            progress["time_invested"][session.subject] += session.duration_seconds
        
        return progress
    
    def _identify_knowledge_gaps(
        self, 
        user_id: int, 
        current_progress: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify gaps in user's knowledge"""
        gaps = []
        
        # Get curriculum structure (this would come from a curriculum service)
        curriculum = self._get_curriculum_structure()
        
        completed_topics = current_progress.get("completed_topics", set())
        mastered_topics = current_progress.get("mastered_topics", set())
        
        for subject, topics in curriculum.items():
            for topic in topics:
                topic_key = f"{subject}:{topic['name']}"
                
                # Check prerequisites
                prereqs_met = all(
                    f"{subject}:{prereq}" in completed_topics 
                    for prereq in topic.get("prerequisites", [])
                )
                
                if prereqs_met and topic_key not in completed_topics:
                    gaps.append({
                        "subject": subject,
                        "topic": topic["name"],
                        "type": "not_started",
                        "priority": topic.get("priority", "medium"),
                        "estimated_time": topic.get("estimated_time", 30)
                    })
                elif topic_key in completed_topics and topic_key not in mastered_topics:
                    gaps.append({
                        "subject": subject,
                        "topic": topic["name"],
                        "type": "needs_practice",
                        "priority": "high",
                        "estimated_time": 20
                    })
        
        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        gaps.sort(key=lambda x: priority_order.get(x["priority"], 1))
        
        return gaps
    
    def _get_curriculum_structure(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get curriculum structure (mock data)"""
        return {
            "math": [
                {"name": "basic_arithmetic", "prerequisites": [], "priority": "high"},
                {"name": "fractions", "prerequisites": ["basic_arithmetic"], "priority": "high"},
                {"name": "decimals", "prerequisites": ["fractions"], "priority": "medium"},
                {"name": "algebra_basics", "prerequisites": ["fractions", "decimals"], "priority": "medium"}
            ],
            "science": [
                {"name": "scientific_method", "prerequisites": [], "priority": "high"},
                {"name": "matter_states", "prerequisites": [], "priority": "medium"},
                {"name": "energy_forms", "prerequisites": ["matter_states"], "priority": "medium"}
            ]
        }
    
    def _get_effective_content_for_user(
        self, 
        profile: Dict[str, Any]
    ) -> List[ContentEffectiveness]:
        """Get content that has been effective for similar users"""
        # Get content with high effectiveness scores
        effective_content = self.db.query(ContentEffectiveness).filter(
            ContentEffectiveness.engagement_score > 0.7,
            ContentEffectiveness.average_completion_rate > 0.8
        ).all()
        
        # Filter based on user's learning style
        learning_style = profile.get("learning_style", "balanced")
        
        # This would use more sophisticated matching in production
        return effective_content
    
    def _find_content_for_gap(
        self,
        gap: Dict[str, Any],
        profile: Dict[str, Any],
        effective_content: List[ContentEffectiveness]
    ) -> Optional[ContentRecommendation]:
        """Find content to address a specific knowledge gap"""
        subject = gap["subject"]
        topic = gap["topic"]
        
        # Find matching content
        for content in effective_content:
            if content.subject == subject and content.topic == topic:
                return ContentRecommendation(
                    content_id=content.content_id,
                    content_type=content.content_type,
                    subject=subject,
                    topic=topic,
                    difficulty=self._determine_content_difficulty(profile, subject, topic),
                    relevance_score=0.9,
                    reason=f"Address gap in {topic}"
                )
        
        # Generate new content recommendation if no existing content found
        return ContentRecommendation(
            content_id=f"generated_{subject}_{topic}",
            content_type="interactive",
            subject=subject,
            topic=topic,
            difficulty="beginner",
            relevance_score=0.8,
            reason=f"Foundation building for {topic}"
        )
    
    def _find_strength_building_content(
        self,
        profile: Dict[str, Any],
        progress: Dict[str, Any],
        effective_content: List[ContentEffectiveness]
    ) -> List[ContentRecommendation]:
        """Find content that builds on user's strengths"""
        recommendations = []
        mastered_topics = progress.get("mastered_topics", set())
        
        for topic_key in mastered_topics:
            subject, topic = topic_key.split(":")
            
            # Find advanced content in the same subject
            for content in effective_content:
                if (content.subject == subject and 
                    content.difficulty_rating > 3 and
                    content.topic != topic):
                    recommendations.append(ContentRecommendation(
                        content_id=content.content_id,
                        content_type=content.content_type,
                        subject=subject,
                        topic=content.topic,
                        difficulty="advanced",
                        relevance_score=0.7,
                        reason=f"Build on mastery of {topic}"
                    ))
        
        return recommendations[:3]
    
    def _find_related_new_topics(
        self,
        user_id: int,
        current_content_id: Optional[str],
        effective_content: List[ContentEffectiveness]
    ) -> List[ContentRecommendation]:
        """Find new related topics to explore"""
        recommendations = []
        
        if current_content_id:
            # Find current content
            current = next(
                (c for c in effective_content if c.content_id == current_content_id), 
                None
            )
            
            if current:
                # Find related topics
                for content in effective_content:
                    if (content.subject == current.subject and 
                        content.topic != current.topic):
                        recommendations.append(ContentRecommendation(
                            content_id=content.content_id,
                            content_type=content.content_type,
                            subject=content.subject,
                            topic=content.topic,
                            difficulty="medium",
                            relevance_score=0.6,
                            reason="Related topic to explore"
                        ))
        
        return recommendations[:5]
    
    def _calculate_subject_scores(self, user_id: int) -> Dict[str, float]:
        """Calculate performance scores by subject"""
        sessions = self.db.query(LearningSession).filter_by(user_id=user_id).all()
        
        subject_scores = {}
        for session in sessions:
            if session.subject not in subject_scores:
                subject_scores[session.subject] = []
            
            # Calculate session score
            score = (
                (session.accuracy_rate or 0) * 0.4 +
                (session.completion_rate or 0) * 0.3 +
                (session.engagement_score or 0) * 0.3
            )
            subject_scores[session.subject].append(score)
        
        # Average scores by subject
        return {
            subject: np.mean(scores) 
            for subject, scores in subject_scores.items()
        }
    
    def _determine_learning_pace(self, user_id: int) -> str:
        """Determine user's learning pace"""
        recent_sessions = self.db.query(LearningSession).filter(
            LearningSession.user_id == user_id
        ).order_by(LearningSession.start_time.desc()).limit(10).all()
        
        if not recent_sessions:
            return "moderate"
        
        # Calculate average completion time vs estimated time
        completion_ratios = []
        for session in recent_sessions:
            if session.duration_seconds and session.content_type:
                # Estimate expected duration based on content type
                expected_duration = {
                    "video": 600,  # 10 minutes
                    "interactive": 900,  # 15 minutes
                    "quiz": 300,  # 5 minutes
                    "reading": 480  # 8 minutes
                }.get(session.content_type, 600)
                
                ratio = session.duration_seconds / expected_duration
                completion_ratios.append(ratio)
        
        if not completion_ratios:
            return "moderate"
        
        avg_ratio = np.mean(completion_ratios)
        
        if avg_ratio < 0.8:
            return "fast"
        elif avg_ratio > 1.2:
            return "slow"
        else:
            return "moderate"
    
    def _update_skill_levels(
        self, 
        profile: LearningProfile, 
        session_data: Dict[str, Any]
    ) -> None:
        """Update skill levels based on session performance"""
        subject = session_data.get("subject")
        topic = session_data.get("topic")
        accuracy = session_data.get("accuracy", 0)
        
        if not subject or not topic:
            return
        
        skill_levels = profile.skill_levels or {}
        
        if subject not in skill_levels:
            skill_levels[subject] = {}
        
        current_level = skill_levels[subject].get(topic, 0)
        
        # Update level based on performance
        if accuracy > 0.9:
            new_level = min(current_level + 1, 10)
        elif accuracy > 0.7:
            new_level = current_level + 0.5
        elif accuracy < 0.5:
            new_level = max(current_level - 0.5, 0)
        else:
            new_level = current_level
        
        skill_levels[subject][topic] = new_level
        profile.skill_levels = skill_levels