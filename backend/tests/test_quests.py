import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models.user import User
from app.models.quest import Quest, QuestProgress
from app.models.character import Character
from app.schemas.quest import (
    QuestCreate,
    QuestUpdate,
    QuestProgressCreate,
    QuestProgressUpdate,
    QuestSubmission,
    QuestType,
    QuestDifficulty,
    QuestStatus
)
from app.services.quest_service import QuestService
from app.core.exceptions import (
    ConflictException, 
    NotFoundException, 
    BadRequestException,
    ForbiddenException
)


class TestQuestService:
    """퀘스트 서비스 테스트"""
    
    def test_create_quest(self, db: Session):
        """퀘스트 생성 테스트"""
        quest_data = QuestCreate(
            title="Basic Math Quest",
            description="Solve basic addition problems",
            quest_type=QuestType.DAILY,
            difficulty=QuestDifficulty.EASY,
            subject="math",
            objectives=[{"type": "solve", "count": 5}],
            exp_reward=100,
            coin_reward=50,
            gem_reward=0,
            time_limit_minutes=30,
            min_level=1
        )
        
        quest = QuestService.create_quest(db, quest_data)
        
        assert quest.title == "Basic Math Quest"
        assert quest.quest_type == QuestType.DAILY
        assert quest.difficulty == QuestDifficulty.EASY
        assert quest.exp_reward == 100
        assert quest.is_active == True
    
    def test_get_quest(self, db: Session, test_quest: Quest):
        """퀘스트 조회 테스트"""
        quest = QuestService.get_quest(db, test_quest.id)
        assert quest.id == test_quest.id
        assert quest.title == test_quest.title
    
    def test_get_nonexistent_quest(self, db: Session):
        """존재하지 않는 퀘스트 조회 시 예외 발생 테스트"""
        with pytest.raises(NotFoundException):
            QuestService.get_quest(db, 99999)
    
    def test_get_quests_with_filters(self, db: Session, test_quests):
        """필터를 사용한 퀘스트 목록 조회 테스트"""
        # 타입별 조회
        daily_quests = QuestService.get_quests(
            db, quest_type=QuestType.DAILY
        )
        assert all(q.quest_type == QuestType.DAILY for q in daily_quests)
        
        # 난이도별 조회
        easy_quests = QuestService.get_quests(
            db, difficulty=QuestDifficulty.EASY
        )
        assert all(q.difficulty == QuestDifficulty.EASY for q in easy_quests)
        
        # 과목별 조회
        math_quests = QuestService.get_quests(
            db, subject="math"
        )
        assert all(q.subject == "math" for q in math_quests)
    
    def test_update_quest(self, db: Session, test_quest: Quest):
        """퀘스트 업데이트 테스트"""
        update_data = QuestUpdate(
            description="Updated description",
            exp_reward=150,
            coin_reward=75
        )
        
        updated = QuestService.update_quest(
            db, test_quest.id, update_data
        )
        
        assert updated.description == "Updated description"
        assert updated.exp_reward == 150
        assert updated.coin_reward == 75
    
    def test_start_quest(
        self, 
        db: Session, 
        test_user: User, 
        test_quest: Quest,
        test_character: Character
    ):
        """퀘스트 시작 테스트"""
        quest_data = QuestProgressCreate(quest_id=test_quest.id)
        
        progress = QuestService.start_quest(
            db, test_user.id, quest_data
        )
        
        assert progress.user_id == test_user.id
        assert progress.quest_id == test_quest.id
        assert progress.status == QuestStatus.IN_PROGRESS
        assert progress.started_at is not None
        assert progress.attempts == 1
    
    def test_start_quest_already_in_progress(
        self, 
        db: Session, 
        test_user: User, 
        test_quest_progress: QuestProgress
    ):
        """이미 진행 중인 퀘스트 시작 시 예외 발생 테스트"""
        quest_data = QuestProgressCreate(
            quest_id=test_quest_progress.quest_id
        )
        
        with pytest.raises(ConflictException):
            QuestService.start_quest(db, test_user.id, quest_data)
    
    def test_start_quest_with_prerequisites(
        self, 
        db: Session, 
        test_user: User,
        test_quest_with_prerequisites: Quest
    ):
        """선행 퀘스트 미완료 시 시작 불가 테스트"""
        quest_data = QuestProgressCreate(
            quest_id=test_quest_with_prerequisites.id
        )
        
        with pytest.raises(BadRequestException, match="Prerequisites not met"):
            QuestService.start_quest(db, test_user.id, quest_data)
    
    def test_update_quest_progress(
        self, 
        db: Session, 
        test_user: User,
        test_quest_progress: QuestProgress
    ):
        """퀘스트 진행도 업데이트 테스트"""
        progress_update = QuestProgressUpdate(
            progress={"solved": 3, "total": 5}
        )
        
        updated = QuestService.update_quest_progress(
            db, 
            test_user.id,
            test_quest_progress.quest_id,
            progress_update
        )
        
        assert updated.progress["solved"] == 3
        assert updated.progress["total"] == 5
    
    def test_submit_quest(
        self, 
        db: Session, 
        test_user: User,
        test_quest_progress: QuestProgress,
        test_character: Character
    ):
        """퀘스트 제출 테스트"""
        submission = QuestSubmission(
            quest_progress_id=test_quest_progress.id,
            answers={"answer1": "42", "answer2": "correct"},
            time_spent_seconds=600
        )
        
        result = QuestService.submit_quest(
            db, test_user.id, submission
        )
        
        assert result.quest_progress_id == test_quest_progress.id
        assert result.score >= 0
        assert result.score <= 100
        
        # 퀘스트 상태 확인
        db.refresh(test_quest_progress)
        assert test_quest_progress.status in [
            QuestStatus.COMPLETED, 
            QuestStatus.FAILED
        ]
    
    def test_submit_quest_time_limit_exceeded(
        self, 
        db: Session, 
        test_user: User,
        test_quest_progress_with_time_limit: QuestProgress
    ):
        """시간 제한 초과 퀘스트 제출 테스트"""
        # 시작 시간을 과거로 설정
        test_quest_progress_with_time_limit.started_at = (
            datetime.utcnow() - timedelta(hours=2)
        )
        db.commit()
        
        submission = QuestSubmission(
            quest_progress_id=test_quest_progress_with_time_limit.id,
            answers={"answer": "late"},
            time_spent_seconds=7200
        )
        
        with pytest.raises(BadRequestException, match="time limit exceeded"):
            QuestService.submit_quest(
                db, test_user.id, submission
            )
    
    def test_get_daily_quests(
        self, 
        db: Session, 
        test_user: User,
        test_daily_quests,
        test_character: Character
    ):
        """일일 퀘스트 조회 테스트"""
        daily_set = QuestService.get_daily_quests(db, test_user.id)
        
        assert daily_set.date.date() == datetime.utcnow().date()
        assert len(daily_set.quests) > 0
        assert all(q.quest_type == QuestType.DAILY for q in daily_set.quests)
        assert daily_set.total_count == len(daily_set.quests)
        assert daily_set.completed_count >= 0
    
    def test_get_quest_recommendations(
        self, 
        db: Session, 
        test_user: User,
        test_character: Character,
        test_quests_for_recommendation
    ):
        """퀘스트 추천 테스트"""
        recommendations = QuestService.get_quest_recommendations(
            db, test_user.id, limit=5
        )
        
        assert len(recommendations) <= 5
        
        # 추천된 퀘스트들이 사용자 레벨에 적합한지 확인
        for quest in recommendations:
            assert quest.min_level <= test_character.total_level
    
    def test_get_user_quest_stats(
        self, 
        db: Session, 
        test_user_with_quest_history
    ):
        """사용자 퀘스트 통계 조회 테스트"""
        stats = QuestService.get_user_quest_stats(
            db, test_user_with_quest_history.id
        )
        
        assert stats.total_quests_available > 0
        assert stats.quests_completed >= 0
        assert stats.quests_in_progress >= 0
        assert stats.total_exp_earned >= 0
        assert stats.total_coins_earned >= 0
        assert 0 <= stats.completion_rate <= 100
        assert stats.average_score >= 0
        assert len(stats.quests_by_type) > 0
        assert len(stats.quests_by_difficulty) > 0


class TestQuestAPI:
    """퀘스트 API 엔드포인트 테스트"""
    
    def test_get_quests_endpoint(
        self, 
        client: TestClient, 
        test_user_token_headers: dict
    ):
        """GET /api/v1/quests/ 테스트"""
        response = client.get(
            "/api/v1/quests/",
            headers=test_user_token_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_quest_endpoint(
        self, 
        client: TestClient,
        test_user_token_headers: dict,
        test_quest: Quest
    ):
        """GET /api/v1/quests/{quest_id} 테스트"""
        response = client.get(
            f"/api/v1/quests/{test_quest.id}",
            headers=test_user_token_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_quest.id
        assert data["title"] == test_quest.title
    
    def test_start_quest_endpoint(
        self,
        client: TestClient,
        test_user_token_headers: dict,
        test_quest: Quest
    ):
        """POST /api/v1/quests/{quest_id}/start 테스트"""
        response = client.post(
            f"/api/v1/quests/{test_quest.id}/start",
            headers=test_user_token_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["quest_id"] == test_quest.id
        assert data["status"] == "in_progress"
    
    def test_get_my_quest_progress_endpoint(
        self,
        client: TestClient,
        test_user_token_headers: dict
    ):
        """GET /api/v1/quests/progress 테스트"""
        response = client.get(
            "/api/v1/quests/progress",
            headers=test_user_token_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_submit_quest_endpoint(
        self,
        client: TestClient,
        test_user_token_headers: dict,
        test_quest_progress: QuestProgress
    ):
        """POST /api/v1/quests/submit 테스트"""
        submission_data = {
            "quest_progress_id": test_quest_progress.id,
            "answers": {"q1": "answer1", "q2": "answer2"},
            "time_spent_seconds": 300
        }
        
        response = client.post(
            "/api/v1/quests/submit",
            json=submission_data,
            headers=test_user_token_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "quest_progress_id" in data
        assert "score" in data
        assert "is_correct" in data
        assert "exp_earned" in data
        assert "coins_earned" in data
    
    def test_get_daily_quests_endpoint(
        self,
        client: TestClient,
        test_user_token_headers: dict
    ):
        """GET /api/v1/quests/daily 테스트"""
        response = client.get(
            "/api/v1/quests/daily",
            headers=test_user_token_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "date" in data
        assert "quests" in data
        assert "completed_count" in data
        assert "total_count" in data
    
    def test_get_quest_recommendations_endpoint(
        self,
        client: TestClient,
        test_user_token_headers: dict
    ):
        """GET /api/v1/quests/recommendations 테스트"""
        response = client.get(
            "/api/v1/quests/recommendations?limit=5",
            headers=test_user_token_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5
    
    def test_get_quest_stats_endpoint(
        self,
        client: TestClient,
        test_user_token_headers: dict
    ):
        """GET /api/v1/quests/stats 테스트"""
        response = client.get(
            "/api/v1/quests/stats",
            headers=test_user_token_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_quests_available" in data
        assert "quests_completed" in data
        assert "quests_in_progress" in data
        assert "total_exp_earned" in data
        assert "completion_rate" in data
    
    def test_create_quest_admin_endpoint(
        self,
        client: TestClient,
        admin_token_headers: dict
    ):
        """POST /api/v1/quests/ (관리자) 테스트"""
        quest_data = {
            "title": "Admin Created Quest",
            "description": "Created by admin API test",
            "quest_type": "special",
            "difficulty": "hard",
            "subject": "science",
            "objectives": [{"type": "research", "topic": "physics"}],
            "exp_reward": 500,
            "coin_reward": 200,
            "gem_reward": 10,
            "time_limit_minutes": 60,
            "min_level": 5
        }
        
        response = client.post(
            "/api/v1/quests/",
            json=quest_data,
            headers=admin_token_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Admin Created Quest"
        assert data["difficulty"] == "hard"
        assert data["exp_reward"] == 500