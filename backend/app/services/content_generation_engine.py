from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
import json
import random
from datetime import datetime

from app.models.learning_analytics import LearningProfile, PersonalizedContent
from app.core.exceptions import APIException


class ContentGenerator(ABC):
    """Abstract base class for content generators"""
    
    @abstractmethod
    async def generate(
        self, 
        topic: str, 
        difficulty: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate educational content for a specific topic and difficulty level.
        
        Args:
            topic: The specific topic to generate content for
            difficulty: The difficulty level (beginner, intermediate, advanced)
            context: User context including learning style, preferences, and performance
            
        Returns:
            Dict containing generated content with sections, exercises, and metadata
            
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement generate() method"
        )


class MathContentGenerator(ContentGenerator):
    """Generates personalized math content"""
    
    async def generate(
        self, 
        topic: str, 
        difficulty: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        learning_style = context.get("learning_style", "balanced")
        
        if topic == "fractions":
            return await self._generate_fractions_content(difficulty, learning_style)
        elif topic == "algebra_basics":
            return await self._generate_algebra_content(difficulty, learning_style)
        elif topic == "geometry":
            return await self._generate_geometry_content(difficulty, learning_style)
        else:
            return await self._generate_generic_math_content(topic, difficulty, learning_style)
    
    async def _generate_fractions_content(
        self, 
        difficulty: str, 
        learning_style: str
    ) -> Dict[str, Any]:
        """Generate fractions content"""
        base_content = {
            "topic": "fractions",
            "difficulty": difficulty,
            "sections": []
        }
        
        if difficulty == "beginner":
            base_content["sections"].extend([
                {
                    "type": "concept",
                    "title": "What are Fractions?",
                    "content": "A fraction represents a part of a whole. It has two parts: the numerator (top number) and denominator (bottom number).",
                    "visual": "fraction_parts_diagram.svg",
                    "interactive": learning_style in ["kinesthetic", "visual"]
                },
                {
                    "type": "example",
                    "title": "Pizza Slices",
                    "content": "If a pizza is cut into 8 slices and you eat 3, you've eaten 3/8 of the pizza.",
                    "visual": "pizza_fraction.svg",
                    "practice": {
                        "question": "If you eat 2 more slices, what fraction have you eaten in total?",
                        "answer": "5/8",
                        "explanation": "3 slices + 2 slices = 5 slices out of 8 total"
                    }
                }
            ])
            
            if learning_style == "visual":
                base_content["sections"].append({
                    "type": "animation",
                    "title": "Fraction Visualization",
                    "content": "Watch how fractions represent parts of shapes",
                    "animation_url": "/animations/fractions_visual.mp4"
                })
            
        elif difficulty == "intermediate":
            base_content["sections"].extend([
                {
                    "type": "concept",
                    "title": "Adding Fractions",
                    "content": "To add fractions with the same denominator, add the numerators and keep the denominator.",
                    "formula": "a/c + b/c = (a+b)/c",
                    "steps": [
                        "Check if denominators are the same",
                        "Add the numerators",
                        "Keep the denominator",
                        "Simplify if possible"
                    ]
                },
                {
                    "type": "worked_example",
                    "problem": "Calculate: 2/5 + 1/5",
                    "solution_steps": [
                        {"step": "Denominators are the same (5)", "result": "✓"},
                        {"step": "Add numerators: 2 + 1 = 3", "result": "3"},
                        {"step": "Keep denominator: 5", "result": "3/5"},
                        {"step": "Check if we can simplify", "result": "3/5 is already simplified"}
                    ]
                }
            ])
        
        # Add practice problems
        base_content["practice_problems"] = self._generate_fraction_problems(difficulty, 3)
        
        return base_content
    
    async def _generate_algebra_content(
        self, 
        difficulty: str, 
        learning_style: str
    ) -> Dict[str, Any]:
        """Generate algebra content"""
        content = {
            "topic": "algebra_basics",
            "difficulty": difficulty,
            "sections": []
        }
        
        if difficulty == "beginner":
            content["sections"] = [
                {
                    "type": "concept",
                    "title": "Introduction to Variables",
                    "content": "A variable is a letter that represents an unknown number. We use variables to write mathematical expressions.",
                    "examples": ["x + 5 = 10", "2y = 14", "a - 3 = 7"],
                    "visual": learning_style == "visual"
                },
                {
                    "type": "interactive",
                    "title": "Variable Explorer",
                    "content": "Drag different values to see how they affect the equation",
                    "interactive_type": "equation_solver",
                    "equation": "x + 3 = 8"
                }
            ]
        
        return content
    
    async def _generate_geometry_content(
        self, 
        difficulty: str, 
        learning_style: str
    ) -> Dict[str, Any]:
        """Generate geometry content"""
        return {
            "topic": "geometry",
            "difficulty": difficulty,
            "sections": [
                {
                    "type": "concept",
                    "title": "Basic Shapes",
                    "content": "Learn about different geometric shapes and their properties",
                    "interactive": True,
                    "visual": True
                }
            ]
        }
    
    async def _generate_generic_math_content(
        self, 
        topic: str, 
        difficulty: str, 
        learning_style: str
    ) -> Dict[str, Any]:
        """Generate generic math content for any topic"""
        return {
            "topic": topic,
            "difficulty": difficulty,
            "sections": [
                {
                    "type": "concept",
                    "title": f"Understanding {topic}",
                    "content": f"Introduction to {topic} concepts",
                    "adaptive": True
                }
            ]
        }
    
    def _generate_fraction_problems(
        self, 
        difficulty: str, 
        count: int
    ) -> List[Dict[str, Any]]:
        """Generate fraction practice problems"""
        problems = []
        
        if difficulty == "beginner":
            # Simple fraction identification
            for i in range(count):
                numerator = random.randint(1, 5)
                denominator = random.randint(numerator + 1, 10)
                problems.append({
                    "id": i + 1,
                    "type": "multiple_choice",
                    "question": f"What fraction is shown? {numerator} parts out of {denominator} total parts",
                    "options": [
                        f"{numerator}/{denominator}",
                        f"{denominator}/{numerator}",
                        f"{numerator + 1}/{denominator}",
                        f"{numerator}/{denominator + 1}"
                    ],
                    "correct_answer": 0,
                    "explanation": f"The fraction is {numerator}/{denominator} because we have {numerator} parts selected out of {denominator} total parts."
                })
        
        elif difficulty == "intermediate":
            # Fraction addition
            for i in range(count):
                denominator = random.choice([4, 5, 8, 10])
                num1 = random.randint(1, denominator - 1)
                num2 = random.randint(1, denominator - num1)
                answer = num1 + num2
                
                problems.append({
                    "id": i + 1,
                    "type": "fill_in_blank",
                    "question": f"Calculate: {num1}/{denominator} + {num2}/{denominator} = ___",
                    "correct_answer": f"{answer}/{denominator}",
                    "hints": [
                        "The denominators are the same",
                        f"Add the numerators: {num1} + {num2}",
                        "Keep the same denominator"
                    ],
                    "explanation": f"When denominators are the same, add numerators: {num1} + {num2} = {answer}, so the answer is {answer}/{denominator}"
                })
        
        return problems


class ScienceContentGenerator(ContentGenerator):
    """Generates personalized science content"""
    
    async def generate(
        self, 
        topic: str, 
        difficulty: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        learning_style = context.get("learning_style", "balanced")
        
        content = {
            "topic": topic,
            "difficulty": difficulty,
            "sections": []
        }
        
        if topic == "matter_states":
            content["sections"] = await self._generate_matter_states_content(difficulty, learning_style)
        elif topic == "photosynthesis":
            content["sections"] = await self._generate_photosynthesis_content(difficulty, learning_style)
        elif topic == "solar_system":
            content["sections"] = await self._generate_solar_system_content(difficulty, learning_style)
        
        # Add experiments for kinesthetic learners
        if learning_style == "kinesthetic":
            content["experiments"] = self._generate_experiments(topic, difficulty)
        
        return content
    
    async def _generate_matter_states_content(
        self, 
        difficulty: str, 
        learning_style: str
    ) -> List[Dict[str, Any]]:
        """Generate content about states of matter"""
        sections = []
        
        if difficulty == "beginner":
            sections.extend([
                {
                    "type": "concept",
                    "title": "Three States of Matter",
                    "content": "Matter exists in three main states: solid, liquid, and gas",
                    "characteristics": {
                        "solid": ["Fixed shape", "Fixed volume", "Particles tightly packed"],
                        "liquid": ["No fixed shape", "Fixed volume", "Particles can move"],
                        "gas": ["No fixed shape", "No fixed volume", "Particles move freely"]
                    },
                    "visual": "states_of_matter_diagram.svg"
                },
                {
                    "type": "real_world_examples",
                    "title": "Examples Around Us",
                    "examples": [
                        {"state": "solid", "items": ["Ice", "Rock", "Wood"]},
                        {"state": "liquid", "items": ["Water", "Milk", "Oil"]},
                        {"state": "gas", "items": ["Air", "Steam", "Oxygen"]}
                    ]
                }
            ])
            
            if learning_style == "visual":
                sections.append({
                    "type": "animation",
                    "title": "Particle Movement",
                    "content": "See how particles move in different states",
                    "animation_url": "/animations/particle_movement.mp4"
                })
        
        return sections
    
    async def _generate_photosynthesis_content(
        self, 
        difficulty: str, 
        learning_style: str
    ) -> List[Dict[str, Any]]:
        """Generate photosynthesis content"""
        return [
            {
                "type": "concept",
                "title": "How Plants Make Food",
                "content": "Photosynthesis is the process plants use to make their own food using sunlight",
                "equation": "CO2 + H2O + Sunlight → Glucose + O2",
                "visual": learning_style in ["visual", "balanced"]
            }
        ]
    
    async def _generate_solar_system_content(
        self, 
        difficulty: str, 
        learning_style: str
    ) -> List[Dict[str, Any]]:
        """Generate solar system content"""
        return [
            {
                "type": "interactive",
                "title": "Solar System Explorer",
                "content": "Explore the planets in our solar system",
                "interactive_type": "3d_model",
                "model_url": "/models/solar_system.glb"
            }
        ]
    
    def _generate_experiments(
        self, 
        topic: str, 
        difficulty: str
    ) -> List[Dict[str, Any]]:
        """Generate hands-on experiments"""
        experiments = {
            "matter_states": [
                {
                    "title": "Ice Melting Experiment",
                    "materials": ["Ice cubes", "Bowl", "Timer"],
                    "steps": [
                        "Place ice cubes in a bowl",
                        "Observe and record changes every 5 minutes",
                        "Note when ice completely melts"
                    ],
                    "learning_outcome": "Observe solid to liquid state change"
                }
            ],
            "photosynthesis": [
                {
                    "title": "Plant in Light vs Dark",
                    "materials": ["2 small plants", "Box", "Water"],
                    "steps": [
                        "Place one plant in sunlight",
                        "Place another in a dark box",
                        "Water both equally for a week",
                        "Compare their growth"
                    ],
                    "learning_outcome": "Understand importance of light for plants"
                }
            ]
        }
        
        return experiments.get(topic, [])


class LanguageContentGenerator(ContentGenerator):
    """Generates personalized language/reading content"""
    
    async def generate(
        self, 
        topic: str, 
        difficulty: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        learning_style = context.get("learning_style", "balanced")
        interests = context.get("interests", ["general"])
        
        content = {
            "topic": topic,
            "difficulty": difficulty,
            "sections": []
        }
        
        if topic == "reading_comprehension":
            content = await self._generate_reading_content(difficulty, interests)
        elif topic == "vocabulary":
            content = await self._generate_vocabulary_content(difficulty, learning_style)
        elif topic == "grammar":
            content = await self._generate_grammar_content(difficulty, learning_style)
        
        return content
    
    async def _generate_reading_content(
        self, 
        difficulty: str, 
        interests: List[str]
    ) -> Dict[str, Any]:
        """Generate reading comprehension content"""
        # Select passage based on interests
        theme = interests[0] if interests else "adventure"
        
        passages = {
            "beginner": {
                "adventure": {
                    "title": "The Hidden Treasure",
                    "text": "Sam found an old map in her grandmother's attic. The map showed a path through the forest to a hidden treasure. She packed her backpack with water, snacks, and a flashlight. Following the map carefully, Sam discovered a small wooden box under an old oak tree. Inside was her grandmother's childhood diary - a real treasure!",
                    "questions": [
                        {
                            "question": "Where did Sam find the map?",
                            "options": ["In the forest", "In her grandmother's attic", "Under a tree", "In a box"],
                            "correct": 1
                        },
                        {
                            "question": "What was the real treasure?",
                            "options": ["Gold coins", "A flashlight", "Grandmother's diary", "An old map"],
                            "correct": 2
                        }
                    ]
                }
            }
        }
        
        passage_data = passages.get(difficulty, {}).get(theme, passages["beginner"]["adventure"])
        
        return {
            "topic": "reading_comprehension",
            "difficulty": difficulty,
            "passage": passage_data,
            "skills_practiced": ["Main idea", "Details", "Inference", "Vocabulary in context"]
        }
    
    async def _generate_vocabulary_content(
        self, 
        difficulty: str, 
        learning_style: str
    ) -> Dict[str, Any]:
        """Generate vocabulary content"""
        words = {
            "beginner": [
                {
                    "word": "enormous",
                    "definition": "very large in size",
                    "synonyms": ["huge", "gigantic", "massive"],
                    "example": "The enormous elephant amazed the children.",
                    "visual": "enormous_comparison.svg"
                },
                {
                    "word": "ancient",
                    "definition": "very old, from long ago",
                    "synonyms": ["old", "historic", "antique"],
                    "example": "The ancient pyramid was built thousands of years ago.",
                    "visual": "ancient_timeline.svg"
                }
            ]
        }
        
        content = {
            "topic": "vocabulary",
            "difficulty": difficulty,
            "words": words.get(difficulty, words["beginner"]),
            "activities": []
        }
        
        if learning_style == "kinesthetic":
            content["activities"].append({
                "type": "word_sort",
                "instructions": "Sort words into categories",
                "interactive": True
            })
        elif learning_style == "visual":
            content["activities"].append({
                "type": "picture_match",
                "instructions": "Match words with pictures",
                "visual": True
            })
        
        return content
    
    async def _generate_grammar_content(
        self, 
        difficulty: str, 
        learning_style: str
    ) -> Dict[str, Any]:
        """Generate grammar content"""
        return {
            "topic": "grammar",
            "difficulty": difficulty,
            "sections": [
                {
                    "type": "rule",
                    "title": "Subject-Verb Agreement",
                    "rule": "The subject and verb must agree in number",
                    "examples": [
                        {"correct": "The dog runs fast", "incorrect": "The dog run fast"},
                        {"correct": "The dogs run fast", "incorrect": "The dogs runs fast"}
                    ],
                    "practice": self._generate_grammar_exercises(difficulty)
                }
            ]
        }
    
    def _generate_grammar_exercises(self, difficulty: str) -> List[Dict[str, Any]]:
        """Generate grammar practice exercises"""
        return [
            {
                "type": "fill_in_blank",
                "sentence": "The cat ___ on the mat.",
                "options": ["sit", "sits"],
                "correct": 1,
                "explanation": "'Cat' is singular, so we use 'sits'"
            }
        ]


class ContentGenerationEngine:
    """Main engine for generating personalized content"""
    
    def __init__(self):
        self.generators = {
            "math": MathContentGenerator(),
            "science": ScienceContentGenerator(),
            "language": LanguageContentGenerator(),
            "reading": LanguageContentGenerator()
        }
        
        # Import and register additional generators
        try:
            from app.services.content_generators import register_additional_generators
            register_additional_generators(self)
        except ImportError:
            # Additional generators not available
            pass
    
    async def generate_personalized_content(
        self,
        subject: str,
        topic: str,
        difficulty: str,
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate personalized content based on subject and user context"""
        
        generator = self.generators.get(subject)
        if not generator:
            raise APIException(
                status_code=400,
                detail=f"No content generator available for subject: {subject}"
            )
        
        # Generate base content
        content = await generator.generate(topic, difficulty, user_context)
        
        # Add metadata
        content["metadata"] = {
            "generated_at": datetime.utcnow().isoformat(),
            "personalization_context": {
                "learning_style": user_context.get("learning_style"),
                "performance_level": user_context.get("performance", {}).get("accuracy", 0),
                "preferences": user_context.get("preferences", [])
            },
            "estimated_completion_time": self._estimate_completion_time(content, difficulty),
            "skills_targeted": self._identify_skills(subject, topic),
            "prerequisites": self._get_prerequisites(subject, topic)
        }
        
        # Add adaptive elements
        content["adaptive_features"] = {
            "hint_system": True,
            "difficulty_adjustment": True,
            "progress_tracking": True,
            "instant_feedback": True
        }
        
        return content
    
    def _estimate_completion_time(
        self, 
        content: Dict[str, Any], 
        difficulty: str
    ) -> int:
        """Estimate time to complete content in minutes"""
        base_time = {
            "beginner": 10,
            "intermediate": 15,
            "advanced": 20
        }.get(difficulty, 15)
        
        # Adjust based on content sections
        sections = content.get("sections", [])
        time_multiplier = 1 + (len(sections) * 0.2)
        
        # Add time for practice problems
        if "practice_problems" in content:
            base_time += len(content["practice_problems"]) * 2
        
        return int(base_time * time_multiplier)
    
    def _identify_skills(self, subject: str, topic: str) -> List[str]:
        """Identify skills targeted by the content"""
        skill_map = {
            "math": {
                "fractions": ["Number sense", "Part-whole relationships", "Mathematical reasoning"],
                "algebra_basics": ["Abstract thinking", "Problem solving", "Pattern recognition"],
                "geometry": ["Spatial reasoning", "Visual thinking", "Measurement"]
            },
            "science": {
                "matter_states": ["Observation", "Classification", "Scientific thinking"],
                "photosynthesis": ["Systems thinking", "Process understanding", "Cause and effect"],
                "solar_system": ["Scale comprehension", "Spatial awareness", "Data interpretation"]
            },
            "language": {
                "reading_comprehension": ["Text analysis", "Inference", "Critical thinking"],
                "vocabulary": ["Word knowledge", "Context clues", "Language expansion"],
                "grammar": ["Language structure", "Rule application", "Communication"]
            }
        }
        
        return skill_map.get(subject, {}).get(topic, ["General learning skills"])
    
    def _get_prerequisites(self, subject: str, topic: str) -> List[str]:
        """Get prerequisite topics"""
        prerequisites = {
            "math": {
                "fractions": ["counting", "division concepts"],
                "algebra_basics": ["arithmetic operations", "number patterns"],
                "geometry": ["shapes recognition", "measurement basics"]
            },
            "science": {
                "matter_states": ["observation skills", "basic classification"],
                "photosynthesis": ["plant parts", "basic chemistry"],
                "solar_system": ["Earth and sky", "day and night"]
            },
            "language": {
                "reading_comprehension": ["basic reading", "vocabulary"],
                "vocabulary": ["phonics", "word recognition"],
                "grammar": ["sentence structure", "parts of speech"]
            }
        }
        
        return prerequisites.get(subject, {}).get(topic, [])