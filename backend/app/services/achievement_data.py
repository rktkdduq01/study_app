"""
Default achievement data for the educational RPG platform
"""

from typing import List, Dict, Any
from app.models.achievement import AchievementCategory, AchievementRarity


def get_default_achievements() -> List[Dict[str, Any]]:
    """Get default achievements for the platform"""
    return [
        # Academic Achievements
        {
            "name": "첫 걸음",
            "description": "첫 퀘스트를 완료하세요",
            "category": AchievementCategory.ACADEMIC,
            "rarity": AchievementRarity.COMMON,
            "icon_name": "first_step",
            "badge_color": "#4CAF50",
            "requirements": {
                "trigger_type": "quest_completed",
                "count": {"min": 1}
            },
            "points": 10,
            "xp_bonus": 25,
            "coin_bonus": 10,
            "gem_bonus": 1,
            "max_progress": 1
        },
        {
            "name": "퀘스트 마스터",
            "description": "100개의 퀘스트를 완료하세요",
            "category": AchievementCategory.ACADEMIC,
            "rarity": AchievementRarity.RARE,
            "icon_name": "quest_master",
            "badge_color": "#2196F3",
            "requirements": {
                "trigger_type": "quest_completed",
                "count": {"min": 100}
            },
            "points": 50,
            "xp_bonus": 200,
            "coin_bonus": 100,
            "gem_bonus": 10,
            "max_progress": 100
        },
        {
            "name": "수학 천재",
            "description": "수학 퀘스트 50개를 완료하세요",
            "category": AchievementCategory.ACADEMIC,
            "rarity": AchievementRarity.UNCOMMON,
            "icon_name": "math_genius",
            "badge_color": "#FF9800",
            "requirements": {
                "trigger_type": "quest_completed",
                "subject": "math",
                "count": {"min": 50}
            },
            "points": 30,
            "xp_bonus": 100,
            "coin_bonus": 50,
            "gem_bonus": 5,
            "max_progress": 50
        },
        
        # Consistency Achievements
        {
            "name": "일주일 연속 학습",
            "description": "7일 연속으로 로그인하세요",
            "category": AchievementCategory.CONSISTENCY,
            "rarity": AchievementRarity.COMMON,
            "icon_name": "week_streak",
            "badge_color": "#9C27B0",
            "requirements": {
                "trigger_type": "streak_milestone",
                "streak": {"equals": 7}
            },
            "points": 20,
            "xp_bonus": 50,
            "coin_bonus": 30,
            "gem_bonus": 3,
            "max_progress": 7
        },
        {
            "name": "한 달 연속 학습",
            "description": "30일 연속으로 로그인하세요",
            "category": AchievementCategory.CONSISTENCY,
            "rarity": AchievementRarity.EPIC,
            "icon_name": "month_streak",
            "badge_color": "#F44336",
            "requirements": {
                "trigger_type": "streak_milestone",
                "streak": {"equals": 30}
            },
            "points": 100,
            "xp_bonus": 300,
            "coin_bonus": 200,
            "gem_bonus": 20,
            "max_progress": 30
        },
        {
            "name": "백일의 약속",
            "description": "100일 연속으로 로그인하세요",
            "category": AchievementCategory.CONSISTENCY,
            "rarity": AchievementRarity.LEGENDARY,
            "icon_name": "hundred_days",
            "badge_color": "#FFD700",
            "requirements": {
                "trigger_type": "streak_milestone",
                "streak": {"equals": 100}
            },
            "points": 500,
            "xp_bonus": 1000,
            "coin_bonus": 1000,
            "gem_bonus": 100,
            "max_progress": 100,
            "title_reward": "불굴의 학습자"
        },
        
        # Mastery Achievements
        {
            "name": "완벽주의자",
            "description": "10개의 퀘스트에서 만점을 받으세요",
            "category": AchievementCategory.MASTERY,
            "rarity": AchievementRarity.UNCOMMON,
            "icon_name": "perfectionist",
            "badge_color": "#00BCD4",
            "requirements": {
                "trigger_type": "quest_completed",
                "score": {"equals": 100},
                "count": {"min": 10}
            },
            "points": 40,
            "xp_bonus": 150,
            "coin_bonus": 75,
            "gem_bonus": 7,
            "max_progress": 10
        },
        {
            "name": "하드 모드 챌린저",
            "description": "어려움 난이도 퀘스트 25개를 완료하세요",
            "category": AchievementCategory.MASTERY,
            "rarity": AchievementRarity.RARE,
            "icon_name": "hard_mode",
            "badge_color": "#E91E63",
            "requirements": {
                "trigger_type": "quest_completed",
                "difficulty": "hard",
                "count": {"min": 25}
            },
            "points": 60,
            "xp_bonus": 250,
            "coin_bonus": 150,
            "gem_bonus": 15,
            "max_progress": 25
        },
        
        # Level Milestones
        {
            "name": "레벨 10 달성",
            "description": "레벨 10에 도달하세요",
            "category": AchievementCategory.MILESTONE,
            "rarity": AchievementRarity.COMMON,
            "icon_name": "level_10",
            "badge_color": "#607D8B",
            "requirements": {
                "trigger_type": "level_milestone",
                "level": {"equals": 10}
            },
            "points": 25,
            "xp_bonus": 100,
            "coin_bonus": 50,
            "gem_bonus": 5,
            "max_progress": 1
        },
        {
            "name": "레벨 50 달성",
            "description": "레벨 50에 도달하세요",
            "category": AchievementCategory.MILESTONE,
            "rarity": AchievementRarity.EPIC,
            "icon_name": "level_50",
            "badge_color": "#795548",
            "requirements": {
                "trigger_type": "level_milestone",
                "level": {"equals": 50}
            },
            "points": 200,
            "xp_bonus": 500,
            "coin_bonus": 500,
            "gem_bonus": 50,
            "max_progress": 1,
            "title_reward": "베테랑 학습자"
        },
        {
            "name": "레벨 100 달성",
            "description": "레벨 100에 도달하세요",
            "category": AchievementCategory.MILESTONE,
            "rarity": AchievementRarity.LEGENDARY,
            "icon_name": "level_100",
            "badge_color": "#FFD700",
            "requirements": {
                "trigger_type": "level_milestone",
                "level": {"equals": 100}
            },
            "points": 1000,
            "xp_bonus": 2000,
            "coin_bonus": 2000,
            "gem_bonus": 200,
            "max_progress": 1,
            "title_reward": "전설의 학습자"
        },
        
        # Social Achievements
        {
            "name": "친구 만들기",
            "description": "첫 친구를 추가하세요",
            "category": AchievementCategory.SOCIAL,
            "rarity": AchievementRarity.COMMON,
            "icon_name": "first_friend",
            "badge_color": "#8BC34A",
            "requirements": {
                "trigger_type": "friend_added",
                "count": {"min": 1}
            },
            "points": 10,
            "xp_bonus": 25,
            "coin_bonus": 20,
            "gem_bonus": 2,
            "max_progress": 1
        },
        {
            "name": "인기스타",
            "description": "친구를 20명 만드세요",
            "category": AchievementCategory.SOCIAL,
            "rarity": AchievementRarity.RARE,
            "icon_name": "popular",
            "badge_color": "#CDDC39",
            "requirements": {
                "trigger_type": "friend_added",
                "count": {"min": 20}
            },
            "points": 50,
            "xp_bonus": 150,
            "coin_bonus": 100,
            "gem_bonus": 10,
            "max_progress": 20
        },
        
        # Special Achievements
        {
            "name": "베타 테스터",
            "description": "베타 테스트에 참여해주셔서 감사합니다!",
            "category": AchievementCategory.SPECIAL,
            "rarity": AchievementRarity.LEGENDARY,
            "icon_name": "beta_tester",
            "badge_color": "#9E9E9E",
            "requirements": {
                "trigger_type": "special_event",
                "event": "beta_test"
            },
            "points": 100,
            "xp_bonus": 200,
            "coin_bonus": 200,
            "gem_bonus": 20,
            "max_progress": 1,
            "title_reward": "베타 테스터",
            "is_hidden": False
        },
        {
            "name": "신년 첫 학습",
            "description": "새해 첫날 학습을 시작하세요",
            "category": AchievementCategory.SPECIAL,
            "rarity": AchievementRarity.EPIC,
            "icon_name": "new_year",
            "badge_color": "#FF5722",
            "requirements": {
                "trigger_type": "special_event",
                "event": "new_year_login"
            },
            "points": 75,
            "xp_bonus": 150,
            "coin_bonus": 150,
            "gem_bonus": 15,
            "max_progress": 1,
            "is_seasonal": True,
            "season": "new_year"
        }
    ]


def create_default_achievements(db, AchievementService):
    """Create default achievements in the database"""
    achievements = get_default_achievements()
    created_count = 0
    
    for achievement_data in achievements:
        # Check if achievement already exists
        existing = db.query(Achievement).filter_by(
            name=achievement_data["name"]
        ).first()
        
        if not existing:
            try:
                achievement = AchievementService.create_achievement(
                    db,
                    AchievementCreate(**achievement_data)
                )
                created_count += 1
                print(f"Created achievement: {achievement.name}")
            except Exception as e:
                print(f"Failed to create achievement {achievement_data['name']}: {e}")
        else:
            print(f"Achievement already exists: {achievement_data['name']}")
    
    return created_count