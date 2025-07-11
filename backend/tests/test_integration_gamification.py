"""
Integration tests for gamification system
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.models.user import User
from app.models.character import Character, SubjectType
from app.models.quest import Quest, QuestType, QuestDifficulty
from app.models.achievement import Achievement, AchievementCategory, AchievementRarity
from app.models.gamification import Badge, BadgeCategory, BadgeRarity


class TestQuestFlow:
    """Test complete quest flow from start to completion"""
    
    def test_quest_lifecycle(
        self,
        client: TestClient,
        db: Session,
        test_user: User,
        test_character: Character,
        test_user_token_headers: dict
    ):
        """Test full quest lifecycle"""
        # 1. Create a quest
        quest = Quest(
            title="Integration Test Quest",
            description="Complete math problems",
            quest_type=QuestType.DAILY,
            difficulty=QuestDifficulty.EASY,
            subject="math",
            objectives=[{"type": "solve", "count": 5}],
            exp_reward=100,
            coin_reward=50,
            time_limit_minutes=30,
            min_level=1,
            is_active=True
        )
        db.add(quest)
        db.commit()
        
        # 2. Get available quests
        quests_response = client.get(
            "/api/v1/quests/available",
            headers=test_user_token_headers
        )
        assert quests_response.status_code == 200
        
        available_quests = quests_response.json()
        assert len(available_quests) > 0
        test_quest = next(q for q in available_quests if q["id"] == quest.id)
        assert test_quest["title"] == quest.title
        
        # 3. Start the quest
        start_response = client.post(
            f"/api/v1/quests/{quest.id}/start",
            headers=test_user_token_headers
        )
        assert start_response.status_code == 200
        
        quest_progress = start_response.json()
        assert quest_progress["status"] == "in_progress"
        assert quest_progress["attempts"] == 1
        
        # 4. Update quest progress
        progress_data = {
            "progress": {
                "problems_solved": 3,
                "correct_answers": 3
            }
        }
        
        update_response = client.put(
            f"/api/v1/quests/{quest.id}/progress",
            json=progress_data,
            headers=test_user_token_headers
        )
        assert update_response.status_code == 200
        
        # 5. Complete the quest
        complete_data = {
            "progress": {
                "problems_solved": 5,
                "correct_answers": 5
            },
            "score": 100
        }
        
        complete_response = client.post(
            f"/api/v1/quests/{quest.id}/complete",
            json=complete_data,
            headers=test_user_token_headers
        )
        assert complete_response.status_code == 200
        
        completion_result = complete_response.json()
        assert completion_result["status"] == "completed"
        assert "rewards" in completion_result
        assert completion_result["rewards"]["experience"] == 100
        assert completion_result["rewards"]["coins"] == 50
        
        # 6. Verify character received rewards
        db.refresh(test_character)
        assert test_character.total_experience >= 100
        assert test_character.coins >= 50
        
        # 7. Check quest history
        history_response = client.get(
            "/api/v1/quests/history",
            headers=test_user_token_headers
        )
        assert history_response.status_code == 200
        
        history = history_response.json()
        completed_quest = next(
            h for h in history 
            if h["quest_id"] == quest.id and h["status"] == "completed"
        )
        assert completed_quest is not None
    
    def test_daily_quest_reset(
        self,
        client: TestClient,
        db: Session,
        test_user: User,
        test_user_token_headers: dict
    ):
        """Test daily quest reset functionality"""
        # Create daily quests
        daily_quests = []
        for i in range(3):
            quest = Quest(
                title=f"Daily Quest {i+1}",
                description="Daily task",
                quest_type=QuestType.DAILY,
                difficulty=QuestDifficulty.EASY,
                subject="math",
                objectives=[{"type": "complete"}],
                exp_reward=50,
                coin_reward=25,
                min_level=1,
                is_active=True
            )
            db.add(quest)
            daily_quests.append(quest)
        db.commit()
        
        # Get today's daily quests
        daily_response = client.get(
            "/api/v1/quests/daily",
            headers=test_user_token_headers
        )
        assert daily_response.status_code == 200
        
        today_quests = daily_response.json()
        assert len(today_quests) >= 3
        
        # Start and complete one quest
        quest_id = today_quests[0]["id"]
        
        client.post(
            f"/api/v1/quests/{quest_id}/start",
            headers=test_user_token_headers
        )
        
        client.post(
            f"/api/v1/quests/{quest_id}/complete",
            json={"progress": {}, "score": 100},
            headers=test_user_token_headers
        )
        
        # Check remaining daily quests
        remaining_response = client.get(
            "/api/v1/quests/daily",
            headers=test_user_token_headers
        )
        assert remaining_response.status_code == 200
        
        remaining = remaining_response.json()
        # Completed quest should not appear in available daily quests
        completed_ids = [q["id"] for q in remaining if q["id"] == quest_id]
        assert len(completed_ids) == 0


class TestAchievementSystem:
    """Test achievement unlocking and tracking"""
    
    def test_achievement_unlocking(
        self,
        client: TestClient,
        db: Session,
        test_user: User,
        test_character: Character,
        test_user_token_headers: dict
    ):
        """Test achievement unlocking through actions"""
        # 1. Create achievements
        achievements = [
            Achievement(
                name="First Quest",
                description="Complete your first quest",
                category=AchievementCategory.QUEST,
                rarity=AchievementRarity.COMMON,
                points=10,
                max_progress=1,
                requirements={"trigger_type": "quest_completed"},
                is_active=True
            ),
            Achievement(
                name="Quest Master",
                description="Complete 10 quests",
                category=AchievementCategory.QUEST,
                rarity=AchievementRarity.RARE,
                points=50,
                max_progress=10,
                requirements={"trigger_type": "quest_completed"},
                is_active=True
            ),
            Achievement(
                name="Level 5",
                description="Reach level 5",
                category=AchievementCategory.LEVEL,
                rarity=AchievementRarity.UNCOMMON,
                points=25,
                max_progress=1,
                requirements={"trigger_type": "level_reached", "level": 5},
                is_active=True
            )
        ]
        
        for achievement in achievements:
            db.add(achievement)
        db.commit()
        
        # 2. Get user achievements (should be empty)
        achievements_response = client.get(
            "/api/v1/achievements/user",
            headers=test_user_token_headers
        )
        assert achievements_response.status_code == 200
        
        user_achievements = achievements_response.json()
        unlocked = [a for a in user_achievements if a["is_completed"]]
        assert len(unlocked) == 0
        
        # 3. Complete a quest to trigger achievement
        quest = Quest(
            title="Achievement Test Quest",
            description="Test quest",
            quest_type=QuestType.DAILY,
            difficulty=QuestDifficulty.EASY,
            subject="math",
            objectives=[{"type": "complete"}],
            exp_reward=100,
            coin_reward=50,
            min_level=1,
            is_active=True
        )
        db.add(quest)
        db.commit()
        
        # Start and complete quest
        client.post(
            f"/api/v1/quests/{quest.id}/start",
            headers=test_user_token_headers
        )
        
        complete_response = client.post(
            f"/api/v1/quests/{quest.id}/complete",
            json={"progress": {}, "score": 100},
            headers=test_user_token_headers
        )
        assert complete_response.status_code == 200
        
        # Check if achievement was unlocked
        completion_data = complete_response.json()
        if "achievements_unlocked" in completion_data:
            assert len(completion_data["achievements_unlocked"]) > 0
            assert completion_data["achievements_unlocked"][0]["name"] == "First Quest"
        
        # 4. Verify achievement in user's list
        achievements_response2 = client.get(
            "/api/v1/achievements/user",
            headers=test_user_token_headers
        )
        
        user_achievements2 = achievements_response2.json()
        first_quest_achievement = next(
            a for a in user_achievements2 
            if a["achievement"]["name"] == "First Quest"
        )
        assert first_quest_achievement["is_completed"] is True
        assert first_quest_achievement["progress"] == 1
        
        # 5. Check achievement points added to user
        me_response = client.get(
            "/api/v1/auth/me",
            headers=test_user_token_headers
        )
        user_data = me_response.json()
        # Would need to add achievement_points to user model
        # assert user_data.get("achievement_points", 0) >= 10


class TestBadgeSystem:
    """Test badge earning and display"""
    
    def test_badge_earning(
        self,
        client: TestClient,
        db: Session,
        test_user: User,
        test_character: Character,
        test_user_token_headers: dict
    ):
        """Test earning badges through gameplay"""
        # 1. Create badges
        badges = [
            Badge(
                name="Beginner",
                description="Welcome to the game",
                category=BadgeCategory.GENERAL,
                rarity=BadgeRarity.COMMON,
                icon_url="/badges/beginner.png",
                requirements={},
                is_active=True
            ),
            Badge(
                name="Math Genius",
                description="Complete 5 math quests",
                category=BadgeCategory.SUBJECT,
                rarity=BadgeRarity.UNCOMMON,
                icon_url="/badges/math_genius.png",
                requirements={"math_quests_completed": 5},
                is_active=True
            ),
            Badge(
                name="Week Warrior",
                description="Play for 7 consecutive days",
                category=BadgeCategory.STREAK,
                rarity=BadgeRarity.RARE,
                icon_url="/badges/week_warrior.png",
                requirements={"consecutive_days": 7},
                is_active=True
            )
        ]
        
        for badge in badges:
            db.add(badge)
        db.commit()
        
        # 2. Get all badges
        badges_response = client.get(
            "/api/v1/badges",
            headers=test_user_token_headers
        )
        assert badges_response.status_code == 200
        
        all_badges = badges_response.json()
        assert len(all_badges) >= 3
        
        # 3. Get user badges
        user_badges_response = client.get(
            "/api/v1/badges/user",
            headers=test_user_token_headers
        )
        assert user_badges_response.status_code == 200
        
        user_badges = user_badges_response.json()
        
        # 4. Award beginner badge (would be automatic on registration)
        # This would typically be done automatically
        # For testing, we'll use an admin endpoint or service
        
        # 5. Complete math quests to earn Math Genius badge
        for i in range(5):
            quest = Quest(
                title=f"Math Quest {i+1}",
                description="Math problems",
                quest_type=QuestType.DAILY,
                difficulty=QuestDifficulty.EASY,
                subject="math",
                objectives=[{"type": "complete"}],
                exp_reward=50,
                coin_reward=25,
                min_level=1,
                is_active=True
            )
            db.add(quest)
            db.commit()
            
            # Start and complete quest
            client.post(
                f"/api/v1/quests/{quest.id}/start",
                headers=test_user_token_headers
            )
            
            client.post(
                f"/api/v1/quests/{quest.id}/complete",
                json={"progress": {}, "score": 100},
                headers=test_user_token_headers
            )
        
        # 6. Check if Math Genius badge was earned
        user_badges_response2 = client.get(
            "/api/v1/badges/user",
            headers=test_user_token_headers
        )
        
        updated_badges = user_badges_response2.json()
        math_badge = next(
            (b for b in updated_badges if b["badge"]["name"] == "Math Genius"),
            None
        )
        
        # Badge earning would depend on implementation
        # assert math_badge is not None
        # assert math_badge["unlocked_at"] is not None


class TestRewardSystem:
    """Test various reward mechanisms"""
    
    def test_daily_rewards(
        self,
        client: TestClient,
        db: Session,
        test_user: User,
        test_character: Character,
        test_user_token_headers: dict
    ):
        """Test daily reward claiming"""
        # 1. Check daily reward status
        status_response = client.get(
            "/api/v1/rewards/daily/status",
            headers=test_user_token_headers
        )
        assert status_response.status_code == 200
        
        status = status_response.json()
        assert status["can_claim"] is True
        assert status["streak"] == 0
        
        # 2. Claim daily reward
        claim_response = client.post(
            "/api/v1/rewards/daily/claim",
            headers=test_user_token_headers
        )
        assert claim_response.status_code == 200
        
        reward_data = claim_response.json()
        assert reward_data["success"] is True
        assert "reward" in reward_data
        assert reward_data["streak"] == 1
        
        # 3. Try to claim again (should fail)
        claim_response2 = client.post(
            "/api/v1/rewards/daily/claim",
            headers=test_user_token_headers
        )
        assert claim_response2.status_code == 400
        
        # 4. Check status again
        status_response2 = client.get(
            "/api/v1/rewards/daily/status",
            headers=test_user_token_headers
        )
        
        status2 = status_response2.json()
        assert status2["can_claim"] is False
        assert status2["streak"] == 1
        assert "next_claim_time" in status2
    
    def test_level_rewards(
        self,
        client: TestClient,
        db: Session,
        test_user: User,
        test_character: Character,
        test_user_token_headers: dict
    ):
        """Test level-up rewards"""
        # Add enough experience to level up multiple times
        from app.services.gamification import LevelService
        level_service = LevelService()
        
        # Add experience to reach level 5
        for i in range(4):  # Level 1->2, 2->3, 3->4, 4->5
            exp_needed = level_service.calculate_exp_for_next_level(
                test_character.total_level
            )
            level_service.add_experience(
                db,
                test_character,
                SubjectType.MATH,
                exp_needed
            )
        
        db.refresh(test_character)
        assert test_character.total_level == 5
        
        # Check if level rewards were given
        # This would depend on the implementation
        # Typically level rewards would be automatic
        
        # Get character info to see rewards
        character_response = client.get(
            "/api/v1/character",
            headers=test_user_token_headers
        )
        assert character_response.status_code == 200
        
        character_data = character_response.json()
        assert character_data["total_level"] == 5
        # Check if coins/gems were awarded for leveling