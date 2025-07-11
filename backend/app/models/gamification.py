from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Boolean, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.core.database import Base


class ItemType(str, enum.Enum):
    """Item type enumeration"""
    BOOST = "boost"
    COSMETIC = "cosmetic"
    CONSUMABLE = "consumable"
    EQUIPMENT = "equipment"
    SPECIAL = "special"


class ItemRarity(str, enum.Enum):
    """Item rarity enumeration"""
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class BadgeCategory(str, enum.Enum):
    """Badge category enumeration"""
    ACADEMIC = "academic"
    SOCIAL = "social"
    SPECIAL = "special"
    SEASONAL = "seasonal"
    MILESTONE = "milestone"


class RewardType(str, enum.Enum):
    """Reward type enumeration"""
    EXPERIENCE = "experience"
    GOLD = "gold"
    ITEM = "item"
    BADGE = "badge"
    TITLE = "title"
    COSMETIC = "cosmetic"


class LevelSystem(Base):
    """Level progression system"""
    __tablename__ = "level_system"
    
    level = Column(Integer, primary_key=True)
    required_experience = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    rewards = Column(JSON)  # List of rewards for reaching this level
    perks = Column(JSON)  # Special abilities or bonuses
    icon_url = Column(String)
    
    # Level scaling formula parameters
    base_exp = Column(Integer, default=100)
    exp_multiplier = Column(Float, default=1.5)
    exp_increment = Column(Integer, default=50)


class UserLevel(Base):
    """User level tracking"""
    __tablename__ = "user_levels"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    current_level = Column(Integer, default=1)
    current_experience = Column(Integer, default=0)
    total_experience = Column(Integer, default=0)
    level_progress = Column(Float, default=0.0)  # Percentage to next level
    
    # Prestige system
    prestige_level = Column(Integer, default=0)
    prestige_points = Column(Integer, default=0)
    
    # Stats
    levels_gained_today = Column(Integer, default=0)
    last_level_up = Column(DateTime)
    highest_level_reached = Column(Integer, default=1)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="level_info")


class DailyReward(Base):
    """Daily login rewards configuration"""
    __tablename__ = "daily_rewards"
    
    day = Column(Integer, primary_key=True)  # Day of the month or streak day
    reward_type = Column(SQLEnum(RewardType), nullable=False)
    reward_value = Column(JSON, nullable=False)  # {amount, item_id, badge_id, etc.}
    is_premium = Column(Boolean, default=False)
    special_condition = Column(String)  # Optional condition for special rewards


class UserDailyReward(Base):
    """User daily reward tracking"""
    __tablename__ = "user_daily_rewards"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Streak tracking
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_claim_date = Column(DateTime)
    total_claims = Column(Integer, default=0)
    
    # Monthly tracking
    monthly_claims = Column(JSON)  # {day: claimed_timestamp}
    current_month = Column(Integer)
    current_year = Column(Integer)
    
    # Rewards earned
    total_gold_earned = Column(Integer, default=0)
    total_exp_earned = Column(Integer, default=0)
    total_items_earned = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User", back_populates="daily_rewards")


class Badge(Base):
    """Badge definitions"""
    __tablename__ = "badges"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)
    category = Column(SQLEnum(BadgeCategory), nullable=False)
    icon_url = Column(String)
    
    # Requirements
    requirement_type = Column(String)  # quest_count, level, streak, etc.
    requirement_value = Column(JSON)  # Flexible requirement data
    
    # Rewards for earning the badge
    reward_experience = Column(Integer, default=0)
    reward_gold = Column(Integer, default=0)
    reward_items = Column(JSON)  # List of item rewards
    
    # Display properties
    rarity = Column(SQLEnum(ItemRarity), default=ItemRarity.COMMON)
    display_order = Column(Integer, default=0)
    is_secret = Column(Boolean, default=False)
    
    # Stats
    total_earned = Column(Integer, default=0)
    first_earned_by = Column(Integer, ForeignKey("users.id"))
    first_earned_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class UserBadge(Base):
    """User badge collection"""
    __tablename__ = "user_badges"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    badge_id = Column(Integer, ForeignKey("badges.id"), nullable=False)
    
    earned_at = Column(DateTime, default=datetime.utcnow)
    progress = Column(Float, default=0.0)  # Progress towards earning (0-100)
    is_equipped = Column(Boolean, default=False)  # If displayed on profile
    times_earned = Column(Integer, default=1)  # For repeatable badges
    
    # Relationships
    user = relationship("User", back_populates="badges")
    badge = relationship("Badge")


class Item(Base):
    """Item definitions"""
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)
    type = Column(SQLEnum(ItemType), nullable=False)
    rarity = Column(SQLEnum(ItemRarity), default=ItemRarity.COMMON)
    
    # Item properties
    icon_url = Column(String)
    model_url = Column(String)  # For 3D items
    effects = Column(JSON)  # {effect_type: value}
    duration = Column(Integer)  # Duration in seconds for temporary items
    
    # Shop properties
    shop_price = Column(Integer, default=0)
    is_tradeable = Column(Boolean, default=True)
    is_sellable = Column(Boolean, default=True)
    sell_price = Column(Integer, default=0)
    
    # Requirements
    level_requirement = Column(Integer, default=1)
    badge_requirement = Column(Integer, ForeignKey("badges.id"))
    
    # Stats
    total_owned = Column(Integer, default=0)
    times_used = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserInventory(Base):
    """User item inventory"""
    __tablename__ = "user_inventory"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    
    quantity = Column(Integer, default=1)
    acquired_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime)
    is_equipped = Column(Boolean, default=False)
    
    # Item-specific data
    custom_data = Column(JSON)  # For items with unique properties
    expires_at = Column(DateTime)  # For time-limited items
    
    # Relationships
    user = relationship("User", back_populates="inventory")
    item = relationship("Item")


class QuestReward(Base):
    """Quest completion rewards"""
    __tablename__ = "quest_rewards"
    
    id = Column(Integer, primary_key=True, index=True)
    quest_id = Column(Integer, ForeignKey("quests.id"), nullable=False)
    
    # Base rewards
    experience = Column(Integer, default=0)
    gold = Column(Integer, default=0)
    
    # Bonus rewards
    items = Column(JSON)  # [{item_id, quantity, chance}]
    badges = Column(JSON)  # [badge_id, ...]
    
    # Conditional rewards
    bonus_conditions = Column(JSON)  # {condition: {type, value, reward}}
    first_time_bonus = Column(JSON)  # Extra rewards for first completion
    speed_bonus = Column(JSON)  # Rewards for fast completion
    perfect_bonus = Column(JSON)  # Rewards for perfect score
    
    # Relationships
    quest = relationship("Quest", back_populates="rewards")


class UserRewardHistory(Base):
    """Track all rewards earned by users"""
    __tablename__ = "user_reward_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    reward_type = Column(SQLEnum(RewardType), nullable=False)
    reward_value = Column(JSON, nullable=False)
    source_type = Column(String)  # quest, daily, achievement, etc.
    source_id = Column(String)  # ID of the source
    
    earned_at = Column(DateTime, default=datetime.utcnow)
    claimed = Column(Boolean, default=False)
    claimed_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="reward_history")


class UserStats(Base):
    """Comprehensive user statistics for gamification"""
    __tablename__ = "user_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Currency
    gold = Column(Integer, default=0)
    gems = Column(Integer, default=0)  # Premium currency
    
    # Activity stats
    total_play_time = Column(Integer, default=0)  # In seconds
    total_quests_completed = Column(Integer, default=0)
    total_perfect_scores = Column(Integer, default=0)
    total_items_collected = Column(Integer, default=0)
    total_badges_earned = Column(Integer, default=0)
    
    # Combat stats (for battle system)
    battles_won = Column(Integer, default=0)
    battles_lost = Column(Integer, default=0)
    win_streak = Column(Integer, default=0)
    highest_win_streak = Column(Integer, default=0)
    
    # Social stats
    friends_helped = Column(Integer, default=0)
    gifts_sent = Column(Integer, default=0)
    gifts_received = Column(Integer, default=0)
    
    # Special achievements
    legendary_items_owned = Column(Integer, default=0)
    secret_areas_discovered = Column(Integer, default=0)
    easter_eggs_found = Column(Integer, default=0)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="stats", uselist=False)