"""
API endpoint tests for Gamification system
"""
import pytest
from datetime import datetime, timedelta, date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.gamification import (
    LevelSystem, UserLevel, DailyReward, Badge, 
    Item, UserStats, UserDailyReward
)


class TestGamificationAPI:
    """Test Gamification API endpoints"""
    
    def test_get_user_gamification_data(
        self, client: TestClient, normal_user_token: str, db: Session
    ):
        """Test getting comprehensive user gamification data"""
        # Get user
        user = db.query(User).filter(User.email == "test@example.com").first()
        
        # Create gamification data
        user_level = UserLevel(
            user_id=user.id,
            current_level=5,
            current_experience=250,
            total_experience=1250
        )
        user_stats = UserStats(
            user_id=user.id,
            gold=500,
            gems=50,
            quests_completed=10,
            perfect_scores=5
        )
        db.add(user_level)
        db.add(user_stats)
        db.commit()
        
        response = client.get(
            "/api/v1/gamification/user-data",
            headers={"Authorization": f"Bearer {normal_user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["level"]["current_level"] == 5
        assert data["stats"]["gold"] == 500
        assert data["stats"]["quests_completed"] == 10
    
    def test_add_experience_endpoint(
        self, client: TestClient, admin_token: str, db: Session
    ):
        """Test adding experience (admin only)"""
        user = db.query(User).filter(User.email == "test@example.com").first()
        
        # Create initial level data
        user_level = UserLevel(
            user_id=user.id,
            current_level=1,
            current_experience=0,
            total_experience=0
        )
        db.add(user_level)
        
        # Create level system
        for i in range(1, 5):
            level = LevelSystem(
                level=i,
                experience_required=(i-1) * 100,
                title=f"Level {i}",
                rewards={"gold": 50 * i}
            )
            db.add(level)
        db.commit()
        
        response = client.post(
            f"/api/v1/gamification/users/{user.id}/add-experience",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "amount": 150,
                "source": "quest_completion"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["leveled_up"] is True
        assert data["new_level"] == 2
        assert data["experience_gained"] == 150
    
    def test_claim_daily_reward_endpoint(
        self, client: TestClient, normal_user_token: str, db: Session
    ):
        """Test claiming daily reward"""
        # Create daily rewards
        for day in range(1, 8):
            reward = DailyReward(
                day=day,
                gold=10 * day,
                gems=day // 3,
                experience=20 * day
            )
            db.add(reward)
        db.commit()
        
        response = client.post(
            "/api/v1/gamification/daily-reward/claim",
            headers={"Authorization": f"Bearer {normal_user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["day"] == 1
        assert data["rewards"]["gold"] == 10
    
    def test_get_badges_endpoint(
        self, client: TestClient, normal_user_token: str, db: Session
    ):
        """Test getting user badges"""
        user = db.query(User).filter(User.email == "test@example.com").first()
        
        # Create badges
        badge1 = Badge(
            name="First Quest",
            description="Complete first quest",
            icon="first_quest.png",
            category="milestone",
            rarity="common"
        )
        badge2 = Badge(
            name="Perfect Score",
            description="Get perfect score",
            icon="perfect.png",
            category="academic",
            rarity="rare"
        )
        db.add(badge1)
        db.add(badge2)
        db.commit()
        
        response = client.get(
            "/api/v1/gamification/badges",
            headers={"Authorization": f"Bearer {normal_user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["badges"]) >= 2
        assert data["total_badges"] >= 2
        assert data["earned_badges"] == 0
    
    def test_get_inventory_endpoint(
        self, client: TestClient, normal_user_token: str, db: Session
    ):
        """Test getting user inventory"""
        response = client.get(
            "/api/v1/gamification/inventory",
            headers={"Authorization": f"Bearer {normal_user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["total_items"] == 0
    
    def test_use_item_endpoint(
        self, client: TestClient, normal_user_token: str, db: Session
    ):
        """Test using an item"""
        user = db.query(User).filter(User.email == "test@example.com").first()
        
        # Create consumable item
        item = Item(
            name="Health Potion",
            description="Restore health",
            type="consumable",
            rarity="common",
            effects={"health_restore": 50},
            consumable=True
        )
        db.add(item)
        db.commit()
        
        # Give item to user
        from app.models.gamification import UserInventory
        inventory = UserInventory(
            user_id=user.id,
            item_id=item.id,
            quantity=3
        )
        db.add(inventory)
        db.commit()
        
        response = client.post(
            f"/api/v1/gamification/items/{item.id}/use",
            headers={"Authorization": f"Bearer {normal_user_token}"},
            json={"quantity": 1}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["remaining_quantity"] == 2
    
    def test_get_leaderboard_endpoint(
        self, client: TestClient, normal_user_token: str, db: Session
    ):
        """Test getting leaderboards"""
        # Create multiple users with levels
        for i in range(3):
            user = User(
                email=f"player{i}@example.com",
                username=f"player{i}",
                level=10 - i
            )
            db.add(user)
        db.commit()
        
        # Add user levels
        users = db.query(User).filter(User.username.like("player%")).all()
        for user in users:
            user_level = UserLevel(
                user_id=user.id,
                current_level=user.level,
                total_experience=user.level * 1000
            )
            db.add(user_level)
        db.commit()
        
        response = client.get(
            "/api/v1/gamification/leaderboard/level",
            headers={"Authorization": f"Bearer {normal_user_token}"},
            params={"limit": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["leaderboard"]) >= 3
        assert data["leaderboard"][0]["level"] >= data["leaderboard"][1]["level"]
    
    def test_get_level_progress_endpoint(
        self, client: TestClient, normal_user_token: str, db: Session
    ):
        """Test getting level progress"""
        user = db.query(User).filter(User.email == "test@example.com").first()
        
        # Create level data
        user_level = UserLevel(
            user_id=user.id,
            current_level=3,
            current_experience=50,
            total_experience=350
        )
        db.add(user_level)
        
        # Create level system
        level = LevelSystem(
            level=4,
            experience_required=100,
            title="Level 4"
        )
        db.add(level)
        db.commit()
        
        response = client.get(
            "/api/v1/gamification/level-progress",
            headers={"Authorization": f"Bearer {normal_user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["current_level"] == 3
        assert data["current_experience"] == 50
        assert data["experience_for_next_level"] == 100
        assert data["progress_percentage"] == 50.0


class TestGamificationAPIValidation:
    """Test API validation and error handling"""
    
    def test_use_item_insufficient_quantity(
        self, client: TestClient, normal_user_token: str, db: Session
    ):
        """Test using more items than available"""
        user = db.query(User).filter(User.email == "test@example.com").first()
        
        # Create item with 1 quantity
        item = Item(name="Test Item", type="consumable", consumable=True)
        db.add(item)
        db.commit()
        
        from app.models.gamification import UserInventory
        inventory = UserInventory(
            user_id=user.id,
            item_id=item.id,
            quantity=1
        )
        db.add(inventory)
        db.commit()
        
        response = client.post(
            f"/api/v1/gamification/items/{item.id}/use",
            headers={"Authorization": f"Bearer {normal_user_token}"},
            json={"quantity": 2}
        )
        
        assert response.status_code == 400
        assert "insufficient" in response.json()["error"]["message"].lower()
    
    def test_claim_daily_reward_already_claimed(
        self, client: TestClient, normal_user_token: str, db: Session
    ):
        """Test claiming daily reward twice"""
        user = db.query(User).filter(User.email == "test@example.com").first()
        
        # Create daily reward
        reward = DailyReward(day=1, gold=10, gems=0, experience=20)
        db.add(reward)
        
        # Create claim record for today
        user_reward = UserDailyReward(
            user_id=user.id,
            current_streak=1,
            last_claim_date=date.today()
        )
        db.add(user_reward)
        db.commit()
        
        response = client.post(
            "/api/v1/gamification/daily-reward/claim",
            headers={"Authorization": f"Bearer {normal_user_token}"}
        )
        
        assert response.status_code == 400
        assert "already claimed" in response.json()["error"]["message"].lower()
    
    def test_invalid_leaderboard_type(
        self, client: TestClient, normal_user_token: str
    ):
        """Test requesting invalid leaderboard type"""
        response = client.get(
            "/api/v1/gamification/leaderboard/invalid_type",
            headers={"Authorization": f"Bearer {normal_user_token}"}
        )
        
        assert response.status_code == 400
    
    def test_add_experience_non_admin(
        self, client: TestClient, normal_user_token: str, db: Session
    ):
        """Test that non-admins cannot add experience"""
        user = db.query(User).filter(User.email == "test@example.com").first()
        
        response = client.post(
            f"/api/v1/gamification/users/{user.id}/add-experience",
            headers={"Authorization": f"Bearer {normal_user_token}"},
            json={"amount": 100, "source": "test"}
        )
        
        assert response.status_code == 403


class TestGamificationWebSocket:
    """Test WebSocket notifications for gamification events"""
    
    @pytest.mark.asyncio
    async def test_level_up_notification(
        self, client: TestClient, normal_user_token: str, db: Session
    ):
        """Test that level up triggers WebSocket notification"""
        # This would test WebSocket notifications if implemented
        # For now, just verify the event would be triggered
        pass
    
    @pytest.mark.asyncio
    async def test_badge_earned_notification(
        self, client: TestClient, normal_user_token: str, db: Session
    ):
        """Test that earning badge triggers WebSocket notification"""
        # This would test WebSocket notifications if implemented
        pass