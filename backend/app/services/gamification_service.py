from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import math
import json
from dataclasses import dataclass

from app.models.gamification import (
    LevelSystem, UserLevel, DailyReward, UserDailyReward,
    Badge, UserBadge, Item, UserInventory, QuestReward,
    UserRewardHistory, UserStats, RewardType, ItemRarity,
    BadgeCategory
)
from app.models.user import User
from app.models.quest import Quest, QuestProgress
from app.core.exceptions import APIException
from app.websocket.events import WebSocketEvents
from app.services.achievement_service import AchievementService


@dataclass
class LevelUpResult:
    """Result of a level up calculation"""
    leveled_up: bool
    new_level: int
    experience_gained: int
    total_experience: int
    rewards: List[Dict[str, Any]]
    next_level_exp: int
    progress_percentage: float


@dataclass
class RewardResult:
    """Result of claiming rewards"""
    success: bool
    rewards: List[Dict[str, Any]]
    message: str
    bonus_rewards: Optional[List[Dict[str, Any]]] = None


class GamificationService:
    """Service for managing gamification features"""
    
    def __init__(self, db: Session):
        self.db = db
        self._init_level_system()
    
    def _init_level_system(self):
        """Initialize level system if not exists"""
        existing_levels = self.db.query(LevelSystem).count()
        if existing_levels == 0:
            # Create levels 1-100
            for level in range(1, 101):
                exp_required = self._calculate_level_exp(level)
                level_data = LevelSystem(
                    level=level,
                    required_experience=exp_required,
                    title=self._get_level_title(level),
                    rewards=self._get_level_rewards(level),
                    perks=self._get_level_perks(level),
                    icon_url=f"/icons/levels/level_{level}.png"
                )
                self.db.add(level_data)
            self.db.commit()
    
    def _calculate_level_exp(self, level: int) -> int:
        """
        Calculate experience required for a level using exponential growth formula.
        
        The formula creates a balanced progression curve:
        - Early levels (1-10): Quick progression to hook new users
        - Mid levels (11-50): Steady progression requiring consistent engagement
        - Late levels (51-100): Challenging progression for dedicated users
        
        Formula: base_exp * (multiplier^(level-1)) + (increment * (level-1))
        Example: Level 10 requires ~1,925 exp, Level 50 requires ~990,950 exp
        
        Args:
            level: The level to calculate experience for
            
        Returns:
            Total experience points required to reach this level
        """
        if level == 1:
            return 0
        
        # Base experience for level 2 (starting point)
        base_exp = 100
        
        # Exponential growth rate (1.5 = 50% increase per level)
        # This creates a smooth but challenging curve
        multiplier = 1.5
        
        # Linear increment to prevent early levels from being too easy
        # Adds consistent minimum progression requirement
        increment = 50
        
        return int(base_exp * (multiplier ** (level - 1)) + (increment * (level - 1)))
    
    def _get_level_title(self, level: int) -> str:
        """Get title for a level"""
        titles = {
            range(1, 11): "Beginner Adventurer",
            range(11, 21): "Apprentice Scholar",
            range(21, 31): "Journeyman Explorer",
            range(31, 41): "Expert Learner",
            range(41, 51): "Master Student",
            range(51, 61): "Grand Scholar",
            range(61, 71): "Elite Researcher",
            range(71, 81): "Legendary Sage",
            range(81, 91): "Mythic Intellect",
            range(91, 101): "Transcendent Mind"
        }
        
        for level_range, title in titles.items():
            if level in level_range:
                return title
        return "Unknown"
    
    def _get_level_rewards(self, level: int) -> List[Dict[str, Any]]:
        """
        Get rewards for reaching a level based on milestone system.
        
        Reward Structure:
        - Base rewards: Gold for every level (scales linearly)
        - Periodic rewards: Items every 5 levels, badges every 10 levels
        - Milestone rewards: Special titles at key levels (25, 50, 75, 100)
        
        This tiered system ensures:
        - Consistent rewards to maintain engagement (gold)
        - Regular power boosts (items) 
        - Achievement recognition (badges)
        - Prestigious accomplishments (titles)
        
        Args:
            level: The level reached
            
        Returns:
            List of reward dictionaries with type and value
        """
        rewards = []
        
        # Gold reward scales linearly with level
        # Level 1 = 100 gold, Level 50 = 5000 gold, Level 100 = 10000 gold
        # This ensures gold income matches economy inflation
        gold_amount = level * 100
        rewards.append({
            "type": RewardType.GOLD.value,
            "amount": gold_amount
        })
        
        # Milestone rewards encourage continued progression
        
        # Every 5 levels: Power-up items
        # These items provide temporary boosts (XP, gold, energy)
        # Item power scales with level tier (boost_item_1 through boost_item_20)
        if level % 5 == 0:
            rewards.append({
                "type": RewardType.ITEM.value,
                "item_id": f"boost_item_{level // 5}",
                "quantity": 1
            })
        
        # Every 10 levels: Achievement badges
        # Visual recognition of major milestones
        # Badges unlock profile customization options
        if level % 10 == 0:
            rewards.append({
                "type": RewardType.BADGE.value,
                "badge_id": f"level_{level}_badge"
            })
        
        # Special milestone levels: Prestigious titles
        # These are rare achievements that display social status
        # Only 4 titles available, making them highly valuable
        if level in [25, 50, 75, 100]:
            rewards.append({
                "type": RewardType.TITLE.value,
                "title": f"{self._get_level_title(level)} Elite"
            })
        
        return rewards
    
    def _get_level_perks(self, level: int) -> Dict[str, Any]:
        """
        Calculate permanent perks based on user level.
        
        Perk System Design:
        - Perks unlock at specific level thresholds
        - Values scale with level but have maximum caps
        - Higher level requirements for more powerful perks
        - Encourages long-term player retention
        
        Perk Types:
        1. exp_boost: Increases all experience gains (unlocks at level 10)
        2. gold_boost: Increases all gold rewards (unlocks at level 20)
        3. energy_regen: Faster energy regeneration (unlocks at level 30)
        4. bonus_hints: Extra hints for quests (unlocks at level 15)
        
        Args:
            level: User's current level
            
        Returns:
            Dictionary of active perks and their values
        """
        perks = {}
        
        # Experience boost perk
        # Unlocks at level 10, increases by 5% every 10 levels
        # Cap at 50% to prevent exponential growth exploitation
        # Level 10 = 5%, Level 50 = 25%, Level 100 = 50%
        if level >= 10:
            perks["exp_boost"] = min(level // 10 * 5, 50)
        
        # Gold boost perk
        # Unlocks at level 20, increases by 10% every 20 levels
        # Cap at 50% to maintain economy balance
        # Level 20 = 10%, Level 60 = 30%, Level 100 = 50%
        if level >= 20:
            perks["gold_boost"] = min(level // 20 * 10, 50)
        
        # Energy regeneration perk
        # Unlocks at level 30, increases by 10% every 30 levels
        # Cap at 30% to prevent unlimited play sessions
        # Level 30 = 10%, Level 60 = 20%, Level 90 = 30%
        if level >= 30:
            perks["energy_regen"] = min(level // 30 * 10, 30)
        
        # Hint availability perk
        # Unlocks at level 15, gain 1 extra hint every 15 levels
        # No cap - rewards very high level players
        # Level 15 = 1 hint, Level 45 = 3 hints, Level 90 = 6 hints
        if level >= 15:
            perks["bonus_hints"] = level // 15
        
        return perks
    
    async def add_experience(
        self, 
        user_id: int, 
        experience: int, 
        source: str
    ) -> LevelUpResult:
        """
        Add experience to user and process potential level ups.
        
        This method handles the core leveling mechanic:
        1. Applies experience boosts from perks and items
        2. Adds experience to user's total
        3. Checks and processes multiple level ups in one go
        4. Awards level rewards automatically
        5. Calculates progress to next level
        6. Sends real-time notifications for level ups
        
        Multiple level ups are possible if experience gain is large
        (e.g., completing a difficult quest at low level).
        
        Args:
            user_id: ID of the user gaining experience
            experience: Base experience amount to add
            source: Source of experience for tracking (e.g., 'quest_complete', 'battle_win')
            
        Returns:
            LevelUpResult with level up details and rewards
        """
        user_level = self.db.query(UserLevel).filter_by(user_id=user_id).first()
        
        if not user_level:
            # First time user - initialize at level 1
            user_level = UserLevel(user_id=user_id)
            self.db.add(user_level)
        
        # Apply experience boost from permanent perks
        perks = self._get_user_perks(user_id)
        exp_boost = perks.get("exp_boost", 0)
        
        # Calculate final experience with boosts
        # Formula: base_exp * (1 + boost_percentage/100)
        # Example: 100 exp with 50% boost = 150 exp
        boosted_exp = int(experience * (1 + exp_boost / 100))
        
        # Add experience
        user_level.current_experience += boosted_exp
        user_level.total_experience += boosted_exp
        
        # Check for level up - Handle multiple level ups in one transaction
        leveled_up = False
        rewards = []
        current_level = user_level.current_level  # Store initial level for comparison
        
        # Loop to handle multiple level ups from large experience gains
        # This ensures users don't miss rewards if they gain many levels at once
        while True:
            # Get data for next level
            next_level = self.db.query(LevelSystem).filter_by(
                level=user_level.current_level + 1
            ).first()
            
            # Stop if max level reached or insufficient experience
            if not next_level or user_level.current_experience < next_level.required_experience:
                break
            
            # Level up achieved!
            user_level.current_level += 1
            user_level.last_level_up = datetime.utcnow()
            user_level.levels_gained_today += 1  # For daily level up achievements
            
            # Track highest level for leaderboards and statistics
            if user_level.current_level > user_level.highest_level_reached:
                user_level.highest_level_reached = user_level.current_level
            
            leveled_up = True
            
            # Get rewards for this level
            level_rewards = next_level.rewards or []
            rewards.extend(level_rewards)
            
            # Process each reward immediately to prevent loss on error
            for reward in level_rewards:
                await self._process_reward(user_id, reward, f"level_{user_level.current_level}")
        
        # Calculate progress to next level
        current_level_data = self.db.query(LevelSystem).filter_by(
            level=user_level.current_level
        ).first()
        next_level_data = self.db.query(LevelSystem).filter_by(
            level=user_level.current_level + 1
        ).first()
        
        if current_level_data and next_level_data:
            exp_in_level = user_level.current_experience - current_level_data.required_experience
            exp_needed = next_level_data.required_experience - current_level_data.required_experience
            user_level.level_progress = (exp_in_level / exp_needed) * 100
        
        self.db.commit()
        
        # Check for level-related achievements
        if leveled_up:
            # Check level achievements
            AchievementService.check_and_award_achievements(
                self.db,
                user_id,
                'level_up',
                {
                    'new_level': user_level.current_level,
                    'previous_level': current_level,
                    'total_levels': user_level.current_level
                }
            )
            
            # Check for milestone levels (10, 25, 50, 100)
            if user_level.current_level in [10, 25, 50, 100]:
                AchievementService.check_and_award_achievements(
                    self.db,
                    user_id,
                    'level_milestone',
                    {
                        'level': user_level.current_level
                    }
                )
        
        # Send WebSocket notification if leveled up
        if leveled_up:
            await WebSocketEvents.emit_level_up(
                user_id=str(user_id),
                level_data={
                    "new_level": user_level.current_level,
                    "previous_level": current_level,
                    "rewards": rewards
                }
            )
        
        return LevelUpResult(
            leveled_up=leveled_up,
            new_level=user_level.current_level,
            experience_gained=boosted_exp,
            total_experience=user_level.total_experience,
            rewards=rewards,
            next_level_exp=next_level_data.required_experience if next_level_data else 0,
            progress_percentage=user_level.level_progress
        )
    
    async def claim_daily_reward(self, user_id: int) -> RewardResult:
        """
        Process daily login reward claim with streak tracking.
        
        Daily Reward System:
        - Rewards increase with consecutive daily logins (streak)
        - Streak resets if user misses a day
        - Maximum 30-day reward cycle (then loops back)
        - Special bonus rewards at 7, 14, and 30 day milestones
        
        Streak Mechanics:
        - Must claim within 24 hours to maintain streak
        - Timezone considered for "daily" definition
        - One claim per calendar day allowed
        
        Args:
            user_id: ID of user claiming reward
            
        Returns:
            RewardResult with claimed rewards and streak info
        """
        user_daily = self.db.query(UserDailyReward).filter_by(user_id=user_id).first()
        
        if not user_daily:
            # Initialize daily reward tracking for new user
            user_daily = UserDailyReward(user_id=user_id)
            self.db.add(user_daily)
        
        # Check if already claimed today
        # Uses date comparison to allow one claim per calendar day
        today = date.today()
        if user_daily.last_claim_date and user_daily.last_claim_date.date() == today:
            return RewardResult(
                success=False,
                rewards=[],
                message="Daily reward already claimed today"
            )
        
        # Update streak based on last claim
        # Streak continues if claimed yesterday, resets otherwise
        yesterday = today - timedelta(days=1)
        if user_daily.last_claim_date and user_daily.last_claim_date.date() == yesterday:
            # Consecutive day - increment streak
            user_daily.current_streak += 1
        else:
            # Missed day(s) - reset streak to 1
            user_daily.current_streak = 1
        
        if user_daily.current_streak > user_daily.longest_streak:
            user_daily.longest_streak = user_daily.current_streak
        
        # Get reward for current streak day
        # Cap at 30 days to create a repeating cycle
        # This prevents infinite reward scaling while maintaining engagement
        streak_day = min(user_daily.current_streak, 30)
        daily_reward = self.db.query(DailyReward).filter_by(day=streak_day).first()
        
        if not daily_reward:
            # Fallback: Create default reward if not configured
            # Formula: 50 base + (10 * day) = gradually increasing rewards
            # Day 1 = 60 gold, Day 15 = 200 gold, Day 30 = 350 gold
            daily_reward = DailyReward(
                day=streak_day,
                reward_type=RewardType.GOLD,
                reward_value={"amount": 50 + (streak_day * 10)}
            )
        
        # Process reward
        rewards = []
        reward_data = {
            "type": daily_reward.reward_type.value,
            **daily_reward.reward_value
        }
        await self._process_reward(user_id, reward_data, f"daily_login_day_{streak_day}")
        rewards.append(reward_data)
        
        # Bonus rewards for streak milestones
        # These encourage maintaining long streaks
        bonus_rewards = []
        if user_daily.current_streak in [7, 14, 30]:
            # Milestone rewards:
            # 7 days: Weekly boost item for temporary benefits
            # 14 days: Significant gold bonus (500)
            # 30 days: Prestigious badge showing dedication
            bonus = {
                7: {"type": RewardType.ITEM.value, "item_id": "weekly_boost", "quantity": 1},
                14: {"type": RewardType.GOLD.value, "amount": 500},
                30: {"type": RewardType.BADGE.value, "badge_id": "monthly_dedication"}
            }
            bonus_reward = bonus[user_daily.current_streak]
            await self._process_reward(user_id, bonus_reward, f"streak_bonus_{user_daily.current_streak}")
            bonus_rewards.append(bonus_reward)
        
        # Update tracking
        user_daily.last_claim_date = datetime.utcnow()
        user_daily.total_claims += 1
        
        # Update monthly tracking
        if user_daily.current_month != today.month or user_daily.current_year != today.year:
            user_daily.monthly_claims = {}
            user_daily.current_month = today.month
            user_daily.current_year = today.year
        
        monthly_claims = user_daily.monthly_claims or {}
        monthly_claims[str(today.day)] = datetime.utcnow().isoformat()
        user_daily.monthly_claims = monthly_claims
        
        self.db.commit()
        
        # Check for streak-related achievements
        AchievementService.check_and_award_achievements(
            self.db,
            user_id,
            'daily_streak',
            {
                'streak': user_daily.current_streak,
                'total_claims': user_daily.total_claims
            }
        )
        
        # Check for milestone streaks (7, 14, 30, 60, 100 days)
        if user_daily.current_streak in [7, 14, 30, 60, 100]:
            AchievementService.check_and_award_achievements(
                self.db,
                user_id,
                'streak_milestone',
                {
                    'streak': user_daily.current_streak
                }
            )
        
        return RewardResult(
            success=True,
            rewards=rewards,
            message=f"Day {user_daily.current_streak} reward claimed!",
            bonus_rewards=bonus_rewards if bonus_rewards else None
        )
    
    async def check_and_award_badges(self, user_id: int) -> List[Badge]:
        """Check and award badges based on user progress"""
        awarded_badges = []
        user = self.db.query(User).filter_by(id=user_id).first()
        
        if not user:
            return awarded_badges
        
        # Get all badges
        all_badges = self.db.query(Badge).all()
        
        # Get user's current badges
        user_badge_ids = [ub.badge_id for ub in self.db.query(UserBadge).filter_by(user_id=user_id).all()]
        
        for badge in all_badges:
            if badge.id in user_badge_ids:
                continue  # Already has this badge
            
            # Check if user meets requirements
            if self._check_badge_requirements(user_id, badge):
                # Award badge
                user_badge = UserBadge(
                    user_id=user_id,
                    badge_id=badge.id,
                    progress=100.0
                )
                self.db.add(user_badge)
                
                # Process badge rewards
                if badge.reward_experience > 0:
                    await self.add_experience(user_id, badge.reward_experience, f"badge_{badge.id}")
                
                if badge.reward_gold > 0:
                    await self._add_gold(user_id, badge.reward_gold)
                
                if badge.reward_items:
                    for item_reward in badge.reward_items:
                        await self._process_reward(user_id, item_reward, f"badge_{badge.id}")
                
                # Update badge stats
                badge.total_earned += 1
                if not badge.first_earned_by:
                    badge.first_earned_by = user_id
                    badge.first_earned_at = datetime.utcnow()
                
                awarded_badges.append(badge)
                
                # Send notification
                await WebSocketEvents.emit_achievement_unlock(
                    user_id=str(user_id),
                    achievement_data={
                        "id": badge.id,
                        "name": badge.name,
                        "description": badge.description,
                        "icon_url": badge.icon_url,
                        "rarity": badge.rarity.value
                    }
                )
        
        self.db.commit()
        return awarded_badges
    
    def _check_badge_requirements(self, user_id: int, badge: Badge) -> bool:
        """Check if user meets badge requirements"""
        req_type = badge.requirement_type
        req_value = badge.requirement_value or {}
        
        if req_type == "quest_count":
            completed_quests = self.db.query(QuestProgress).filter(
                QuestProgress.user_id == user_id,
                QuestProgress.status == "completed"
            ).count()
            return completed_quests >= req_value.get("count", 0)
        
        elif req_type == "level":
            user_level = self.db.query(UserLevel).filter_by(user_id=user_id).first()
            return user_level and user_level.current_level >= req_value.get("min_level", 1)
        
        elif req_type == "streak":
            user_daily = self.db.query(UserDailyReward).filter_by(user_id=user_id).first()
            return user_daily and user_daily.current_streak >= req_value.get("days", 0)
        
        elif req_type == "perfect_scores":
            user_stats = self.db.query(UserStats).filter_by(user_id=user_id).first()
            return user_stats and user_stats.total_perfect_scores >= req_value.get("count", 0)
        
        elif req_type == "subject_mastery":
            # Check if user has completed enough quests in a subject
            subject = req_value.get("subject")
            count = req_value.get("count", 0)
            
            completed = self.db.query(QuestProgress).join(Quest).filter(
                QuestProgress.user_id == user_id,
                QuestProgress.status == "completed",
                Quest.subject == subject
            ).count()
            return completed >= count
        
        return False
    
    async def add_item_to_inventory(
        self, 
        user_id: int, 
        item_id: int, 
        quantity: int = 1,
        custom_data: Optional[Dict] = None
    ) -> bool:
        """Add item to user's inventory"""
        item = self.db.query(Item).filter_by(id=item_id).first()
        
        if not item:
            raise APIException(status_code=404, detail="Item not found")
        
        # Check if user already has this item
        inventory_item = self.db.query(UserInventory).filter_by(
            user_id=user_id,
            item_id=item_id
        ).first()
        
        if inventory_item:
            inventory_item.quantity += quantity
        else:
            inventory_item = UserInventory(
                user_id=user_id,
                item_id=item_id,
                quantity=quantity,
                custom_data=custom_data
            )
            self.db.add(inventory_item)
        
        # Update item stats
        item.total_owned += quantity
        
        # Update user stats
        user_stats = self._get_or_create_user_stats(user_id)
        user_stats.total_items_collected += quantity
        
        if item.rarity == ItemRarity.LEGENDARY:
            user_stats.legendary_items_owned += quantity
        
        self.db.commit()
        return True
    
    async def use_item(self, user_id: int, item_id: int) -> Dict[str, Any]:
        """Use an item from inventory"""
        inventory_item = self.db.query(UserInventory).filter_by(
            user_id=user_id,
            item_id=item_id
        ).first()
        
        if not inventory_item or inventory_item.quantity <= 0:
            raise APIException(status_code=400, detail="Item not in inventory")
        
        item = inventory_item.item
        
        # Check if item is usable
        if item.type not in ["boost", "consumable"]:
            raise APIException(status_code=400, detail="Item cannot be used")
        
        # Apply item effects
        effects_applied = {}
        if item.effects:
            for effect_type, value in item.effects.items():
                if effect_type == "exp_boost":
                    # Apply temporary exp boost
                    effects_applied[effect_type] = value
                elif effect_type == "gold_boost":
                    # Apply temporary gold boost
                    effects_applied[effect_type] = value
                elif effect_type == "instant_exp":
                    # Give instant experience
                    await self.add_experience(user_id, value, f"item_{item_id}")
                    effects_applied[effect_type] = value
                elif effect_type == "instant_gold":
                    # Give instant gold
                    await self._add_gold(user_id, value)
                    effects_applied[effect_type] = value
        
        # Update inventory
        inventory_item.quantity -= 1
        inventory_item.last_used_at = datetime.utcnow()
        
        if inventory_item.quantity == 0:
            self.db.delete(inventory_item)
        
        # Update item stats
        item.times_used += 1
        
        self.db.commit()
        
        return {
            "item_used": item.name,
            "effects": effects_applied,
            "duration": item.duration,
            "remaining_quantity": inventory_item.quantity if inventory_item.quantity > 0 else 0
        }
    
    async def _process_reward(self, user_id: int, reward: Dict[str, Any], source: str):
        """Process and award a reward to user"""
        reward_type = reward.get("type")
        
        # Record reward history
        history = UserRewardHistory(
            user_id=user_id,
            reward_type=reward_type,
            reward_value=reward,
            source_type=source.split("_")[0],
            source_id=source,
            claimed=True,
            claimed_at=datetime.utcnow()
        )
        self.db.add(history)
        
        if reward_type == RewardType.EXPERIENCE.value:
            await self.add_experience(user_id, reward["amount"], source)
        
        elif reward_type == RewardType.GOLD.value:
            await self._add_gold(user_id, reward["amount"])
        
        elif reward_type == RewardType.ITEM.value:
            # Find or create item
            item = self.db.query(Item).filter_by(name=reward["item_id"]).first()
            if item:
                await self.add_item_to_inventory(
                    user_id, 
                    item.id, 
                    reward.get("quantity", 1)
                )
        
        elif reward_type == RewardType.BADGE.value:
            # Award badge directly
            badge = self.db.query(Badge).filter_by(name=reward["badge_id"]).first()
            if badge:
                existing = self.db.query(UserBadge).filter_by(
                    user_id=user_id,
                    badge_id=badge.id
                ).first()
                
                if not existing:
                    user_badge = UserBadge(
                        user_id=user_id,
                        badge_id=badge.id,
                        progress=100.0
                    )
                    self.db.add(user_badge)
    
    async def _add_gold(self, user_id: int, amount: int):
        """Add gold to user's stats"""
        user_stats = self._get_or_create_user_stats(user_id)
        
        # Apply gold boost if any
        perks = self._get_user_perks(user_id)
        gold_boost = perks.get("gold_boost", 0)
        boosted_amount = int(amount * (1 + gold_boost / 100))
        
        user_stats.gold += boosted_amount
        self.db.commit()
    
    def _get_or_create_user_stats(self, user_id: int) -> UserStats:
        """Get or create user stats"""
        user_stats = self.db.query(UserStats).filter_by(user_id=user_id).first()
        
        if not user_stats:
            user_stats = UserStats(user_id=user_id)
            self.db.add(user_stats)
            self.db.commit()
        
        return user_stats
    
    def _get_user_perks(self, user_id: int) -> Dict[str, Any]:
        """Get user's active perks based on level"""
        user_level = self.db.query(UserLevel).filter_by(user_id=user_id).first()
        
        if not user_level:
            return {}
        
        level_data = self.db.query(LevelSystem).filter_by(
            level=user_level.current_level
        ).first()
        
        return level_data.perks if level_data else {}
    
    def get_user_gamification_data(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive gamification data for a user"""
        user_level = self.db.query(UserLevel).filter_by(user_id=user_id).first()
        user_stats = self.db.query(UserStats).filter_by(user_id=user_id).first()
        user_daily = self.db.query(UserDailyReward).filter_by(user_id=user_id).first()
        
        # Get badges
        user_badges = self.db.query(UserBadge).filter_by(user_id=user_id).all()
        badge_count = len(user_badges)
        
        # Get inventory
        inventory_items = self.db.query(UserInventory).filter_by(user_id=user_id).all()
        
        return {
            "level": {
                "current": user_level.current_level if user_level else 1,
                "experience": user_level.current_experience if user_level else 0,
                "progress": user_level.level_progress if user_level else 0,
                "title": self._get_level_title(user_level.current_level if user_level else 1)
            },
            "stats": {
                "gold": user_stats.gold if user_stats else 0,
                "gems": user_stats.gems if user_stats else 0,
                "total_quests": user_stats.total_quests_completed if user_stats else 0,
                "badges_earned": badge_count,
                "items_collected": user_stats.total_items_collected if user_stats else 0
            },
            "daily_reward": {
                "streak": user_daily.current_streak if user_daily else 0,
                "can_claim": self._can_claim_daily(user_daily) if user_daily else True
            },
            "inventory": {
                "total_items": sum(item.quantity for item in inventory_items),
                "unique_items": len(inventory_items)
            },
            "perks": self._get_user_perks(user_id)
        }
    
    def _can_claim_daily(self, user_daily: UserDailyReward) -> bool:
        """Check if user can claim daily reward"""
        if not user_daily.last_claim_date:
            return True
        
        return user_daily.last_claim_date.date() < date.today()