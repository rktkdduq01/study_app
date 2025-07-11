"""
AI Tutor Service for personalized learning
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import asyncio
from sqlalchemy.orm import Session
from openai import AsyncOpenAI
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

from app.core.config import settings
from app.core.logger import get_logger
from app.models.user import User
from app.models.learning_profile import LearningProfile
from app.models.personalized_content import PersonalizedContent
from app.core.redis_client import redis_client
from app.services.user_analytics import UserAnalyticsService

logger = get_logger(__name__)


class AITutorService:
    """AI-powered tutoring service"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.analytics = UserAnalyticsService()
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.temperature = settings.OPENAI_TEMPERATURE
        
    async def generate_personalized_content(
        self,
        user: User,
        subject: str,
        topic: str,
        difficulty_level: int,
        db: Session
    ) -> Dict[str, Any]:
        """Generate personalized learning content"""
        try:
            # Get user's learning profile
            profile = await self._get_learning_profile(user, db)
            
            # Analyze user's performance
            performance_data = await self.analytics.get_user_performance(user.id, subject)
            
            # Generate content prompt
            prompt = self._create_content_prompt(
                profile,
                subject,
                topic,
                difficulty_level,
                performance_data
            )
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            content = response.choices[0].message.content
            
            # Parse and structure the content
            structured_content = self._parse_content(content)
            
            # Save to database
            personalized_content = PersonalizedContent(
                user_id=user.id,
                subject=subject,
                topic=topic,
                difficulty_level=difficulty_level,
                content_type=structured_content["type"],
                content=json.dumps(structured_content),
                adaptation_reason=structured_content.get("adaptation_reason", "")
            )
            db.add(personalized_content)
            db.commit()
            
            # Cache the content
            await self._cache_content(user.id, structured_content)
            
            logger.info(f"Generated personalized content for user {user.id} - {subject}/{topic}")
            
            return structured_content
            
        except Exception as e:
            logger.error(f"Error generating personalized content: {str(e)}")
            raise
    
    async def provide_real_time_feedback(
        self,
        user: User,
        question: str,
        user_answer: str,
        correct_answer: str,
        subject: str,
        db: Session
    ) -> Dict[str, Any]:
        """Provide real-time AI feedback on user's answer"""
        try:
            # Analyze the answer
            prompt = self._create_feedback_prompt(question, user_answer, correct_answer, subject)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_feedback_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            feedback_text = response.choices[0].message.content
            
            # Parse feedback
            feedback = self._parse_feedback(feedback_text)
            
            # Update user's learning profile based on feedback
            await self._update_learning_profile(user, subject, feedback, db)
            
            # Generate follow-up recommendations
            if not feedback["is_correct"]:
                feedback["recommendations"] = await self._generate_recommendations(
                    user, subject, question, db
                )
            
            return feedback
            
        except Exception as e:
            logger.error(f"Error providing feedback: {str(e)}")
            raise
    
    async def generate_practice_questions(
        self,
        user: User,
        subject: str,
        topic: str,
        count: int = 5,
        db: Session = None
    ) -> List[Dict[str, Any]]:
        """Generate practice questions based on user's level"""
        try:
            # Get user's current level and weak areas
            profile = await self._get_learning_profile(user, db)
            weak_areas = await self._identify_weak_areas(user, subject)
            
            prompt = self._create_practice_questions_prompt(
                subject, topic, count, profile, weak_areas
            )
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_question_generation_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=0.8
            )
            
            questions_text = response.choices[0].message.content
            questions = self._parse_questions(questions_text)
            
            # Add metadata to each question
            for i, question in enumerate(questions):
                question["id"] = f"{user.id}_{subject}_{topic}_{i}"
                question["difficulty"] = self._calculate_question_difficulty(question, profile)
                question["estimated_time"] = self._estimate_completion_time(question)
            
            return questions
            
        except Exception as e:
            logger.error(f"Error generating practice questions: {str(e)}")
            raise
    
    async def create_learning_path(
        self,
        user: User,
        goal: str,
        timeline_days: int,
        db: Session
    ) -> Dict[str, Any]:
        """Create personalized learning path"""
        try:
            # Analyze user's current knowledge
            current_knowledge = await self._assess_current_knowledge(user, db)
            
            # Generate learning path
            prompt = self._create_learning_path_prompt(
                goal, timeline_days, current_knowledge
            )
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_learning_path_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=0.6
            )
            
            path_text = response.choices[0].message.content
            learning_path = self._parse_learning_path(path_text)
            
            # Add scheduling and milestones
            learning_path = self._add_milestones(learning_path, timeline_days)
            
            # Save learning path
            await self._save_learning_path(user.id, learning_path, db)
            
            return learning_path
            
        except Exception as e:
            logger.error(f"Error creating learning path: {str(e)}")
            raise
    
    async def analyze_learning_style(
        self,
        user: User,
        db: Session
    ) -> Dict[str, Any]:
        """Analyze user's learning style using AI"""
        try:
            # Collect user interaction data
            interaction_data = await self._collect_interaction_data(user.id)
            
            # Prepare data for analysis
            features = self._extract_learning_features(interaction_data)
            
            # Use clustering to identify learning patterns
            learning_style = self._identify_learning_style(features)
            
            # Get AI interpretation
            prompt = self._create_learning_style_prompt(learning_style, features)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_learning_style_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.5
            )
            
            analysis = self._parse_learning_style_analysis(response.choices[0].message.content)
            
            # Update user's profile
            await self._update_learning_style(user, analysis, db)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing learning style: {str(e)}")
            raise
    
    async def generate_explanation(
        self,
        concept: str,
        user_level: str,
        learning_style: str,
        examples_count: int = 3
    ) -> Dict[str, Any]:
        """Generate AI explanation for a concept"""
        try:
            prompt = f"""
            Explain the concept: {concept}
            
            User Level: {user_level}
            Learning Style: {learning_style}
            
            Provide:
            1. Clear explanation suited to the level
            2. {examples_count} relevant examples
            3. Visual descriptions if applicable
            4. Common misconceptions
            5. Practice tips
            
            Format as structured JSON.
            """
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_explanation_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            explanation = self._parse_explanation(response.choices[0].message.content)
            
            # Add interactive elements
            explanation["interactive_elements"] = self._generate_interactive_elements(concept)
            
            return explanation
            
        except Exception as e:
            logger.error(f"Error generating explanation: {str(e)}")
            raise
    
    async def provide_hint(
        self,
        question: str,
        user_attempts: List[str],
        hint_level: int = 1
    ) -> Dict[str, Any]:
        """Provide progressive hints"""
        try:
            prompt = self._create_hint_prompt(question, user_attempts, hint_level)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_hint_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.6
            )
            
            hint = self._parse_hint(response.choices[0].message.content)
            hint["level"] = hint_level
            hint["next_level_available"] = hint_level < 3
            
            return hint
            
        except Exception as e:
            logger.error(f"Error providing hint: {str(e)}")
            raise
    
    # Helper methods
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for content generation"""
        return """
        You are an expert educational content creator and AI tutor. 
        Generate engaging, age-appropriate learning content that:
        1. Matches the user's learning level and style
        2. Includes interactive elements
        3. Provides clear explanations
        4. Uses relevant examples
        5. Encourages active learning
        
        Format all responses as valid JSON.
        """
    
    def _get_feedback_system_prompt(self) -> str:
        """Get system prompt for feedback generation"""
        return """
        You are a supportive and constructive AI tutor providing feedback.
        Analyze student answers and provide:
        1. Whether the answer is correct
        2. What they did well
        3. Areas for improvement
        4. Encouraging message
        5. Next steps
        
        Be positive and growth-oriented. Format as JSON.
        """
    
    def _get_question_generation_prompt(self) -> str:
        """Get system prompt for question generation"""
        return """
        You are an expert question designer creating educational assessments.
        Generate questions that:
        1. Test understanding, not just memorization
        2. Include various difficulty levels
        3. Have clear, unambiguous answers
        4. Include explanations for answers
        5. Are engaging and relevant
        
        Format as JSON array.
        """
    
    def _get_learning_path_system_prompt(self) -> str:
        """Get system prompt for learning path creation"""
        return """
        You are an expert educational planner creating personalized learning paths.
        Design paths that:
        1. Break down complex goals into manageable steps
        2. Build on prerequisite knowledge
        3. Include practice and review sessions
        4. Adapt to the timeline
        5. Maintain motivation
        
        Format as structured JSON with milestones.
        """
    
    def _get_learning_style_system_prompt(self) -> str:
        """Get system prompt for learning style analysis"""
        return """
        You are an educational psychologist analyzing learning patterns.
        Provide insights on:
        1. Primary learning style (visual, auditory, kinesthetic, reading/writing)
        2. Preferred content types
        3. Optimal study session duration
        4. Best practice methods
        5. Personalization recommendations
        
        Be specific and actionable. Format as JSON.
        """
    
    def _get_explanation_system_prompt(self) -> str:
        """Get system prompt for concept explanation"""
        return """
        You are a master teacher explaining complex concepts simply.
        Your explanations should:
        1. Start with the big picture
        2. Break down into digestible parts
        3. Use analogies and examples
        4. Address common confusion points
        5. Connect to real-world applications
        
        Adapt complexity to user level. Format as JSON.
        """
    
    def _get_hint_system_prompt(self) -> str:
        """Get system prompt for hint generation"""
        return """
        You are a patient tutor providing progressive hints.
        Your hints should:
        1. Guide without giving away the answer
        2. Build on previous attempts
        3. Encourage problem-solving
        4. Get more specific with each level
        5. Maintain student engagement
        
        Format as JSON with hint text and guidance.
        """
    
    async def _get_learning_profile(self, user: User, db: Session) -> LearningProfile:
        """Get or create user's learning profile"""
        profile = db.query(LearningProfile).filter_by(user_id=user.id).first()
        if not profile:
            profile = LearningProfile(
                user_id=user.id,
                learning_style="balanced",
                preferred_difficulty=5,
                strengths=[],
                weaknesses=[],
                interests=[]
            )
            db.add(profile)
            db.commit()
        return profile
    
    def _create_content_prompt(
        self,
        profile: LearningProfile,
        subject: str,
        topic: str,
        difficulty: int,
        performance_data: Dict
    ) -> str:
        """Create prompt for content generation"""
        return f"""
        Create personalized learning content:
        
        Subject: {subject}
        Topic: {topic}
        Difficulty Level: {difficulty}/10
        
        User Profile:
        - Learning Style: {profile.learning_style}
        - Strengths: {', '.join(profile.strengths)}
        - Weaknesses: {', '.join(profile.weaknesses)}
        - Recent Performance: {performance_data.get('accuracy', 'N/A')}%
        
        Generate content that includes:
        1. Main explanation
        2. Examples (visual if applicable)
        3. Practice problems
        4. Key takeaways
        5. Additional resources
        
        Format as JSON with clear structure.
        """
    
    def _parse_content(self, content: str) -> Dict[str, Any]:
        """Parse AI-generated content"""
        try:
            # Try to parse as JSON
            return json.loads(content)
        except:
            # Fallback structure
            return {
                "type": "lesson",
                "title": "Learning Content",
                "sections": [
                    {
                        "type": "explanation",
                        "content": content
                    }
                ],
                "practice_problems": [],
                "resources": []
            }
    
    def _parse_feedback(self, feedback_text: str) -> Dict[str, Any]:
        """Parse AI-generated feedback"""
        try:
            return json.loads(feedback_text)
        except:
            # Fallback parsing
            is_correct = "correct" in feedback_text.lower()
            return {
                "is_correct": is_correct,
                "feedback": feedback_text,
                "strengths": [],
                "improvements": [],
                "next_steps": []
            }
    
    def _parse_questions(self, questions_text: str) -> List[Dict[str, Any]]:
        """Parse AI-generated questions"""
        try:
            return json.loads(questions_text)
        except:
            # Fallback to empty list
            logger.error("Failed to parse questions")
            return []
    
    def _parse_learning_path(self, path_text: str) -> Dict[str, Any]:
        """Parse AI-generated learning path"""
        try:
            return json.loads(path_text)
        except:
            # Fallback structure
            return {
                "goal": "Learning Path",
                "duration_days": 30,
                "modules": [],
                "milestones": []
            }
    
    def _parse_learning_style_analysis(self, analysis_text: str) -> Dict[str, Any]:
        """Parse learning style analysis"""
        try:
            return json.loads(analysis_text)
        except:
            return {
                "primary_style": "balanced",
                "characteristics": [],
                "recommendations": []
            }
    
    def _parse_explanation(self, explanation_text: str) -> Dict[str, Any]:
        """Parse concept explanation"""
        try:
            return json.loads(explanation_text)
        except:
            return {
                "concept": "Explanation",
                "main_explanation": explanation_text,
                "examples": [],
                "tips": []
            }
    
    def _parse_hint(self, hint_text: str) -> Dict[str, Any]:
        """Parse hint response"""
        try:
            return json.loads(hint_text)
        except:
            return {
                "hint": hint_text,
                "guidance": "Try thinking about the problem differently"
            }
    
    async def _cache_content(self, user_id: int, content: Dict[str, Any]):
        """Cache generated content"""
        key = f"ai_content:{user_id}:{content.get('topic', 'general')}"
        await redis_client.setex(
            key,
            3600,  # 1 hour cache
            json.dumps(content)
        )
    
    async def _update_learning_profile(
        self,
        user: User,
        subject: str,
        feedback: Dict[str, Any],
        db: Session
    ):
        """Update learning profile based on feedback"""
        profile = await self._get_learning_profile(user, db)
        
        # Update strengths and weaknesses
        if feedback["is_correct"]:
            if subject not in profile.strengths:
                profile.strengths.append(subject)
        else:
            if subject not in profile.weaknesses:
                profile.weaknesses.append(subject)
        
        db.commit()
    
    async def _identify_weak_areas(self, user: User, subject: str) -> List[str]:
        """Identify user's weak areas in subject"""
        # Get performance data from analytics
        performance = await self.analytics.get_detailed_performance(user.id, subject)
        
        weak_areas = []
        for topic, stats in performance.get("topics", {}).items():
            if stats.get("accuracy", 100) < 70:
                weak_areas.append(topic)
        
        return weak_areas
    
    def _calculate_question_difficulty(
        self,
        question: Dict[str, Any],
        profile: LearningProfile
    ) -> int:
        """Calculate appropriate difficulty for question"""
        base_difficulty = question.get("difficulty", 5)
        
        # Adjust based on user's preferred difficulty
        adjusted = base_difficulty * (profile.preferred_difficulty / 5)
        
        return max(1, min(10, int(adjusted)))
    
    def _estimate_completion_time(self, question: Dict[str, Any]) -> int:
        """Estimate time to complete question in seconds"""
        question_type = question.get("type", "multiple_choice")
        
        time_estimates = {
            "multiple_choice": 30,
            "short_answer": 60,
            "essay": 300,
            "problem_solving": 120
        }
        
        return time_estimates.get(question_type, 60)
    
    def _create_practice_questions_prompt(
        self,
        subject: str,
        topic: str,
        count: int,
        profile: LearningProfile,
        weak_areas: List[str]
    ) -> str:
        """Create prompt for practice question generation"""
        return f"""
        Generate {count} practice questions:
        
        Subject: {subject}
        Topic: {topic}
        User Level: {profile.preferred_difficulty}/10
        Weak Areas: {', '.join(weak_areas)}
        
        Include:
        1. Variety of question types
        2. Focus on weak areas
        3. Clear correct answers
        4. Explanations for each answer
        5. Gradually increasing difficulty
        
        Format as JSON array with structure:
        [{{
            "question": "...",
            "type": "multiple_choice|short_answer|problem_solving",
            "options": [...],  // for multiple choice
            "correct_answer": "...",
            "explanation": "...",
            "topic_tags": [...]
        }}]
        """
    
    async def _assess_current_knowledge(self, user: User, db: Session) -> Dict[str, Any]:
        """Assess user's current knowledge level"""
        # Get all subjects user has studied
        performance = await self.analytics.get_overall_performance(user.id)
        
        knowledge_map = {}
        for subject, data in performance.get("subjects", {}).items():
            knowledge_map[subject] = {
                "level": self._calculate_knowledge_level(data),
                "topics_covered": data.get("topics", []),
                "accuracy": data.get("accuracy", 0)
            }
        
        return knowledge_map
    
    def _calculate_knowledge_level(self, performance_data: Dict) -> str:
        """Calculate knowledge level from performance"""
        accuracy = performance_data.get("accuracy", 0)
        
        if accuracy >= 90:
            return "advanced"
        elif accuracy >= 75:
            return "intermediate"
        elif accuracy >= 60:
            return "beginner"
        else:
            return "novice"
    
    def _create_learning_path_prompt(
        self,
        goal: str,
        timeline_days: int,
        current_knowledge: Dict[str, Any]
    ) -> str:
        """Create prompt for learning path generation"""
        return f"""
        Create a personalized learning path:
        
        Goal: {goal}
        Timeline: {timeline_days} days
        
        Current Knowledge:
        {json.dumps(current_knowledge, indent=2)}
        
        Design a path that:
        1. Builds on existing knowledge
        2. Fills knowledge gaps
        3. Progresses logically
        4. Includes practice and review
        5. Maintains realistic daily commitments
        
        Format as JSON with modules, topics, and daily schedule.
        """
    
    def _add_milestones(self, learning_path: Dict[str, Any], timeline_days: int) -> Dict[str, Any]:
        """Add milestones to learning path"""
        modules = learning_path.get("modules", [])
        if not modules:
            return learning_path
        
        # Calculate milestone intervals
        milestone_interval = max(7, timeline_days // 4)  # At least weekly
        
        milestones = []
        for i in range(0, timeline_days, milestone_interval):
            milestone = {
                "day": i + milestone_interval,
                "title": f"Week {(i // 7) + 1} Review",
                "goals": [],
                "assessment_type": "quiz"
            }
            milestones.append(milestone)
        
        learning_path["milestones"] = milestones
        return learning_path
    
    async def _save_learning_path(self, user_id: int, learning_path: Dict[str, Any], db: Session):
        """Save learning path to database"""
        # Store in Redis for quick access
        key = f"learning_path:{user_id}"
        await redis_client.setex(
            key,
            86400 * 30,  # 30 days
            json.dumps(learning_path)
        )
        
        logger.info(f"Saved learning path for user {user_id}")
    
    async def _collect_interaction_data(self, user_id: int) -> Dict[str, Any]:
        """Collect user interaction data for analysis"""
        # Get various interaction metrics
        data = {
            "session_durations": await self._get_session_durations(user_id),
            "content_preferences": await self._get_content_preferences(user_id),
            "response_times": await self._get_response_times(user_id),
            "error_patterns": await self._get_error_patterns(user_id),
            "engagement_metrics": await self._get_engagement_metrics(user_id)
        }
        
        return data
    
    def _extract_learning_features(self, interaction_data: Dict[str, Any]) -> np.ndarray:
        """Extract features for learning style analysis"""
        features = []
        
        # Average session duration
        sessions = interaction_data.get("session_durations", [])
        avg_session = np.mean(sessions) if sessions else 30
        features.append(avg_session)
        
        # Content type preferences (video, text, interactive)
        prefs = interaction_data.get("content_preferences", {})
        features.extend([
            prefs.get("video", 0),
            prefs.get("text", 0),
            prefs.get("interactive", 0)
        ])
        
        # Response time patterns
        response_times = interaction_data.get("response_times", [])
        avg_response = np.mean(response_times) if response_times else 60
        features.append(avg_response)
        
        # Error recovery rate
        error_data = interaction_data.get("error_patterns", {})
        recovery_rate = error_data.get("recovery_rate", 0.5)
        features.append(recovery_rate)
        
        return np.array(features).reshape(1, -1)
    
    def _identify_learning_style(self, features: np.ndarray) -> str:
        """Identify learning style from features"""
        # Simple rule-based classification
        # In production, use trained ML model
        
        video_pref = features[0][1]
        text_pref = features[0][2]
        interactive_pref = features[0][3]
        
        if video_pref > text_pref and video_pref > interactive_pref:
            return "visual"
        elif text_pref > video_pref and text_pref > interactive_pref:
            return "reading/writing"
        elif interactive_pref > video_pref and interactive_pref > text_pref:
            return "kinesthetic"
        else:
            return "balanced"
    
    def _create_learning_style_prompt(self, style: str, features: np.ndarray) -> str:
        """Create prompt for learning style analysis"""
        return f"""
        Analyze learning style data:
        
        Identified Style: {style}
        
        Metrics:
        - Average Session Duration: {features[0][0]:.1f} minutes
        - Video Content Preference: {features[0][1]:.2f}
        - Text Content Preference: {features[0][2]:.2f}
        - Interactive Content Preference: {features[0][3]:.2f}
        - Average Response Time: {features[0][4]:.1f} seconds
        - Error Recovery Rate: {features[0][5]:.2f}
        
        Provide:
        1. Detailed style characteristics
        2. Optimal learning strategies
        3. Content recommendations
        4. Study schedule suggestions
        5. Potential challenges and solutions
        
        Format as comprehensive JSON analysis.
        """
    
    async def _update_learning_style(self, user: User, analysis: Dict[str, Any], db: Session):
        """Update user's learning style in profile"""
        profile = await self._get_learning_profile(user, db)
        profile.learning_style = analysis.get("primary_style", "balanced")
        profile.learning_preferences = json.dumps(analysis)
        db.commit()
    
    def _generate_interactive_elements(self, concept: str) -> List[Dict[str, Any]]:
        """Generate interactive elements for concept"""
        return [
            {
                "type": "quiz",
                "title": f"Quick Check: {concept}",
                "questions": 3
            },
            {
                "type": "simulation",
                "title": f"Explore {concept}",
                "interactive": True
            },
            {
                "type": "practice",
                "title": f"Practice {concept}",
                "problems": 5
            }
        ]
    
    def _create_hint_prompt(self, question: str, attempts: List[str], level: int) -> str:
        """Create prompt for hint generation"""
        return f"""
        Question: {question}
        
        User's attempts: {', '.join(attempts)}
        Hint Level: {level}/3
        
        Provide a hint that:
        1. Helps without revealing the answer
        2. Builds on their attempts
        3. Gets progressively more specific
        4. Encourages problem-solving
        
        Format as JSON with hint and guidance.
        """
    
    # Data collection helpers (mock implementations)
    
    async def _get_session_durations(self, user_id: int) -> List[float]:
        """Get user's session durations"""
        # In production, query from session tracking
        return [30, 45, 25, 60, 40]  # minutes
    
    async def _get_content_preferences(self, user_id: int) -> Dict[str, float]:
        """Get content type preferences"""
        # In production, analyze user's content interactions
        return {
            "video": 0.4,
            "text": 0.3,
            "interactive": 0.3
        }
    
    async def _get_response_times(self, user_id: int) -> List[float]:
        """Get response times for questions"""
        # In production, query from response tracking
        return [45, 30, 60, 25, 50]  # seconds
    
    async def _get_error_patterns(self, user_id: int) -> Dict[str, Any]:
        """Get error patterns and recovery"""
        # In production, analyze error logs
        return {
            "common_errors": ["calculation", "concept_confusion"],
            "recovery_rate": 0.7
        }
    
    async def _get_engagement_metrics(self, user_id: int) -> Dict[str, Any]:
        """Get engagement metrics"""
        # In production, query from engagement tracking
        return {
            "completion_rate": 0.85,
            "interaction_rate": 0.65,
            "return_rate": 0.9
        }


# Global AI tutor service instance
ai_tutor_service = AITutorService()