import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models.user import User
from app.models.character import Character, SubjectLevel
from app.schemas.character import (
    CharacterCreate,
    CharacterUpdate,
    ExperienceGain,
    CurrencyUpdate,
    SubjectType
)
from app.services.character_service import CharacterService
from app.core.exceptions import ConflictException, NotFoundException, BadRequestException


class TestCharacterService:
    """캐릭터 서비스 테스트"""
    
    def test_create_character(self, db: Session, test_user: User):
        """캐릭터 생성 테스트"""
        character_data = CharacterCreate(
            name="TestHero",
            avatar_url="https://example.com/avatar.png"
        )
        
        character = CharacterService.create_character(
            db, test_user.id, character_data
        )
        
        assert character.name == "TestHero"
        assert character.user_id == test_user.id
        assert character.total_level == 1
        assert character.total_experience == 0
        assert character.coins == 0
        assert character.gems == 0
        
        # 과목별 레벨 초기화 확인
        subject_levels = db.query(SubjectLevel).filter(
            SubjectLevel.character_id == character.id
        ).all()
        
        assert len(subject_levels) == len(SubjectType)
        for sl in subject_levels:
            assert sl.level == 1
            assert sl.experience == 0
            assert sl.exp_to_next_level == 100
    
    def test_create_duplicate_character(self, db: Session, test_user: User, test_character: Character):
        """중복 캐릭터 생성 시 예외 발생 테스트"""
        character_data = CharacterCreate(
            name="AnotherHero",
            avatar_url=None
        )
        
        with pytest.raises(ConflictException):
            CharacterService.create_character(db, test_user.id, character_data)
    
    def test_get_character(self, db: Session, test_character: Character):
        """캐릭터 조회 테스트"""
        character = CharacterService.get_character(db, test_character.id)
        assert character.id == test_character.id
        assert character.name == test_character.name
    
    def test_get_nonexistent_character(self, db: Session):
        """존재하지 않는 캐릭터 조회 시 예외 발생 테스트"""
        with pytest.raises(NotFoundException):
            CharacterService.get_character(db, 99999)
    
    def test_update_character(self, db: Session, test_character: Character):
        """캐릭터 업데이트 테스트"""
        update_data = CharacterUpdate(
            name="UpdatedHero",
            coins=100,
            gems=10
        )
        
        updated_character = CharacterService.update_character(
            db, test_character.id, update_data
        )
        
        assert updated_character.name == "UpdatedHero"
        assert updated_character.coins == 100
        assert updated_character.gems == 10
    
    def test_add_experience(self, db: Session, test_character: Character):
        """경험치 추가 테스트"""
        exp_gain = ExperienceGain(
            subject=SubjectType.MATH,
            experience_gained=150,
            reason="Completed quest"
        )
        
        subject_level = CharacterService.add_experience(
            db, test_character.id, exp_gain
        )
        
        # 레벨업 확인 (100 exp for level 2, 50 remaining)
        assert subject_level.level == 2
        assert subject_level.experience == 50
        assert subject_level.exp_to_next_level > 100
        
        # 캐릭터 총 경험치 확인
        db.refresh(test_character)
        assert test_character.total_experience == 150
    
    def test_update_currency(self, db: Session, test_character: Character):
        """화폐 업데이트 테스트"""
        # 화폐 추가
        currency_update = CurrencyUpdate(
            coins=500,
            gems=50,
            reason="Quest reward"
        )
        
        updated_character = CharacterService.update_currency(
            db, test_character.id, currency_update
        )
        
        assert updated_character.coins == 500
        assert updated_character.gems == 50
        
        # 화폐 차감
        currency_update = CurrencyUpdate(
            coins=-200,
            gems=-20,
            reason="Item purchase"
        )
        
        updated_character = CharacterService.update_currency(
            db, test_character.id, currency_update
        )
        
        assert updated_character.coins == 300
        assert updated_character.gems == 30
    
    def test_insufficient_currency(self, db: Session, test_character: Character):
        """부족한 화폐 차감 시 예외 발생 테스트"""
        currency_update = CurrencyUpdate(
            coins=-1000,  # More than available
            reason="Expensive item"
        )
        
        with pytest.raises(BadRequestException):
            CharacterService.update_currency(
                db, test_character.id, currency_update
            )
    
    def test_update_streak(self, db: Session, test_character: Character):
        """연속 출석 업데이트 테스트"""
        # 첫 번째 업데이트
        updated_character = CharacterService.update_streak(
            db, test_character.id
        )
        
        assert updated_character.streak_days == 1
        assert updated_character.last_active_date is not None
        
        # 같은 날 재업데이트 (변화 없음)
        updated_character = CharacterService.update_streak(
            db, test_character.id
        )
        
        assert updated_character.streak_days == 1
    
    def test_get_rankings(self, db: Session, test_characters_for_ranking):
        """랭킹 조회 테스트"""
        rankings = CharacterService.get_rankings(db, limit=10)
        
        assert len(rankings) > 0
        
        # 레벨과 경험치 내림차순 확인
        for i in range(len(rankings) - 1):
            current = rankings[i]
            next_char = rankings[i + 1]
            
            if current.total_level == next_char.total_level:
                assert current.total_experience >= next_char.total_experience
            else:
                assert current.total_level > next_char.total_level


class TestCharacterAPI:
    """캐릭터 API 엔드포인트 테스트"""
    
    def test_create_character_endpoint(
        self, 
        client: TestClient, 
        test_user_token_headers: dict
    ):
        """POST /api/v1/characters/ 테스트"""
        character_data = {
            "name": "APITestHero",
            "avatar_url": "https://example.com/api-avatar.png"
        }
        
        response = client.post(
            "/api/v1/characters/",
            json=character_data,
            headers=test_user_token_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "APITestHero"
        assert "id" in data
        assert "user_id" in data
        assert "subject_levels" in data
    
    def test_get_my_character_endpoint(
        self, 
        client: TestClient,
        test_user_token_headers: dict,
        test_character: Character
    ):
        """GET /api/v1/characters/me 테스트"""
        response = client.get(
            "/api/v1/characters/me",
            headers=test_user_token_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_character.id
        assert data["name"] == test_character.name
    
    def test_update_character_endpoint(
        self,
        client: TestClient,
        test_user_token_headers: dict,
        test_character: Character
    ):
        """PUT /api/v1/characters/{character_id} 테스트"""
        update_data = {
            "name": "UpdatedAPIHero",
            "avatar_url": "https://example.com/new-avatar.png"
        }
        
        response = client.put(
            f"/api/v1/characters/{test_character.id}",
            json=update_data,
            headers=test_user_token_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "UpdatedAPIHero"
        assert data["avatar_url"] == "https://example.com/new-avatar.png"
    
    def test_add_experience_endpoint(
        self,
        client: TestClient,
        test_user_token_headers: dict,
        test_character: Character
    ):
        """POST /api/v1/characters/{character_id}/experience 테스트"""
        exp_data = {
            "subject": "math",
            "experience_gained": 200,
            "reason": "API test quest completion"
        }
        
        response = client.post(
            f"/api/v1/characters/{test_character.id}/experience",
            json=exp_data,
            headers=test_user_token_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["subject"] == "math"
        assert data["level"] >= 1
    
    def test_get_rankings_endpoint(
        self,
        client: TestClient,
        test_user_token_headers: dict
    ):
        """GET /api/v1/characters/rankings 테스트"""
        response = client.get(
            "/api/v1/characters/rankings?limit=10",
            headers=test_user_token_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 1:
            # 랭킹 순서 확인
            for i in range(len(data) - 1):
                assert data[i]["total_level"] >= data[i + 1]["total_level"]