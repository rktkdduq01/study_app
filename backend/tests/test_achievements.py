import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models.user import User
from app.models.achievement import Achievement, UserAchievement
from app.schemas.achievement import (
    AchievementCreate,
    AchievementUpdate,
    UserAchievementCreate,
    UserAchievementProgressUpdate,
    AchievementCategory,
    AchievementRarity
)
from app.services.achievement_service import AchievementService
from app.core.exceptions import ConflictException, NotFoundException


class TestAchievementService:
    """업적 서비스 테스트"""
    
    def test_create_achievement(self, db: Session):
        """업적 생성 테스트"""
        achievement_data = AchievementCreate(
            name="First Steps",
            description="Complete your first quest",
            category=AchievementCategory.QUEST,
            rarity=AchievementRarity.COMMON,
            points=10,
            max_progress=1,
            requirements={"trigger_type": "quest_completed"}
        )
        
        achievement = AchievementService.create_achievement(db, achievement_data)
        
        assert achievement.name == "First Steps"
        assert achievement.category == AchievementCategory.QUEST
        assert achievement.rarity == AchievementRarity.COMMON
        assert achievement.points == 10
        assert achievement.is_active == True
    
    def test_get_achievement(self, db: Session, test_achievement: Achievement):
        """업적 조회 테스트"""
        achievement = AchievementService.get_achievement(db, test_achievement.id)
        assert achievement.id == test_achievement.id
        assert achievement.name == test_achievement.name
    
    def test_get_nonexistent_achievement(self, db: Session):
        """존재하지 않는 업적 조회 시 예외 발생 테스트"""
        with pytest.raises(NotFoundException):
            AchievementService.get_achievement(db, 99999)
    
    def test_get_achievements_with_filters(self, db: Session, test_achievements):
        """필터를 사용한 업적 목록 조회 테스트"""
        # 카테고리별 조회
        quest_achievements = AchievementService.get_achievements(
            db, category=AchievementCategory.QUEST
        )
        assert all(a.category == AchievementCategory.QUEST for a in quest_achievements)
        
        # 희귀도별 조회
        rare_achievements = AchievementService.get_achievements(
            db, rarity=AchievementRarity.RARE
        )
        assert all(a.rarity == AchievementRarity.RARE for a in rare_achievements)
    
    def test_update_achievement(self, db: Session, test_achievement: Achievement):
        """업적 업데이트 테스트"""
        update_data = AchievementUpdate(
            description="Updated description",
            points=20,
            rarity=AchievementRarity.RARE
        )
        
        updated = AchievementService.update_achievement(
            db, test_achievement.id, update_data
        )
        
        assert updated.description == "Updated description"
        assert updated.points == 20
        assert updated.rarity == AchievementRarity.RARE
    
    def test_create_user_achievement(
        self, 
        db: Session, 
        test_user: User, 
        test_achievement: Achievement
    ):
        """사용자 업적 생성 테스트"""
        user_achievement_data = UserAchievementCreate(
            achievement_id=test_achievement.id
        )
        
        user_achievement = AchievementService.create_user_achievement(
            db, test_user.id, user_achievement_data
        )
        
        assert user_achievement.user_id == test_user.id
        assert user_achievement.achievement_id == test_achievement.id
        assert user_achievement.progress == 0
        assert user_achievement.is_completed == False
    
    def test_create_duplicate_user_achievement(
        self, 
        db: Session, 
        test_user: User, 
        test_user_achievement: UserAchievement
    ):
        """중복 사용자 업적 생성 시 예외 발생 테스트"""
        user_achievement_data = UserAchievementCreate(
            achievement_id=test_user_achievement.achievement_id
        )
        
        with pytest.raises(ConflictException):
            AchievementService.create_user_achievement(
                db, test_user.id, user_achievement_data
            )
    
    def test_update_user_achievement_progress(
        self, 
        db: Session, 
        test_user: User, 
        test_achievement: Achievement
    ):
        """사용자 업적 진행도 업데이트 테스트"""
        # 업적이 없을 때 자동 생성 확인
        progress_update = UserAchievementProgressUpdate(progress=1)
        
        user_achievement = AchievementService.update_user_achievement_progress(
            db, test_user.id, test_achievement.id, progress_update
        )
        
        assert user_achievement.progress == 1
        assert user_achievement.is_completed == True  # max_progress가 1이므로
        assert user_achievement.completed_at is not None
    
    def test_check_and_award_achievements(
        self, 
        db: Session, 
        test_user: User,
        test_achievements_for_triggers
    ):
        """트리거 기반 업적 자동 부여 테스트"""
        # 퀘스트 완료 트리거
        trigger_data = {
            "quest_id": 1,
            "quest_type": "daily",
            "difficulty": "easy",
            "score": 95
        }
        
        awarded = AchievementService.check_and_award_achievements(
            db, test_user.id, "quest_completed", trigger_data
        )
        
        assert len(awarded) > 0
        for ua in awarded:
            assert ua.is_completed == True
            assert ua.completed_at is not None
    
    def test_get_user_achievement_stats(
        self, 
        db: Session, 
        test_user_with_achievements
    ):
        """사용자 업적 통계 조회 테스트"""
        stats = AchievementService.get_user_achievement_stats(
            db, test_user_with_achievements.id
        )
        
        assert stats.total_achievements > 0
        assert stats.completed_achievements >= 0
        assert stats.completed_achievements <= stats.total_achievements
        assert stats.total_points > 0
        assert stats.earned_points >= 0
        assert 0 <= stats.completion_percentage <= 100
        assert len(stats.achievements_by_category) > 0
        assert len(stats.achievements_by_rarity) > 0


class TestAchievementAPI:
    """업적 API 엔드포인트 테스트"""
    
    def test_get_achievements_endpoint(
        self, 
        client: TestClient, 
        test_user_token_headers: dict
    ):
        """GET /api/v1/achievements/ 테스트"""
        response = client.get(
            "/api/v1/achievements/",
            headers=test_user_token_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_achievement_endpoint(
        self, 
        client: TestClient,
        test_user_token_headers: dict,
        test_achievement: Achievement
    ):
        """GET /api/v1/achievements/{achievement_id} 테스트"""
        response = client.get(
            f"/api/v1/achievements/{test_achievement.id}",
            headers=test_user_token_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_achievement.id
        assert data["name"] == test_achievement.name
    
    def test_get_my_achievements_endpoint(
        self,
        client: TestClient,
        test_user_token_headers: dict
    ):
        """GET /api/v1/achievements/me 테스트"""
        response = client.get(
            "/api/v1/achievements/me",
            headers=test_user_token_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_update_achievement_progress_endpoint(
        self,
        client: TestClient,
        test_user_token_headers: dict,
        test_achievement: Achievement
    ):
        """PUT /api/v1/achievements/{achievement_id}/progress 테스트"""
        progress_data = {
            "progress": 1
        }
        
        response = client.put(
            f"/api/v1/achievements/{test_achievement.id}/progress",
            json=progress_data,
            headers=test_user_token_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["progress"] == 1
        assert data["achievement_id"] == test_achievement.id
    
    def test_get_achievement_stats_endpoint(
        self,
        client: TestClient,
        test_user_token_headers: dict
    ):
        """GET /api/v1/achievements/stats 테스트"""
        response = client.get(
            "/api/v1/achievements/stats",
            headers=test_user_token_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_achievements" in data
        assert "completed_achievements" in data
        assert "total_points" in data
        assert "earned_points" in data
        assert "completion_percentage" in data
        assert "achievements_by_category" in data
        assert "achievements_by_rarity" in data
    
    def test_create_achievement_admin_endpoint(
        self,
        client: TestClient,
        admin_token_headers: dict
    ):
        """POST /api/v1/achievements/ (관리자) 테스트"""
        achievement_data = {
            "name": "Admin Created Achievement",
            "description": "Created by admin API test",
            "category": "learning",
            "rarity": "epic",
            "points": 50,
            "max_progress": 10
        }
        
        response = client.post(
            "/api/v1/achievements/",
            json=achievement_data,
            headers=admin_token_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Admin Created Achievement"
        assert data["rarity"] == "epic"
        assert data["points"] == 50