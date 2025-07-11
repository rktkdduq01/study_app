"""
Tests for content generation engine
"""
import pytest
from typing import Dict, Any

from app.services.content_generation_engine import (
    ContentGenerationEngine,
    MathContentGenerator,
    ScienceContentGenerator,
    LanguageContentGenerator
)
from app.services.content_generators import (
    HistoryContentGenerator,
    GeographyContentGenerator,
    ComputerScienceContentGenerator,
    ArtContentGenerator
)


class TestContentGenerators:
    """Test individual content generators"""
    
    @pytest.mark.asyncio
    async def test_math_content_generator(self):
        """Test math content generation"""
        generator = MathContentGenerator()
        
        # Test fractions content
        content = await generator.generate(
            topic="fractions",
            difficulty="beginner",
            context={"learning_style": "visual"}
        )
        
        assert content["topic"] == "fractions"
        assert content["difficulty"] == "beginner"
        assert len(content["sections"]) > 0
        assert "practice_problems" in content
        
        # Check for visual elements
        visual_section = next(
            (s for s in content["sections"] if s.get("visual")), 
            None
        )
        assert visual_section is not None
    
    @pytest.mark.asyncio
    async def test_science_content_generator(self):
        """Test science content generation"""
        generator = ScienceContentGenerator()
        
        # Test matter states content
        content = await generator.generate(
            topic="matter_states",
            difficulty="beginner",
            context={"learning_style": "kinesthetic"}
        )
        
        assert content["topic"] == "matter_states"
        assert len(content["sections"]) > 0
        assert "experiments" in content  # Kinesthetic learners get experiments
    
    @pytest.mark.asyncio
    async def test_language_content_generator(self):
        """Test language content generation"""
        generator = LanguageContentGenerator()
        
        # Test reading comprehension
        content = await generator.generate(
            topic="reading_comprehension",
            difficulty="beginner",
            context={"interests": ["adventure"]}
        )
        
        assert content["topic"] == "reading_comprehension"
        assert "passage" in content
        assert content["passage"]["title"] == "The Hidden Treasure"
    
    @pytest.mark.asyncio
    async def test_history_content_generator(self):
        """Test history content generation"""
        generator = HistoryContentGenerator()
        
        # Test ancient civilizations
        content = await generator.generate(
            topic="ancient_civilizations",
            difficulty="intermediate",
            context={"learning_style": "visual"}
        )
        
        assert content["topic"] == "ancient_civilizations"
        assert len(content["sections"]) > 0
        assert "timeline" in content  # Visual learners get timeline
    
    @pytest.mark.asyncio
    async def test_computer_science_content_generator(self):
        """Test computer science content generation"""
        generator = ComputerScienceContentGenerator()
        
        # Test programming basics
        content = await generator.generate(
            topic="programming_basics",
            difficulty="beginner",
            context={"learning_style": "visual", "programming_experience": "none"}
        )
        
        assert content["topic"] == "programming_basics"
        assert "coding_environment" in content
        assert content["coding_environment"]["enabled"] is True


class TestContentGenerationEngine:
    """Test the main content generation engine"""
    
    @pytest.fixture
    def engine(self):
        """Create content generation engine instance"""
        return ContentGenerationEngine()
    
    @pytest.mark.asyncio
    async def test_generate_personalized_content(self, engine):
        """Test personalized content generation"""
        content = await engine.generate_personalized_content(
            subject="math",
            topic="fractions",
            difficulty="beginner",
            user_context={
                "learning_style": "visual",
                "performance": {"accuracy": 85},
                "preferences": {},
                "interests": []
            }
        )
        
        assert "metadata" in content
        assert "adaptive_features" in content
        assert content["metadata"]["personalization_context"]["learning_style"] == "visual"
        assert content["metadata"]["estimated_completion_time"] > 0
        assert len(content["metadata"]["skills_targeted"]) > 0
    
    @pytest.mark.asyncio
    async def test_invalid_subject(self, engine):
        """Test handling of invalid subject"""
        with pytest.raises(Exception) as exc_info:
            await engine.generate_personalized_content(
                subject="invalid_subject",
                topic="some_topic",
                difficulty="beginner",
                user_context={}
            )
        
        assert "No content generator available" in str(exc_info.value)
    
    def test_estimate_completion_time(self, engine):
        """Test completion time estimation"""
        content = {
            "sections": [{"type": "concept"}, {"type": "example"}],
            "practice_problems": [1, 2, 3]
        }
        
        time_beginner = engine._estimate_completion_time(content, "beginner")
        time_advanced = engine._estimate_completion_time(content, "advanced")
        
        assert time_beginner < time_advanced
        assert time_beginner >= 10  # Base time for beginner
    
    def test_identify_skills(self, engine):
        """Test skill identification"""
        skills = engine._identify_skills("math", "fractions")
        
        assert isinstance(skills, list)
        assert len(skills) > 0
        assert "Number sense" in skills
    
    def test_get_prerequisites(self, engine):
        """Test prerequisite identification"""
        prereqs = engine._get_prerequisites("math", "algebra_basics")
        
        assert isinstance(prereqs, list)
        assert "arithmetic operations" in prereqs


class TestContentGeneratorFeatures:
    """Test specific features of content generators"""
    
    @pytest.mark.asyncio
    async def test_adaptive_difficulty(self):
        """Test that content adapts to difficulty levels"""
        generator = MathContentGenerator()
        
        beginner = await generator.generate(
            topic="fractions",
            difficulty="beginner",
            context={}
        )
        
        intermediate = await generator.generate(
            topic="fractions",
            difficulty="intermediate",
            context={}
        )
        
        # Intermediate should have more complex content
        assert len(intermediate["sections"]) >= len(beginner["sections"])
        
        # Check for difficulty-specific content
        beginner_has_basics = any(
            "What are Fractions?" in s.get("title", "") 
            for s in beginner["sections"]
        )
        intermediate_has_operations = any(
            "Adding Fractions" in s.get("title", "")
            for s in intermediate["sections"]
        )
        
        assert beginner_has_basics
        assert intermediate_has_operations
    
    @pytest.mark.asyncio
    async def test_learning_style_adaptation(self):
        """Test that content adapts to learning styles"""
        generator = ScienceContentGenerator()
        
        visual = await generator.generate(
            topic="matter_states",
            difficulty="beginner",
            context={"learning_style": "visual"}
        )
        
        kinesthetic = await generator.generate(
            topic="matter_states",
            difficulty="beginner",
            context={"learning_style": "kinesthetic"}
        )
        
        # Visual learners should get animations/visuals
        has_animation = any(
            s.get("type") == "animation"
            for s in visual["sections"]
        )
        
        # Kinesthetic learners should get experiments
        assert "experiments" in kinesthetic
        assert len(kinesthetic["experiments"]) > 0
    
    @pytest.mark.asyncio
    async def test_practice_problem_generation(self):
        """Test practice problem generation"""
        generator = MathContentGenerator()
        
        problems = generator._generate_fraction_problems("beginner", 3)
        
        assert len(problems) == 3
        for problem in problems:
            assert "question" in problem
            assert "correct_answer" in problem
            assert "explanation" in problem


@pytest.mark.integration
class TestContentGenerationIntegration:
    """Integration tests for content generation"""
    
    @pytest.mark.asyncio
    async def test_full_content_generation_flow(self):
        """Test complete content generation flow"""
        engine = ContentGenerationEngine()
        
        # Simulate user context from learning profile
        user_context = {
            "learning_style": "balanced",
            "performance": {
                "accuracy": 75,
                "speed": "medium"
            },
            "preferences": {
                "interactive_content": True,
                "video_content": False
            },
            "interests": ["space", "technology"],
            "grade_level": 5
        }
        
        # Generate content for different subjects
        subjects_topics = [
            ("math", "geometry"),
            ("science", "solar_system"),
            ("computer_science", "programming_basics"),
            ("history", "ancient_civilizations")
        ]
        
        for subject, topic in subjects_topics:
            content = await engine.generate_personalized_content(
                subject=subject,
                topic=topic,
                difficulty="intermediate",
                user_context=user_context
            )
            
            # Verify content structure
            assert content["topic"] == topic
            assert content["difficulty"] == "intermediate"
            assert "sections" in content
            assert "metadata" in content
            assert "adaptive_features" in content
            
            # Verify personalization
            meta = content["metadata"]
            assert meta["personalization_context"]["learning_style"] == "balanced"
            assert meta["estimated_completion_time"] > 0
            
            # Verify adaptive features
            assert content["adaptive_features"]["hint_system"] is True
            assert content["adaptive_features"]["progress_tracking"] is True