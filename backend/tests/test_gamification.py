"""
Comprehensive unit tests for Gamification system
"""
import pytest
from datetime import datetime, timedelta, date
from typing import List
from unittest.mock import Mock, patch

from sqlalchemy.orm import Session
from app.services.gamification import GamificationService
from app.models.user import User
from app.models.gamification import (
    LevelSystem, UserLevel, DailyReward, UserDailyReward,
    Badge, UserBadge, Item, UserInventory, QuestReward,
    UserRewardHistory, UserStats
)
from app.models.quest import Quest, UserQuest
from app.models.achievement import Achievement, UserAchievement
from app.core.exceptions import BusinessLogicError, NotFoundError


@pytest.fixture
def gamification_service():
    """Create gamification service instance"""
    return GamificationService()


@pytest.fixture
def sample_user(db: Session):
    """Create a sample user with initial stats"""
    user = User(
        email="gamer@example.com",
        username="gamer123",
        full_name="Test Gamer",
        level=1,
        experience=0
    )
    db.add(user)
    db.commit()
    
    # Create user level
    user_level = UserLevel(
        user_id=user.id,
        current_level=1,
        current_experience=0,
        total_experience=0,
        level_up_count=0
    )
    db.add(user_level)
    
    # Create user stats
    user_stats = UserStats(
        user_id=user.id,
        gold=100,
        gems=10,
        total_play_time=0,
        quests_completed=0,
        perfect_scores=0,
        battles_won=0,
        battles_lost=0
    )
    db.add(user_stats)
    db.commit()
    
    return user


@pytest.fixture
def level_system(db: Session):
    """Create level system data"""
    levels = []
    for i in range(1, 11):
        level = LevelSystem(
            level=i,
            experience_required=100 * i * (i - 1) // 2,  # 0, 100, 200, 300...
            title=f"Level {i} Title",
            rewards={
                "gold": 50 * i,
                "items": [],
                "badges": []
            },
            perks={
                "experience_boost": 1.0 + (i * 0.05),
                "gold_boost": 1.0 + (i * 0.03)
            }
        )
        levels.append(level)
        db.add(level)
    db.commit()
    return levels


@pytest.fixture
def daily_rewards(db: Session):
    """Create daily reward system"""
    rewards = []
    for day in range(1, 8):
        reward = DailyReward(
            day=day,
            gold=10 * day,
            gems=day // 2,
            experience=20 * day,
            items=[],
            milestone_bonus={"extra_gold": 100} if day == 7 else {}
        )
        rewards.append(reward)
        db.add(reward)
    db.commit()
    return rewards


@pytest.fixture
def sample_badges(db: Session):
    """Create sample badges"""
    badges = [
        Badge(
            name="First Steps",
            description="Complete your first quest",
            icon="first_steps.png",
            category="milestone",
            rarity="common",
            requirements={"quests_completed": 1},
            rewards={"gold": 50, "experience": 100},
            secret=False
        ),
        Badge(
            name="Perfect Score",
            description="Get a perfect score on any quiz",
            icon="perfect_score.png",
            category="academic",
            rarity="rare",
            requirements={"perfect_scores": 1},
            rewards={"gold": 100, "experience": 200},
            secret=False
        ),
        Badge(
            name="Week Warrior",
            description="Login for 7 consecutive days",
            icon="week_warrior.png",
            category="milestone",
            rarity="uncommon",
            requirements={"login_streak": 7},
            rewards={"gold": 200, "gems": 5},
            secret=False
        ),
        Badge(
            name="Level 10",
            description="Reach level 10",
            icon="level_10.png",
            category="milestone",
            rarity="uncommon",
            requirements={"level": 10},
            rewards={"gold": 500, "experience": 1000},
            secret=False
        )
    ]
    for badge in badges:
        db.add(badge)
    db.commit()
    return badges


@pytest.fixture
def sample_items(db: Session):
    """Create sample items"""
    items = [
        Item(
            name="XP Boost",
            description="Double XP for 1 hour",
            icon="xp_boost.png",
            type="boost",
            rarity="uncommon",
            effects={"experience_multiplier": 2.0, "duration": 3600},
            shop_price=100,
            tradeable=True,
            consumable=True,
            max_stack=5
        ),
        Item(
            name="Energy Potion",
            description="Restore 50 energy",
            icon="energy_potion.png",
            type="consumable",
            rarity="common",
            effects={"energy_restore": 50},
            shop_price=50,
            tradeable=True,
            consumable=True,
            max_stack=10
        ),
        Item(
            name="Lucky Charm",
            description="Increase gold drops by 50%",
            icon="lucky_charm.png",
            type="equipment",
            rarity="rare",
            effects={"gold_multiplier": 1.5},
            shop_price=500,
            tradeable=False,
            consumable=False,
            max_stack=1
        )
    ]
    for item in items:
        db.add(item)
    db.commit()
    return items


class TestLevelSystem:
    """Test level and experience system"""
    
    def test_calculate_experience_for_next_level(self, gamification_service, level_system):
        """Test experience calculation for next level"""
        # Level 1 to 2 requires 100 XP
        exp_needed = gamification_service._calculate_experience_for_level(2)
        assert exp_needed == 100
        
        # Level 5 to 6
        exp_needed = gamification_service._calculate_experience_for_level(6)
        assert exp_needed > 500
    
    def test_add_experience_level_up(self, gamification_service, sample_user, level_system, db):
        """Test adding experience and leveling up"""
        # Add enough XP to level up from 1 to 2
        result = gamification_service.add_experience(
            user_id=sample_user.id,
            amount=150,
            source="quest_completion",
            db=db
        )
        
        assert result.leveled_up is True
        assert result.new_level == 2
        assert result.experience_gained == 150
        assert result.rewards["gold"] == 100  # Level 2 reward
        
        # Check user was updated
        user_level = db.query(UserLevel).filter(
            UserLevel.user_id == sample_user.id
        ).first()
        assert user_level.current_level == 2
        assert user_level.current_experience == 50  # 150 - 100 (level 2 requirement)
        assert user_level.total_experience == 150
    
    def test_add_experience_with_boost(self, gamification_service, sample_user, level_system, db):
        """Test experience boost from level perks"""
        # Set user to level 5 (has experience boost)
        user_level = db.query(UserLevel).filter(
            UserLevel.user_id == sample_user.id
        ).first()
        user_level.current_level = 5
        db.commit()
        
        # Add experience with boost
        result = gamification_service.add_experience(
            user_id=sample_user.id,
            amount=100,
            source="quest_completion",
            db=db
        )
        
        # Level 5 has 25% boost (1.25x)
        assert result.experience_gained == 125
    
    def test_multiple_level_ups(self, gamification_service, sample_user, level_system, db):
        """Test gaining multiple levels at once"""
        # Add enough XP to go from level 1 to level 3
        result = gamification_service.add_experience(
            user_id=sample_user.id,
            amount=500,  # Enough for multiple levels
            source="achievement",
            db=db
        )
        
        assert result.leveled_up is True
        assert result.new_level >= 3
        assert len(result.rewards) > 0
    
    def test_level_cap(self, gamification_service, sample_user, db):
        """Test behavior at level cap"""
        # Set user to max level (100)
        user_level = db.query(UserLevel).filter(
            UserLevel.user_id == sample_user.id
        ).first()
        user_level.current_level = 100
        user_level.total_experience = 1000000
        db.commit()
        
        # Try to add more experience
        result = gamification_service.add_experience(
            user_id=sample_user.id,
            amount=1000,
            source="quest_completion",
            db=db
        )
        
        assert result.leveled_up is False
        assert result.new_level == 100
        # Experience should still be tracked
        assert result.experience_gained == 1000


class TestDailyRewards:
    """Test daily reward system"""
    
    def test_claim_first_daily_reward(self, gamification_service, sample_user, daily_rewards, db):
        """Test claiming first daily reward"""
        result = gamification_service.claim_daily_reward(
            user_id=sample_user.id,
            db=db
        )
        
        assert result.success is True
        assert result.day == 1
        assert result.streak == 1
        assert result.rewards["gold"] == 10
        assert result.rewards["experience"] == 20
        
        # Check database update
        user_reward = db.query(UserDailyReward).filter(
            UserDailyReward.user_id == sample_user.id
        ).first()
        assert user_reward.current_streak == 1
        assert user_reward.last_claim_date == date.today()
    
    def test_claim_consecutive_daily_rewards(self, gamification_service, sample_user, daily_rewards, db):
        """Test claiming rewards on consecutive days"""
        # Claim day 1
        gamification_service.claim_daily_reward(user_id=sample_user.id, db=db)
        
        # Mock next day
        user_reward = db.query(UserDailyReward).filter(
            UserDailyReward.user_id == sample_user.id
        ).first()
        user_reward.last_claim_date = date.today() - timedelta(days=1)
        db.commit()
        
        # Claim day 2
        result = gamification_service.claim_daily_reward(
            user_id=sample_user.id,
            db=db
        )
        
        assert result.day == 2
        assert result.streak == 2
        assert result.rewards["gold"] == 20  # Day 2 reward
    
    def test_streak_reset_after_missing_day(self, gamification_service, sample_user, daily_rewards, db):
        """Test streak reset when missing a day"""
        # Build up a streak
        user_reward = UserDailyReward(
            user_id=sample_user.id,
            current_streak=5,
            longest_streak=5,
            last_claim_date=date.today() - timedelta(days=2),  # Missed yesterday
            total_claims=5
        )
        db.add(user_reward)
        db.commit()
        
        # Claim today (should reset streak)
        result = gamification_service.claim_daily_reward(
            user_id=sample_user.id,
            db=db
        )
        
        assert result.day == 1  # Reset to day 1
        assert result.streak == 1
        assert result.streak_lost is True
        
        # Longest streak should be preserved
        user_reward = db.query(UserDailyReward).filter(
            UserDailyReward.user_id == sample_user.id
        ).first()
        assert user_reward.longest_streak == 5
    
    def test_weekly_milestone_bonus(self, gamification_service, sample_user, daily_rewards, db):
        """Test milestone bonus at 7 days"""
        # Set up 6-day streak
        user_reward = UserDailyReward(
            user_id=sample_user.id,
            current_streak=6,
            last_claim_date=date.today() - timedelta(days=1),
            total_claims=6
        )
        db.add(user_reward)
        db.commit()
        
        # Claim day 7
        result = gamification_service.claim_daily_reward(
            user_id=sample_user.id,
            db=db
        )
        
        assert result.day == 7
        assert result.is_milestone is True
        assert "extra_gold" in result.milestone_bonus
        assert result.rewards["gold"] == 70 + result.milestone_bonus["extra_gold"]
    
    def test_cannot_claim_twice_same_day(self, gamification_service, sample_user, daily_rewards, db):
        """Test preventing multiple claims on same day"""
        # First claim
        gamification_service.claim_daily_reward(user_id=sample_user.id, db=db)
        
        # Try to claim again
        with pytest.raises(BusinessLogicError) as exc_info:
            gamification_service.claim_daily_reward(user_id=sample_user.id, db=db)
        
        assert "already claimed" in str(exc_info.value).lower()


class TestBadgeSystem:
    """Test badge awarding and tracking"""
    
    def test_check_and_award_badge_quest_completion(self, gamification_service, sample_user, sample_badges, db):
        """Test awarding badge for quest completion"""
        # Update user stats
        user_stats = db.query(UserStats).filter(
            UserStats.user_id == sample_user.id
        ).first()
        user_stats.quests_completed = 1
        db.commit()
        
        # Check for badges
        awarded = gamification_service.check_and_award_badges(
            user_id=sample_user.id,
            trigger="quest_complete",
            db=db
        )
        
        assert len(awarded) == 1
        assert awarded[0].name == "First Steps"
        
        # Verify badge was awarded
        user_badge = db.query(UserBadge).filter(
            UserBadge.user_id == sample_user.id,
            UserBadge.badge_id == awarded[0].id
        ).first()
        assert user_badge is not None
        assert user_badge.progress == 100.0
    
    def test_check_and_award_badge_perfect_score(self, gamification_service, sample_user, sample_badges, db):
        """Test awarding badge for perfect score"""
        # Update user stats
        user_stats = db.query(UserStats).filter(
            UserStats.user_id == sample_user.id
        ).first()
        user_stats.perfect_scores = 1
        db.commit()
        
        # Check for badges
        awarded = gamification_service.check_and_award_badges(
            user_id=sample_user.id,
            trigger="perfect_score",
            db=db
        )
        
        assert len(awarded) == 1
        assert awarded[0].name == "Perfect Score"
    
    def test_badge_progress_tracking(self, gamification_service, sample_user, sample_badges, db):
        """Test tracking progress towards badges"""
        # Create partial progress
        user_badge = UserBadge(
            user_id=sample_user.id,
            badge_id=sample_badges[2].id,  # Week Warrior (7 day streak)
            earned=False,
            progress=57.14  # 4/7 days
        )
        db.add(user_badge)
        db.commit()
        
        # Update progress (5 days now)
        user_reward = UserDailyReward(
            user_id=sample_user.id,
            current_streak=5,
            last_claim_date=date.today()
        )
        db.add(user_reward)
        db.commit()
        
        # Check badges (shouldn't award yet)
        awarded = gamification_service.check_and_award_badges(
            user_id=sample_user.id,
            trigger="daily_login",
            db=db
        )
        
        assert len(awarded) == 0
        
        # Check progress updated
        user_badge = db.query(UserBadge).filter(
            UserBadge.user_id == sample_user.id,
            UserBadge.badge_id == sample_badges[2].id
        ).first()
        assert user_badge.progress == 71.43  # 5/7 days
    
    def test_badge_rewards_distribution(self, gamification_service, sample_user, sample_badges, db):
        """Test that badge rewards are properly distributed"""
        # Award a badge with rewards
        user_stats = db.query(UserStats).filter(
            UserStats.user_id == sample_user.id
        ).first()
        initial_gold = user_stats.gold
        
        user_stats.perfect_scores = 1
        db.commit()
        
        awarded = gamification_service.check_and_award_badges(
            user_id=sample_user.id,
            trigger="perfect_score",
            db=db
        )
        
        # Check rewards were added
        user_stats = db.query(UserStats).filter(
            UserStats.user_id == sample_user.id
        ).first()
        assert user_stats.gold == initial_gold + 100  # Badge reward
    
    def test_no_duplicate_badge_awards(self, gamification_service, sample_user, sample_badges, db):
        """Test that badges can't be awarded twice"""
        # Award badge first time
        user_stats = db.query(UserStats).filter(
            UserStats.user_id == sample_user.id
        ).first()
        user_stats.quests_completed = 1
        db.commit()
        
        awarded1 = gamification_service.check_and_award_badges(
            user_id=sample_user.id,
            trigger="quest_complete",
            db=db
        )
        
        # Try to award again
        awarded2 = gamification_service.check_and_award_badges(
            user_id=sample_user.id,
            trigger="quest_complete",
            db=db
        )
        
        assert len(awarded1) == 1
        assert len(awarded2) == 0  # No duplicate award


class TestInventorySystem:
    """Test item and inventory management"""
    
    def test_add_item_to_inventory(self, gamification_service, sample_user, sample_items, db):
        """Test adding items to inventory"""
        item = sample_items[0]  # XP Boost
        
        result = gamification_service.add_item_to_inventory(
            user_id=sample_user.id,
            item_id=item.id,
            quantity=3,
            source="quest_reward",
            db=db
        )
        
        assert result.success is True
        assert result.total_quantity == 3
        
        # Check inventory
        inventory = db.query(UserInventory).filter(
            UserInventory.user_id == sample_user.id,
            UserInventory.item_id == item.id
        ).first()
        assert inventory.quantity == 3
    
    def test_stack_limit_enforcement(self, gamification_service, sample_user, sample_items, db):
        """Test that stack limits are enforced"""
        item = sample_items[0]  # XP Boost (max stack 5)
        
        # Add max stack
        gamification_service.add_item_to_inventory(
            user_id=sample_user.id,
            item_id=item.id,
            quantity=5,
            source="purchase",
            db=db
        )
        
        # Try to add more
        with pytest.raises(BusinessLogicError) as exc_info:
            gamification_service.add_item_to_inventory(
                user_id=sample_user.id,
                item_id=item.id,
                quantity=2,
                source="purchase",
                db=db
            )
        
        assert "stack limit" in str(exc_info.value).lower()
    
    def test_use_consumable_item(self, gamification_service, sample_user, sample_items, db):
        """Test using consumable items"""
        item = sample_items[1]  # Energy Potion
        
        # Add item first
        gamification_service.add_item_to_inventory(
            user_id=sample_user.id,
            item_id=item.id,
            quantity=3,
            source="purchase",
            db=db
        )
        
        # Use one
        result = gamification_service.use_item(
            user_id=sample_user.id,
            item_id=item.id,
            quantity=1,
            db=db
        )
        
        assert result.success is True
        assert result.effects_applied["energy_restore"] == 50
        assert result.remaining_quantity == 2
        
        # Check inventory updated
        inventory = db.query(UserInventory).filter(
            UserInventory.user_id == sample_user.id,
            UserInventory.item_id == item.id
        ).first()
        assert inventory.quantity == 2
    
    def test_use_boost_item(self, gamification_service, sample_user, sample_items, db):
        """Test using boost items with duration"""
        item = sample_items[0]  # XP Boost
        
        # Add and use
        gamification_service.add_item_to_inventory(
            user_id=sample_user.id,
            item_id=item.id,
            quantity=1,
            source="reward",
            db=db
        )
        
        with patch('app.services.gamification.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 12, 0, 0)
            
            result = gamification_service.use_item(
                user_id=sample_user.id,
                item_id=item.id,
                quantity=1,
                db=db
            )
            
            assert result.success is True
            assert result.effects_applied["experience_multiplier"] == 2.0
            assert result.effects_applied["expires_at"] is not None
    
    def test_cannot_use_non_consumable_item(self, gamification_service, sample_user, sample_items, db):
        """Test that non-consumable items can't be used"""
        item = sample_items[2]  # Lucky Charm (equipment)
        
        # Add item
        gamification_service.add_item_to_inventory(
            user_id=sample_user.id,
            item_id=item.id,
            quantity=1,
            source="reward",
            db=db
        )
        
        # Try to use
        with pytest.raises(BusinessLogicError) as exc_info:
            gamification_service.use_item(
                user_id=sample_user.id,
                item_id=item.id,
                quantity=1,
                db=db
            )
        
        assert "cannot be consumed" in str(exc_info.value).lower()


class TestUserStats:
    """Test user statistics tracking"""
    
    def test_update_user_stats(self, gamification_service, sample_user, db):
        """Test updating various user stats"""
        stats = db.query(UserStats).filter(
            UserStats.user_id == sample_user.id
        ).first()
        
        # Update different stats
        stats.quests_completed += 1
        stats.perfect_scores += 1
        stats.total_play_time += 3600  # 1 hour
        stats.battles_won += 1
        db.commit()
        
        # Verify updates
        updated_stats = db.query(UserStats).filter(
            UserStats.user_id == sample_user.id
        ).first()
        assert updated_stats.quests_completed == 1
        assert updated_stats.perfect_scores == 1
        assert updated_stats.total_play_time == 3600
        assert updated_stats.battles_won == 1
    
    def test_currency_management(self, gamification_service, sample_user, db):
        """Test gold and gem management"""
        stats = db.query(UserStats).filter(
            UserStats.user_id == sample_user.id
        ).first()
        initial_gold = stats.gold
        initial_gems = stats.gems
        
        # Add currency
        gamification_service._add_currency(
            user_id=sample_user.id,
            gold=50,
            gems=5,
            db=db
        )
        
        stats = db.query(UserStats).filter(
            UserStats.user_id == sample_user.id
        ).first()
        assert stats.gold == initial_gold + 50
        assert stats.gems == initial_gems + 5
        
        # Test spending (would be in purchase method)
        stats.gold -= 30
        db.commit()
        
        assert stats.gold == initial_gold + 20


class TestQuestRewards:
    """Test quest completion rewards"""
    
    def test_calculate_quest_rewards(self, gamification_service, sample_user, db):
        """Test calculating rewards for quest completion"""
        # Create a quest
        quest = Quest(
            title="Test Quest",
            description="Complete this test",
            difficulty="medium",
            experience_reward=200,
            gold_reward=50,
            type="main"
        )
        db.add(quest)
        db.commit()
        
        # Create quest reward configuration
        quest_reward = QuestReward(
            quest_id=quest.id,
            base_experience=200,
            base_gold=50,
            bonus_items=[],
            conditional_rewards={
                "first_time": {"gold": 100, "experience": 100},
                "speed_bonus": {"threshold": 300, "gold": 50},
                "perfect": {"gold": 100, "gems": 5}
            }
        )
        db.add(quest_reward)
        db.commit()
        
        # Calculate rewards
        rewards = gamification_service._calculate_quest_rewards(
            quest_id=quest.id,
            user_id=sample_user.id,
            completion_time=250,  # Under speed threshold
            perfect=True,
            first_time=True,
            db=db
        )
        
        assert rewards["experience"] == 300  # Base 200 + first time 100
        assert rewards["gold"] == 300  # Base 50 + first 100 + speed 50 + perfect 100
        assert rewards["gems"] == 5  # Perfect bonus


class TestLeaderboards:
    """Test leaderboard functionality"""
    
    def test_get_level_leaderboard(self, gamification_service, db):
        """Test level-based leaderboard"""
        # Create multiple users with different levels
        users = []
        for i in range(5):
            user = User(
                email=f"player{i}@example.com",
                username=f"player{i}",
                level=10 - i * 2  # 10, 8, 6, 4, 2
            )
            db.add(user)
            users.append(user)
        db.commit()
        
        # Create user levels
        for i, user in enumerate(users):
            user_level = UserLevel(
                user_id=user.id,
                current_level=10 - i * 2,
                total_experience=1000 * (5 - i)
            )
            db.add(user_level)
        db.commit()
        
        # Get leaderboard
        leaderboard = gamification_service.get_leaderboard(
            leaderboard_type="level",
            limit=3,
            db=db
        )
        
        assert len(leaderboard) == 3
        assert leaderboard[0]["username"] == "player0"
        assert leaderboard[0]["level"] == 10
        assert leaderboard[1]["level"] == 8
        assert leaderboard[2]["level"] == 6


class TestGamificationIntegration:
    """Integration tests for gamification system"""
    
    def test_complete_quest_flow(self, gamification_service, sample_user, level_system, sample_badges, db):
        """Test complete quest completion flow with all rewards"""
        # Setup quest
        quest = Quest(
            title="Integration Test Quest",
            difficulty="easy",
            experience_reward=150,
            gold_reward=75
        )
        db.add(quest)
        db.commit()
        
        # Complete quest (this would normally be called by quest service)
        initial_level = sample_user.level
        initial_stats = db.query(UserStats).filter(
            UserStats.user_id == sample_user.id
        ).first()
        initial_gold = initial_stats.gold
        
        # Add experience
        exp_result = gamification_service.add_experience(
            user_id=sample_user.id,
            amount=150,
            source="quest_completion",
            db=db
        )
        
        # Add gold
        gamification_service._add_currency(
            user_id=sample_user.id,
            gold=75,
            gems=0,
            db=db
        )
        
        # Update quest count
        initial_stats.quests_completed += 1
        db.commit()
        
        # Check for badges
        badges_earned = gamification_service.check_and_award_badges(
            user_id=sample_user.id,
            trigger="quest_complete",
            db=db
        )
        
        # Verify results
        assert exp_result.leveled_up is True  # Should level from 1 to 2
        assert len(badges_earned) == 1  # First Steps badge
        
        final_stats = db.query(UserStats).filter(
            UserStats.user_id == sample_user.id
        ).first()
        assert final_stats.gold > initial_gold + 75  # Quest gold + level up gold + badge gold
    
    def test_daily_login_streak_flow(self, gamification_service, sample_user, daily_rewards, sample_badges, db):
        """Test daily login streak with milestone"""
        # Simulate 7 days of login
        for day in range(7):
            if day > 0:
                # Update last claim date to yesterday
                user_reward = db.query(UserDailyReward).filter(
                    UserDailyReward.user_id == sample_user.id
                ).first()
                user_reward.last_claim_date = date.today() - timedelta(days=1)
                db.commit()
            
            # Claim daily reward
            result = gamification_service.claim_daily_reward(
                user_id=sample_user.id,
                db=db
            )
            
            # Check for streak badges
            if day == 6:  # Day 7
                badges = gamification_service.check_and_award_badges(
                    user_id=sample_user.id,
                    trigger="daily_login",
                    db=db
                )
                assert len(badges) == 1  # Week Warrior badge
                assert result.is_milestone is True


class TestErrorHandling:
    """Test error handling in gamification system"""
    
    def test_add_experience_user_not_found(self, gamification_service, db):
        """Test handling of non-existent user"""
        with pytest.raises(NotFoundError):
            gamification_service.add_experience(
                user_id=99999,
                amount=100,
                source="test",
                db=db
            )
    
    def test_use_item_insufficient_quantity(self, gamification_service, sample_user, sample_items, db):
        """Test using more items than available"""
        # Add 1 item
        gamification_service.add_item_to_inventory(
            user_id=sample_user.id,
            item_id=sample_items[0].id,
            quantity=1,
            source="test",
            db=db
        )
        
        # Try to use 2
        with pytest.raises(BusinessLogicError) as exc_info:
            gamification_service.use_item(
                user_id=sample_user.id,
                item_id=sample_items[0].id,
                quantity=2,
                db=db
            )
        
        assert "insufficient quantity" in str(exc_info.value).lower()