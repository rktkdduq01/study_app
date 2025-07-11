import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models.user import User, UserRole
from app.models.character import Character, SubjectLevel, SubjectType
from app.models.achievement import Achievement, UserAchievement, AchievementCategory, AchievementRarity
from app.models.quest import Quest, QuestProgress, QuestType, QuestDifficulty, QuestStatus
from app.core.security import get_password_hash, create_token_pair
import asyncio
from unittest.mock import Mock, patch


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """Create a test client with overridden database"""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# User fixtures
@pytest.fixture
def test_user(db: Session) -> User:
    """Create a test user"""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Test User",
        role=UserRole.STUDENT,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_admin_user(db: Session) -> User:
    """Create a test admin user"""
    admin = User(
        username="admin",
        email="admin@example.com",
        hashed_password=get_password_hash("adminpassword"),
        full_name="Admin User",
        role=UserRole.ADMIN,
        is_active=True
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


@pytest.fixture
def test_user_token_headers(test_user: User) -> dict:
    """Create authorization headers for test user"""
    access_token, _ = create_token_pair(
        data={"sub": test_user.username}
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def admin_token_headers(test_admin_user: User) -> dict:
    """Create authorization headers for admin user"""
    access_token, _ = create_token_pair(
        data={"sub": test_admin_user.username}
    )
    return {"Authorization": f"Bearer {access_token}"}


# Character fixtures
@pytest.fixture
def test_character(db: Session, test_user: User) -> Character:
    """Create a test character"""
    character = Character(
        user_id=test_user.id,
        name="TestHero",
        avatar_url="https://example.com/avatar.png",
        total_level=1,
        total_experience=0,
        coins=0,
        gems=0
    )
    db.add(character)
    db.commit()
    db.refresh(character)
    
    # Initialize subject levels
    for subject in SubjectType:
        subject_level = SubjectLevel(
            character_id=character.id,
            subject=subject.value,
            level=1,
            experience=0,
            exp_to_next_level=100
        )
        db.add(subject_level)
    
    db.commit()
    db.refresh(character)
    return character


@pytest.fixture
def test_characters_for_ranking(db: Session) -> list[Character]:
    """Create multiple characters for ranking tests"""
    characters = []
    for i in range(5):
        user = User(
            username=f"rankuser{i}",
            email=f"rank{i}@example.com",
            hashed_password=get_password_hash("password"),
            full_name=f"Rank User {i}",
            is_active=True
        )
        db.add(user)
        db.commit()
        
        character = Character(
            user_id=user.id,
            name=f"RankHero{i}",
            total_level=i + 1,
            total_experience=i * 100,
            coins=i * 50,
            gems=i * 10
        )
        db.add(character)
        characters.append(character)
    
    db.commit()
    return characters


# Achievement fixtures
@pytest.fixture
def test_achievement(db: Session) -> Achievement:
    """Create a test achievement"""
    achievement = Achievement(
        name="First Steps",
        description="Complete your first quest",
        category=AchievementCategory.QUEST,
        rarity=AchievementRarity.COMMON,
        points=10,
        max_progress=1,
        is_active=True
    )
    db.add(achievement)
    db.commit()
    db.refresh(achievement)
    return achievement


@pytest.fixture
def test_achievements(db: Session) -> list[Achievement]:
    """Create multiple test achievements"""
    achievements_data = [
        {
            "name": "Novice Learner",
            "description": "Complete 10 easy quests",
            "category": AchievementCategory.LEARNING,
            "rarity": AchievementRarity.COMMON,
            "points": 20,
            "max_progress": 10
        },
        {
            "name": "Streak Master",
            "description": "Maintain a 7-day streak",
            "category": AchievementCategory.STREAK,
            "rarity": AchievementRarity.RARE,
            "points": 50,
            "max_progress": 7
        },
        {
            "name": "Quest Champion",
            "description": "Complete 50 quests",
            "category": AchievementCategory.QUEST,
            "rarity": AchievementRarity.EPIC,
            "points": 100,
            "max_progress": 50
        }
    ]
    
    achievements = []
    for data in achievements_data:
        achievement = Achievement(**data, is_active=True)
        db.add(achievement)
        achievements.append(achievement)
    
    db.commit()
    return achievements


@pytest.fixture
def test_achievements_for_triggers(db: Session) -> list[Achievement]:
    """Create achievements with trigger requirements"""
    achievement = Achievement(
        name="Quest Beginner",
        description="Complete any quest",
        category=AchievementCategory.QUEST,
        rarity=AchievementRarity.COMMON,
        points=10,
        max_progress=1,
        requirements={
            "trigger_type": "quest_completed"
        },
        is_active=True
    )
    db.add(achievement)
    db.commit()
    return [achievement]


@pytest.fixture
def test_user_achievement(
    db: Session, 
    test_user: User, 
    test_achievement: Achievement
) -> UserAchievement:
    """Create a test user achievement"""
    user_achievement = UserAchievement(
        user_id=test_user.id,
        achievement_id=test_achievement.id,
        progress=0,
        is_completed=False
    )
    db.add(user_achievement)
    db.commit()
    db.refresh(user_achievement)
    return user_achievement


@pytest.fixture
def test_user_with_achievements(
    db: Session,
    test_user: User,
    test_achievements: list[Achievement]
) -> User:
    """Create a user with some completed achievements"""
    for i, achievement in enumerate(test_achievements[:2]):
        user_achievement = UserAchievement(
            user_id=test_user.id,
            achievement_id=achievement.id,
            progress=achievement.max_progress,
            is_completed=True
        )
        db.add(user_achievement)
    
    db.commit()
    db.refresh(test_user)
    return test_user


# Quest fixtures
@pytest.fixture
def test_quest(db: Session) -> Quest:
    """Create a test quest"""
    quest = Quest(
        title="Basic Math Problems",
        description="Solve basic addition problems",
        quest_type=QuestType.DAILY,
        difficulty=QuestDifficulty.EASY,
        subject="math",
        objectives=[{"type": "solve", "count": 5}],
        exp_reward=100,
        coin_reward=50,
        gem_reward=0,
        time_limit_minutes=30,
        min_level=1,
        is_active=True
    )
    db.add(quest)
    db.commit()
    db.refresh(quest)
    return quest


@pytest.fixture
def test_quests(db: Session) -> list[Quest]:
    """Create multiple test quests"""
    quests_data = [
        {
            "title": "Easy Math Quest",
            "description": "Simple addition",
            "quest_type": QuestType.DAILY,
            "difficulty": QuestDifficulty.EASY,
            "subject": "math",
            "exp_reward": 50,
            "coin_reward": 25
        },
        {
            "title": "Science Challenge",
            "description": "Basic science questions",
            "quest_type": QuestType.WEEKLY,
            "difficulty": QuestDifficulty.MEDIUM,
            "subject": "science",
            "exp_reward": 150,
            "coin_reward": 75
        },
        {
            "title": "Language Master",
            "description": "Advanced language skills",
            "quest_type": QuestType.SPECIAL,
            "difficulty": QuestDifficulty.HARD,
            "subject": "korean",
            "exp_reward": 300,
            "coin_reward": 150,
            "gem_reward": 10
        }
    ]
    
    quests = []
    for data in quests_data:
        quest = Quest(
            **data,
            objectives=[{"type": "complete"}],
            min_level=1,
            is_active=True
        )
        db.add(quest)
        quests.append(quest)
    
    db.commit()
    return quests


@pytest.fixture
def test_daily_quests(db: Session) -> list[Quest]:
    """Create daily quests"""
    daily_quests = []
    for i in range(3):
        quest = Quest(
            title=f"Daily Quest {i+1}",
            description=f"Daily quest number {i+1}",
            quest_type=QuestType.DAILY,
            difficulty=QuestDifficulty.EASY,
            subject="math",
            objectives=[{"type": "solve", "count": 3}],
            exp_reward=50,
            coin_reward=25,
            min_level=1,
            is_active=True
        )
        db.add(quest)
        daily_quests.append(quest)
    
    db.commit()
    return daily_quests


@pytest.fixture
def test_quest_with_prerequisites(
    db: Session, 
    test_quest: Quest
) -> Quest:
    """Create a quest with prerequisites"""
    advanced_quest = Quest(
        title="Advanced Quest",
        description="Requires completion of basic quest",
        quest_type=QuestType.SPECIAL,
        difficulty=QuestDifficulty.HARD,
        subject="math",
        objectives=[{"type": "solve", "count": 10}],
        exp_reward=500,
        coin_reward=250,
        gem_reward=20,
        min_level=5,
        prerequisites=[test_quest.id],
        is_active=True
    )
    db.add(advanced_quest)
    db.commit()
    db.refresh(advanced_quest)
    return advanced_quest


@pytest.fixture
def test_quest_progress(
    db: Session,
    test_user: User,
    test_quest: Quest
) -> QuestProgress:
    """Create a test quest progress"""
    progress = QuestProgress(
        user_id=test_user.id,
        quest_id=test_quest.id,
        status=QuestStatus.IN_PROGRESS,
        progress={},
        attempts=1
    )
    db.add(progress)
    db.commit()
    db.refresh(progress)
    return progress


@pytest.fixture
def test_quest_progress_with_time_limit(
    db: Session,
    test_user: User
) -> QuestProgress:
    """Create quest progress with time limit"""
    quest = Quest(
        title="Timed Quest",
        description="Quest with time limit",
        quest_type=QuestType.CHALLENGE,
        difficulty=QuestDifficulty.MEDIUM,
        subject="math",
        objectives=[{"type": "solve"}],
        exp_reward=200,
        coin_reward=100,
        time_limit_minutes=60,
        min_level=1,
        is_active=True
    )
    db.add(quest)
    db.commit()
    
    progress = QuestProgress(
        user_id=test_user.id,
        quest_id=quest.id,
        status=QuestStatus.IN_PROGRESS,
        progress={},
        attempts=1
    )
    db.add(progress)
    db.commit()
    db.refresh(progress)
    return progress


@pytest.fixture
def test_quests_for_recommendation(
    db: Session,
    test_character: Character
) -> list[Quest]:
    """Create quests for recommendation testing"""
    quests = []
    difficulties = [
        QuestDifficulty.EASY,
        QuestDifficulty.MEDIUM,
        QuestDifficulty.HARD
    ]
    
    for i, difficulty in enumerate(difficulties):
        quest = Quest(
            title=f"Recommended Quest {i+1}",
            description=f"Quest for recommendation {i+1}",
            quest_type=QuestType.DAILY,
            difficulty=difficulty,
            subject="math",
            objectives=[{"type": "solve"}],
            exp_reward=100 * (i + 1),
            coin_reward=50 * (i + 1),
            min_level=1,
            is_active=True
        )
        db.add(quest)
        quests.append(quest)
    
    db.commit()
    return quests


@pytest.fixture
def test_user_with_quest_history(
    db: Session,
    test_user: User,
    test_quests: list[Quest]
) -> User:
    """Create a user with quest completion history"""
    for i, quest in enumerate(test_quests[:2]):
        progress = QuestProgress(
            user_id=test_user.id,
            quest_id=quest.id,
            status=QuestStatus.COMPLETED,
            progress={"final_score": 85 + i * 5},
            attempts=1
        )
        db.add(progress)
    
    # Add one in-progress quest
    progress = QuestProgress(
        user_id=test_user.id,
        quest_id=test_quests[2].id,
        status=QuestStatus.IN_PROGRESS,
        progress={},
        attempts=1
    )
    db.add(progress)
    
    db.commit()
    db.refresh(test_user)
    return test_user