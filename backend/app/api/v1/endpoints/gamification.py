from typing import Dict, List, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.gamification_service import GamificationService
from app.schemas.user import User as UserSchema

router = APIRouter()


@router.get("/profile", response_model=Dict[str, Any])
async def get_gamification_profile(
    current_user: UserSchema = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's gamification profile including level, stats, and achievements
    """
    service = GamificationService(db)
    profile_data = service.get_user_gamification_data(current_user.id)
    
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        **profile_data
    }


@router.post("/experience/add", response_model=Dict[str, Any])
async def add_experience(
    amount: int = Body(..., ge=1),
    source: str = Body(...),
    current_user: UserSchema = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add experience to user (for testing or admin purposes)
    """
    service = GamificationService(db)
    result = await service.add_experience(current_user.id, amount, source)
    
    return {
        "success": True,
        "leveled_up": result.leveled_up,
        "new_level": result.new_level,
        "experience_gained": result.experience_gained,
        "total_experience": result.total_experience,
        "rewards": result.rewards,
        "progress_percentage": result.progress_percentage
    }


@router.post("/daily-reward/claim", response_model=Dict[str, Any])
async def claim_daily_reward(
    current_user: UserSchema = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Claim daily login reward
    """
    service = GamificationService(db)
    result = await service.claim_daily_reward(current_user.id)
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    
    return {
        "success": result.success,
        "message": result.message,
        "rewards": result.rewards,
        "bonus_rewards": result.bonus_rewards
    }


@router.get("/daily-reward/status", response_model=Dict[str, Any])
async def get_daily_reward_status(
    current_user: UserSchema = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get daily reward status and streak information
    """
    from app.models.gamification import UserDailyReward
    
    user_daily = db.query(UserDailyReward).filter_by(user_id=current_user.id).first()
    
    can_claim = True
    if user_daily and user_daily.last_claim_date:
        can_claim = user_daily.last_claim_date.date() < datetime.utcnow().date()
    
    return {
        "can_claim": can_claim,
        "current_streak": user_daily.current_streak if user_daily else 0,
        "longest_streak": user_daily.longest_streak if user_daily else 0,
        "last_claim_date": user_daily.last_claim_date.isoformat() if user_daily and user_daily.last_claim_date else None,
        "total_claims": user_daily.total_claims if user_daily else 0
    }


@router.get("/badges", response_model=Dict[str, Any])
async def get_badges(
    category: str = Query(None),
    current_user: UserSchema = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all badges and user's progress
    """
    from app.models.gamification import Badge, UserBadge, BadgeCategory
    
    query = db.query(Badge)
    
    if category:
        try:
            category_enum = BadgeCategory(category)
            query = query.filter(Badge.category == category_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid badge category")
    
    all_badges = query.order_by(Badge.display_order).all()
    
    # Get user's badges
    user_badges = db.query(UserBadge).filter_by(user_id=current_user.id).all()
    user_badge_dict = {ub.badge_id: ub for ub in user_badges}
    
    badges_data = []
    for badge in all_badges:
        user_badge = user_badge_dict.get(badge.id)
        badges_data.append({
            "id": badge.id,
            "name": badge.name,
            "description": badge.description,
            "category": badge.category.value,
            "icon_url": badge.icon_url,
            "rarity": badge.rarity.value,
            "earned": user_badge is not None,
            "earned_at": user_badge.earned_at.isoformat() if user_badge else None,
            "progress": user_badge.progress if user_badge else 0,
            "is_secret": badge.is_secret and not user_badge
        })
    
    return {
        "total_badges": len(all_badges),
        "earned_badges": len(user_badges),
        "badges": badges_data
    }


@router.post("/badges/check", response_model=Dict[str, Any])
async def check_and_award_badges(
    current_user: UserSchema = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check and award any new badges earned
    """
    service = GamificationService(db)
    awarded_badges = await service.check_and_award_badges(current_user.id)
    
    return {
        "success": True,
        "newly_awarded": len(awarded_badges),
        "badges": [
            {
                "id": badge.id,
                "name": badge.name,
                "description": badge.description,
                "icon_url": badge.icon_url,
                "rarity": badge.rarity.value
            }
            for badge in awarded_badges
        ]
    }


@router.get("/inventory", response_model=Dict[str, Any])
async def get_inventory(
    item_type: str = Query(None),
    current_user: UserSchema = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's inventory
    """
    from app.models.gamification import UserInventory, Item, ItemType
    
    query = db.query(UserInventory).filter_by(user_id=current_user.id)
    
    if item_type:
        try:
            type_enum = ItemType(item_type)
            query = query.join(Item).filter(Item.type == type_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid item type")
    
    inventory_items = query.all()
    
    items_data = []
    for inv_item in inventory_items:
        item = inv_item.item
        items_data.append({
            "id": item.id,
            "name": item.name,
            "description": item.description,
            "type": item.type.value,
            "rarity": item.rarity.value,
            "icon_url": item.icon_url,
            "quantity": inv_item.quantity,
            "equipped": inv_item.is_equipped,
            "acquired_at": inv_item.acquired_at.isoformat(),
            "effects": item.effects
        })
    
    return {
        "total_items": sum(item.quantity for item in inventory_items),
        "unique_items": len(inventory_items),
        "items": items_data
    }


@router.post("/items/{item_id}/use", response_model=Dict[str, Any])
async def use_item(
    item_id: int,
    current_user: UserSchema = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Use an item from inventory
    """
    service = GamificationService(db)
    
    try:
        result = await service.use_item(current_user.id, item_id)
        return {
            "success": True,
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/leaderboard", response_model=Dict[str, Any])
async def get_leaderboard(
    type: str = Query("level", regex="^(level|gold|badges|quests)$"),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get leaderboard rankings
    """
    from app.models.gamification import UserLevel, UserStats
    from app.models.user import User
    
    if type == "level":
        # Level leaderboard
        rankings = db.query(
            User.id,
            User.username,
            UserLevel.current_level,
            UserLevel.total_experience
        ).join(
            UserLevel, User.id == UserLevel.user_id
        ).order_by(
            UserLevel.current_level.desc(),
            UserLevel.total_experience.desc()
        ).limit(limit).all()
        
        leaderboard_data = [
            {
                "rank": idx + 1,
                "user_id": r[0],
                "username": r[1],
                "level": r[2],
                "experience": r[3]
            }
            for idx, r in enumerate(rankings)
        ]
    
    elif type == "gold":
        # Gold leaderboard
        rankings = db.query(
            User.id,
            User.username,
            UserStats.gold
        ).join(
            UserStats, User.id == UserStats.user_id
        ).order_by(
            UserStats.gold.desc()
        ).limit(limit).all()
        
        leaderboard_data = [
            {
                "rank": idx + 1,
                "user_id": r[0],
                "username": r[1],
                "gold": r[2]
            }
            for idx, r in enumerate(rankings)
        ]
    
    elif type == "badges":
        # Badge count leaderboard
        from sqlalchemy import func
        from app.models.gamification import UserBadge
        
        rankings = db.query(
            User.id,
            User.username,
            func.count(UserBadge.id).label('badge_count')
        ).join(
            UserBadge, User.id == UserBadge.user_id
        ).group_by(
            User.id, User.username
        ).order_by(
            func.count(UserBadge.id).desc()
        ).limit(limit).all()
        
        leaderboard_data = [
            {
                "rank": idx + 1,
                "user_id": r[0],
                "username": r[1],
                "badge_count": r[2]
            }
            for idx, r in enumerate(rankings)
        ]
    
    else:  # quests
        # Quest completion leaderboard
        rankings = db.query(
            User.id,
            User.username,
            UserStats.total_quests_completed
        ).join(
            UserStats, User.id == UserStats.user_id
        ).order_by(
            UserStats.total_quests_completed.desc()
        ).limit(limit).all()
        
        leaderboard_data = [
            {
                "rank": idx + 1,
                "user_id": r[0],
                "username": r[1],
                "quests_completed": r[2]
            }
            for idx, r in enumerate(rankings)
        ]
    
    return {
        "type": type,
        "rankings": leaderboard_data,
        "updated_at": datetime.utcnow().isoformat()
    }


@router.get("/stats", response_model=Dict[str, Any])
async def get_user_stats(
    current_user: UserSchema = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed user statistics
    """
    from app.models.gamification import UserStats, UserLevel, UserBadge, UserInventory
    
    stats = db.query(UserStats).filter_by(user_id=current_user.id).first()
    level_info = db.query(UserLevel).filter_by(user_id=current_user.id).first()
    badge_count = db.query(UserBadge).filter_by(user_id=current_user.id).count()
    unique_items = db.query(UserInventory).filter_by(user_id=current_user.id).count()
    
    return {
        "user_id": current_user.id,
        "level": {
            "current": level_info.current_level if level_info else 1,
            "total_experience": level_info.total_experience if level_info else 0,
            "highest_reached": level_info.highest_level_reached if level_info else 1
        },
        "currency": {
            "gold": stats.gold if stats else 0,
            "gems": stats.gems if stats else 0
        },
        "achievements": {
            "total_badges": badge_count,
            "perfect_scores": stats.total_perfect_scores if stats else 0,
            "legendary_items": stats.legendary_items_owned if stats else 0
        },
        "activity": {
            "total_play_time": stats.total_play_time if stats else 0,
            "quests_completed": stats.total_quests_completed if stats else 0,
            "items_collected": stats.total_items_collected if stats else 0,
            "unique_items": unique_items
        },
        "social": {
            "friends_helped": stats.friends_helped if stats else 0,
            "gifts_sent": stats.gifts_sent if stats else 0,
            "gifts_received": stats.gifts_received if stats else 0
        }
    }


@router.post("/quest/{quest_id}/complete", response_model=Dict[str, Any])
async def complete_quest_rewards(
    quest_id: int,
    score: int = Body(..., ge=0, le=100),
    time_taken: int = Body(...),  # in seconds
    current_user: UserSchema = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Process rewards for completing a quest
    """
    from app.models.quest import Quest, QuestProgress
    from app.models.gamification import QuestReward, UserStats
    
    # Get quest
    quest = db.query(Quest).filter_by(id=quest_id).first()
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")
    
    # Get quest rewards
    quest_reward = db.query(QuestReward).filter_by(quest_id=quest_id).first()
    if not quest_reward:
        # Create default rewards
        quest_reward = QuestReward(
            quest_id=quest_id,
            experience=quest.reward_experience,
            gold=quest.reward_gold
        )
        db.add(quest_reward)
    
    # Calculate total rewards
    service = GamificationService(db)
    rewards_earned = []
    
    # Base rewards
    exp_earned = quest_reward.experience
    gold_earned = quest_reward.gold
    
    # Perfect score bonus
    if score == 100 and quest_reward.perfect_bonus:
        exp_earned += quest_reward.perfect_bonus.get("experience", 0)
        gold_earned += quest_reward.perfect_bonus.get("gold", 0)
    
    # Speed bonus
    if quest_reward.speed_bonus and time_taken < quest_reward.speed_bonus.get("time_limit", 999999):
        exp_earned += quest_reward.speed_bonus.get("experience", 0)
        gold_earned += quest_reward.speed_bonus.get("gold", 0)
    
    # Award experience
    if exp_earned > 0:
        exp_result = await service.add_experience(current_user.id, exp_earned, f"quest_{quest_id}")
        rewards_earned.append({
            "type": "experience",
            "amount": exp_result.experience_gained,
            "leveled_up": exp_result.leveled_up
        })
    
    # Award gold
    if gold_earned > 0:
        await service._add_gold(current_user.id, gold_earned)
        rewards_earned.append({
            "type": "gold",
            "amount": gold_earned
        })
    
    # Update user stats
    user_stats = service._get_or_create_user_stats(current_user.id)
    user_stats.total_quests_completed += 1
    if score == 100:
        user_stats.total_perfect_scores += 1
    
    # Check for new badges
    awarded_badges = await service.check_and_award_badges(current_user.id)
    if awarded_badges:
        rewards_earned.append({
            "type": "badges",
            "badges": [{"id": b.id, "name": b.name} for b in awarded_badges]
        })
    
    db.commit()
    
    return {
        "success": True,
        "quest_id": quest_id,
        "score": score,
        "rewards": rewards_earned,
        "total_exp": exp_earned,
        "total_gold": gold_earned
    }