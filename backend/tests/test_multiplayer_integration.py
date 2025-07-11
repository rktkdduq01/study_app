"""
Multiplayer system integration tests
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import Mock, patch

from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models.user import User
from app.models.multiplayer import (
    MultiplayerSession, MultiplayerParticipant,
    Battle, BattleParticipant, BattleRound,
    Tournament, TournamentParticipant,
    StudyGroup, StudyGroupMember
)
from app.models.quest import Quest
from app.services.multiplayer_service import MultiplayerService
from app.schemas.multiplayer import (
    BattleCreate, TournamentCreate, StudyGroupCreate,
    BattleAction, TournamentSettings
)


@pytest.fixture
def multiplayer_service():
    """Create multiplayer service instance"""
    return MultiplayerService()


@pytest.fixture
def sample_users(db: Session) -> List[User]:
    """Create multiple test users"""
    users = []
    for i in range(4):
        user = User(
            email=f"player{i}@example.com",
            username=f"player{i}",
            full_name=f"Player {i}",
            level=5 + i,
            experience=1000 * (i + 1)
        )
        users.append(user)
        db.add(user)
    db.commit()
    return users


class TestBattleSystem:
    """Test PvP battle functionality"""
    
    def test_create_battle(self, multiplayer_service, sample_users, db: Session):
        """Test creating a new battle"""
        creator = sample_users[0]
        
        battle_data = BattleCreate(
            title="Math Duel",
            subject="math",
            difficulty="medium",
            max_rounds=5,
            time_per_round=30,
            is_private=False
        )
        
        battle = multiplayer_service.create_battle(
            creator_id=creator.id,
            battle_data=battle_data,
            db=db
        )
        
        assert battle.title == "Math Duel"
        assert battle.creator_id == creator.id
        assert battle.status == "waiting"
        assert battle.max_participants == 2
        assert battle.current_participants == 1
        
        # Check participant was added
        participant = db.query(BattleParticipant).filter(
            BattleParticipant.battle_id == battle.id,
            BattleParticipant.user_id == creator.id
        ).first()
        assert participant is not None
        assert participant.is_ready is False
    
    def test_join_battle(self, multiplayer_service, sample_users, db: Session):
        """Test joining an existing battle"""
        creator = sample_users[0]
        joiner = sample_users[1]
        
        # Create battle
        battle = Battle(
            title="Quick Battle",
            creator_id=creator.id,
            subject="science",
            difficulty="easy",
            max_participants=2,
            current_participants=1,
            status="waiting"
        )
        db.add(battle)
        db.commit()
        
        # Add creator as participant
        db.add(BattleParticipant(
            battle_id=battle.id,
            user_id=creator.id
        ))
        db.commit()
        
        # Join battle
        result = multiplayer_service.join_battle(
            battle_id=battle.id,
            user_id=joiner.id,
            db=db
        )
        
        assert result.success is True
        assert result.battle.current_participants == 2
        assert result.battle.status == "ready"  # Auto-ready when full
        
        # Check participant was added
        participant = db.query(BattleParticipant).filter(
            BattleParticipant.battle_id == battle.id,
            BattleParticipant.user_id == joiner.id
        ).first()
        assert participant is not None
    
    def test_battle_ready_system(self, multiplayer_service, sample_users, db: Session):
        """Test battle ready system"""
        # Create battle with 2 participants
        battle = Battle(
            title="Ready Test",
            creator_id=sample_users[0].id,
            max_participants=2,
            current_participants=2,
            status="waiting"
        )
        db.add(battle)
        db.commit()
        
        # Add participants
        for i in range(2):
            db.add(BattleParticipant(
                battle_id=battle.id,
                user_id=sample_users[i].id,
                is_ready=False
            ))
        db.commit()
        
        # First player ready
        multiplayer_service.set_player_ready(
            battle_id=battle.id,
            user_id=sample_users[0].id,
            db=db
        )
        
        # Battle should still be waiting
        battle = db.query(Battle).filter(Battle.id == battle.id).first()
        assert battle.status == "waiting"
        
        # Second player ready
        multiplayer_service.set_player_ready(
            battle_id=battle.id,
            user_id=sample_users[1].id,
            db=db
        )
        
        # Battle should start
        battle = db.query(Battle).filter(Battle.id == battle.id).first()
        assert battle.status == "in_progress"
        assert battle.started_at is not None
    
    @pytest.mark.asyncio
    async def test_battle_round_flow(self, multiplayer_service, sample_users, db: Session):
        """Test complete battle round flow"""
        # Create active battle
        battle = Battle(
            title="Round Test",
            creator_id=sample_users[0].id,
            subject="math",
            difficulty="easy",
            max_participants=2,
            current_participants=2,
            status="in_progress",
            max_rounds=3,
            current_round=1,
            started_at=datetime.utcnow()
        )
        db.add(battle)
        db.commit()
        
        # Add participants
        participants = []
        for i in range(2):
            p = BattleParticipant(
                battle_id=battle.id,
                user_id=sample_users[i].id,
                is_ready=True,
                score=0
            )
            participants.append(p)
            db.add(p)
        db.commit()
        
        # Mock question generation
        with patch.object(multiplayer_service, '_generate_battle_question') as mock_gen:
            mock_gen.return_value = {
                'id': 'q1',
                'question': 'What is 2 + 2?',
                'options': ['3', '4', '5', '6'],
                'correct_answer': '4',
                'difficulty': 'easy'
            }
            
            # Start round
            round_data = await multiplayer_service.start_battle_round(
                battle_id=battle.id,
                db=db
            )
            
            assert round_data.round_number == 1
            assert round_data.question is not None
            assert len(round_data.question['options']) == 4
        
        # Submit answers
        answer1 = BattleAction(
            action_type="answer",
            data={
                'answer': '4',
                'time_taken': 3.5
            }
        )
        
        answer2 = BattleAction(
            action_type="answer",
            data={
                'answer': '5',
                'time_taken': 4.2
            }
        )
        
        # Player 1 answers correctly
        result1 = await multiplayer_service.submit_battle_action(
            battle_id=battle.id,
            user_id=sample_users[0].id,
            action=answer1,
            db=db
        )
        
        assert result1.correct is True
        assert result1.points_earned > 0
        
        # Player 2 answers incorrectly
        result2 = await multiplayer_service.submit_battle_action(
            battle_id=battle.id,
            user_id=sample_users[1].id,
            action=answer2,
            db=db
        )
        
        assert result2.correct is False
        assert result2.points_earned == 0
        
        # Check round completion
        battle_round = db.query(BattleRound).filter(
            BattleRound.battle_id == battle.id,
            BattleRound.round_number == 1
        ).first()
        assert battle_round is not None
        assert battle_round.winner_id == sample_users[0].id
    
    def test_battle_completion(self, multiplayer_service, sample_users, db: Session):
        """Test battle completion and rewards"""
        # Create completed battle
        battle = Battle(
            title="Completed Battle",
            creator_id=sample_users[0].id,
            max_participants=2,
            current_participants=2,
            status="in_progress",
            max_rounds=3,
            current_round=3,
            started_at=datetime.utcnow()
        )
        db.add(battle)
        db.commit()
        
        # Add participants with scores
        p1 = BattleParticipant(
            battle_id=battle.id,
            user_id=sample_users[0].id,
            score=250,
            rounds_won=2
        )
        p2 = BattleParticipant(
            battle_id=battle.id,
            user_id=sample_users[1].id,
            score=150,
            rounds_won=1
        )
        db.add(p1)
        db.add(p2)
        db.commit()
        
        # Complete battle
        result = multiplayer_service.complete_battle(
            battle_id=battle.id,
            db=db
        )
        
        assert result.winner_id == sample_users[0].id
        assert result.status == "completed"
        assert result.rewards is not None
        assert result.rewards['winner']['experience'] > result.rewards['loser']['experience']
        
        # Check battle status
        battle = db.query(Battle).filter(Battle.id == battle.id).first()
        assert battle.status == "completed"
        assert battle.winner_id == sample_users[0].id
        assert battle.ended_at is not None


class TestTournamentSystem:
    """Test tournament functionality"""
    
    def test_create_tournament(self, multiplayer_service, sample_users, db: Session):
        """Test creating a tournament"""
        creator = sample_users[0]
        
        tournament_data = TournamentCreate(
            name="Math Championship",
            description="Weekly math tournament",
            subject="math",
            difficulty="mixed",
            format="single_elimination",
            max_participants=8,
            start_time=datetime.utcnow() + timedelta(hours=1),
            settings=TournamentSettings(
                rounds_per_match=3,
                time_per_round=45,
                elimination_type="single",
                prize_pool={
                    "1st": {"gold": 1000, "gems": 100},
                    "2nd": {"gold": 500, "gems": 50},
                    "3rd": {"gold": 250, "gems": 25}
                }
            )
        )
        
        tournament = multiplayer_service.create_tournament(
            creator_id=creator.id,
            tournament_data=tournament_data,
            db=db
        )
        
        assert tournament.name == "Math Championship"
        assert tournament.status == "registration"
        assert tournament.max_participants == 8
        assert tournament.current_participants == 0
    
    def test_tournament_registration(self, multiplayer_service, sample_users, db: Session):
        """Test tournament registration"""
        # Create tournament
        tournament = Tournament(
            name="Quick Tournament",
            creator_id=sample_users[0].id,
            format="single_elimination",
            max_participants=4,
            current_participants=0,
            status="registration",
            start_time=datetime.utcnow() + timedelta(minutes=30)
        )
        db.add(tournament)
        db.commit()
        
        # Register players
        for i in range(4):
            result = multiplayer_service.register_for_tournament(
                tournament_id=tournament.id,
                user_id=sample_users[i].id,
                db=db
            )
            assert result.success is True
        
        # Check registration
        tournament = db.query(Tournament).filter(
            Tournament.id == tournament.id
        ).first()
        assert tournament.current_participants == 4
        
        # Try to register 5th player (should fail)
        extra_user = User(email="extra@example.com", username="extra")
        db.add(extra_user)
        db.commit()
        
        with pytest.raises(Exception) as exc_info:
            multiplayer_service.register_for_tournament(
                tournament_id=tournament.id,
                user_id=extra_user.id,
                db=db
            )
        assert "full" in str(exc_info.value).lower()
    
    def test_tournament_bracket_generation(
        self, multiplayer_service, sample_users, db: Session
    ):
        """Test tournament bracket generation"""
        # Create tournament with participants
        tournament = Tournament(
            name="Bracket Test",
            creator_id=sample_users[0].id,
            format="single_elimination",
            max_participants=4,
            current_participants=4,
            status="registration"
        )
        db.add(tournament)
        db.commit()
        
        # Add participants
        for user in sample_users:
            db.add(TournamentParticipant(
                tournament_id=tournament.id,
                user_id=user.id,
                seed=user.level  # Seed by level
            ))
        db.commit()
        
        # Generate bracket
        bracket = multiplayer_service.generate_tournament_bracket(
            tournament_id=tournament.id,
            db=db
        )
        
        assert len(bracket['rounds']) > 0
        assert len(bracket['rounds'][0]['matches']) == 2  # 4 players = 2 first round matches
        
        # Check matchups (higher seeds vs lower seeds)
        first_match = bracket['rounds'][0]['matches'][0]
        assert first_match['player1']['seed'] < first_match['player2']['seed']
    
    def test_tournament_progression(
        self, multiplayer_service, sample_users, db: Session
    ):
        """Test tournament match progression"""
        # Create active tournament
        tournament = Tournament(
            name="Progress Test",
            creator_id=sample_users[0].id,
            format="single_elimination",
            status="in_progress",
            current_round=1
        )
        db.add(tournament)
        db.commit()
        
        # Create first round match
        battle = Battle(
            title=f"Tournament: {tournament.name} - Round 1",
            tournament_id=tournament.id,
            creator_id=sample_users[0].id,
            max_participants=2,
            current_participants=2,
            status="completed",
            winner_id=sample_users[0].id
        )
        db.add(battle)
        db.commit()
        
        # Update tournament participants
        winner = TournamentParticipant(
            tournament_id=tournament.id,
            user_id=sample_users[0].id,
            current_round=2,
            is_eliminated=False
        )
        loser = TournamentParticipant(
            tournament_id=tournament.id,
            user_id=sample_users[1].id,
            current_round=1,
            is_eliminated=True
        )
        db.add(winner)
        db.add(loser)
        db.commit()
        
        # Progress tournament
        next_round = multiplayer_service.progress_tournament(
            tournament_id=tournament.id,
            db=db
        )
        
        assert next_round.round_number == 2
        assert len(next_round.matches) > 0


class TestStudyGroups:
    """Test collaborative study group functionality"""
    
    def test_create_study_group(self, multiplayer_service, sample_users, db: Session):
        """Test creating a study group"""
        leader = sample_users[0]
        
        group_data = StudyGroupCreate(
            name="Advanced Math Study",
            description="Preparing for exams together",
            subject="math",
            max_members=6,
            is_public=True,
            requirements={
                "min_level": 5,
                "subjects": ["math"]
            }
        )
        
        group = multiplayer_service.create_study_group(
            leader_id=leader.id,
            group_data=group_data,
            db=db
        )
        
        assert group.name == "Advanced Math Study"
        assert group.leader_id == leader.id
        assert group.current_members == 1
        assert group.is_active is True
        
        # Check leader was added as member
        member = db.query(StudyGroupMember).filter(
            StudyGroupMember.group_id == group.id,
            StudyGroupMember.user_id == leader.id
        ).first()
        assert member is not None
        assert member.role == "leader"
    
    def test_join_study_group(self, multiplayer_service, sample_users, db: Session):
        """Test joining a study group"""
        # Create group
        group = StudyGroup(
            name="Open Study Group",
            leader_id=sample_users[0].id,
            subject="science",
            max_members=5,
            current_members=1,
            is_public=True,
            is_active=True
        )
        db.add(group)
        db.commit()
        
        # Add leader
        db.add(StudyGroupMember(
            group_id=group.id,
            user_id=sample_users[0].id,
            role="leader"
        ))
        db.commit()
        
        # Other users join
        for i in range(1, 3):
            result = multiplayer_service.join_study_group(
                group_id=group.id,
                user_id=sample_users[i].id,
                db=db
            )
            assert result.success is True
        
        # Check members
        group = db.query(StudyGroup).filter(StudyGroup.id == group.id).first()
        assert group.current_members == 3
        
        members = db.query(StudyGroupMember).filter(
            StudyGroupMember.group_id == group.id
        ).all()
        assert len(members) == 3
    
    def test_study_group_activities(
        self, multiplayer_service, sample_users, db: Session
    ):
        """Test study group collaborative activities"""
        # Create group with members
        group = StudyGroup(
            name="Active Study Group",
            leader_id=sample_users[0].id,
            subject="math",
            current_members=3,
            total_xp_earned=0,
            is_active=True
        )
        db.add(group)
        db.commit()
        
        # Add members
        for i in range(3):
            db.add(StudyGroupMember(
                group_id=group.id,
                user_id=sample_users[i].id,
                role="leader" if i == 0 else "member",
                contribution_points=0
            ))
        db.commit()
        
        # Start group activity
        activity = multiplayer_service.start_group_activity(
            group_id=group.id,
            activity_type="collaborative_quest",
            quest_id=1,
            db=db
        )
        
        assert activity.status == "in_progress"
        assert activity.participants_count == 3
        
        # Members contribute
        for i in range(3):
            contribution = multiplayer_service.add_activity_contribution(
                activity_id=activity.id,
                user_id=sample_users[i].id,
                contribution_type="answer_question",
                value=25,
                db=db
            )
            assert contribution.success is True
        
        # Complete activity
        completion = multiplayer_service.complete_group_activity(
            activity_id=activity.id,
            db=db
        )
        
        assert completion.success is True
        assert completion.total_contribution == 75
        assert completion.rewards is not None
        
        # Check XP distribution
        members = db.query(StudyGroupMember).filter(
            StudyGroupMember.group_id == group.id
        ).all()
        for member in members:
            assert member.contribution_points > 0
    
    def test_study_group_chat_and_resources(
        self, multiplayer_service, sample_users, db: Session
    ):
        """Test study group communication and resource sharing"""
        # Create group
        group = StudyGroup(
            name="Resource Sharing Group",
            leader_id=sample_users[0].id,
            current_members=2,
            is_active=True
        )
        db.add(group)
        db.commit()
        
        # Share resource
        resource = multiplayer_service.share_group_resource(
            group_id=group.id,
            user_id=sample_users[0].id,
            resource_type="note",
            resource_data={
                "title": "Chapter 5 Summary",
                "content": "Key points from chapter 5...",
                "tags": ["math", "algebra"]
            },
            db=db
        )
        
        assert resource.id is not None
        assert resource.shared_by == sample_users[0].id
        
        # Post message
        message = multiplayer_service.post_group_message(
            group_id=group.id,
            user_id=sample_users[0].id,
            message="Let's review chapter 5 together!",
            message_type="announcement",
            db=db
        )
        
        assert message.id is not None
        assert message.is_announcement is True


class TestMultiplayerMatchmaking:
    """Test matchmaking system"""
    
    def test_skill_based_matchmaking(
        self, multiplayer_service, db: Session
    ):
        """Test skill-based matchmaking"""
        # Create players with different skill levels
        players = []
        for i in range(10):
            player = User(
                email=f"skill{i}@example.com",
                username=f"skill{i}",
                level=1 + (i // 2),
                experience=100 * i
            )
            players.append(player)
            db.add(player)
        db.commit()
        
        # Request match for mid-level player
        requesting_player = players[5]  # Level 3
        
        match_result = multiplayer_service.find_match(
            user_id=requesting_player.id,
            game_type="battle",
            subject="math",
            preferences={
                "skill_range": 2,  # +/- 2 levels
                "max_wait_time": 30
            },
            db=db
        )
        
        if match_result.match_found:
            opponent = db.query(User).filter(
                User.id == match_result.opponent_id
            ).first()
            
            # Check skill matching
            level_diff = abs(opponent.level - requesting_player.level)
            assert level_diff <= 2
    
    def test_quick_match(self, multiplayer_service, sample_users, db: Session):
        """Test quick match functionality"""
        # Create waiting battles
        for i in range(2):
            battle = Battle(
                title=f"Quick Match {i}",
                creator_id=sample_users[i].id,
                subject="any",
                difficulty="any",
                max_participants=2,
                current_participants=1,
                status="waiting",
                is_private=False
            )
            db.add(battle)
            
            # Add creator as participant
            db.add(BattleParticipant(
                battle_id=battle.id,
                user_id=sample_users[i].id
            ))
        db.commit()
        
        # Player looking for quick match
        result = multiplayer_service.quick_match(
            user_id=sample_users[2].id,
            db=db
        )
        
        assert result.success is True
        assert result.battle_id is not None
        assert result.match_type == "join_existing"
    
    def test_create_private_match(
        self, multiplayer_service, sample_users, db: Session
    ):
        """Test creating private matches with codes"""
        creator = sample_users[0]
        
        # Create private battle
        private_battle = multiplayer_service.create_private_battle(
            creator_id=creator.id,
            battle_settings={
                "subject": "science",
                "difficulty": "hard",
                "max_rounds": 5
            },
            db=db
        )
        
        assert private_battle.is_private is True
        assert private_battle.join_code is not None
        assert len(private_battle.join_code) == 6  # 6-character code
        
        # Join with code
        join_result = multiplayer_service.join_with_code(
            user_id=sample_users[1].id,
            join_code=private_battle.join_code,
            db=db
        )
        
        assert join_result.success is True
        assert join_result.battle_id == private_battle.id
        
        # Try invalid code
        with pytest.raises(Exception) as exc_info:
            multiplayer_service.join_with_code(
                user_id=sample_users[2].id,
                join_code="INVALID",
                db=db
            )
        assert "not found" in str(exc_info.value).lower()


class TestMultiplayerRewards:
    """Test multiplayer reward system"""
    
    def test_battle_rewards_calculation(
        self, multiplayer_service, sample_users, db: Session
    ):
        """Test battle reward calculations"""
        winner = sample_users[0]
        loser = sample_users[1]
        
        # Calculate rewards based on performance
        rewards = multiplayer_service.calculate_battle_rewards(
            winner_id=winner.id,
            loser_id=loser.id,
            battle_stats={
                "duration": 300,  # 5 minutes
                "winner_score": 250,
                "loser_score": 150,
                "total_rounds": 5,
                "perfect_rounds": 2  # Winner got 2 perfect rounds
            },
            db=db
        )
        
        # Winner rewards
        assert rewards['winner']['experience'] >= 100
        assert rewards['winner']['gold'] >= 50
        assert rewards['winner']['rating_change'] > 0
        
        # Loser rewards (consolation)
        assert rewards['loser']['experience'] >= 25
        assert rewards['loser']['gold'] >= 10
        assert rewards['loser']['rating_change'] < 0
        
        # Bonus rewards for performance
        if 'perfect_bonus' in rewards['winner']:
            assert rewards['winner']['perfect_bonus'] > 0
    
    def test_tournament_prize_distribution(
        self, multiplayer_service, sample_users, db: Session
    ):
        """Test tournament prize distribution"""
        # Create completed tournament
        tournament = Tournament(
            name="Prize Tournament",
            creator_id=sample_users[0].id,
            status="completed",
            prize_pool={
                "1st": {"gold": 1000, "gems": 100, "items": ["legendary_badge"]},
                "2nd": {"gold": 500, "gems": 50},
                "3rd": {"gold": 250, "gems": 25}
            }
        )
        db.add(tournament)
        db.commit()
        
        # Add final standings
        standings = [
            (sample_users[0].id, 1),  # 1st place
            (sample_users[1].id, 2),  # 2nd place
            (sample_users[2].id, 3),  # 3rd place
            (sample_users[3].id, 4),  # 4th place
        ]
        
        for user_id, place in standings:
            db.add(TournamentParticipant(
                tournament_id=tournament.id,
                user_id=user_id,
                final_position=place,
                is_eliminated=True
            ))
        db.commit()
        
        # Distribute prizes
        distribution = multiplayer_service.distribute_tournament_prizes(
            tournament_id=tournament.id,
            db=db
        )
        
        assert len(distribution.prize_winners) == 3
        assert distribution.prize_winners[0]['prize']['gold'] == 1000
        assert distribution.prize_winners[1]['prize']['gold'] == 500
        assert distribution.prize_winners[2]['prize']['gold'] == 250
        
        # Check special items
        assert 'items' in distribution.prize_winners[0]['prize']
    
    def test_study_group_collective_rewards(
        self, multiplayer_service, sample_users, db: Session
    ):
        """Test study group collective achievement rewards"""
        # Create study group with achievement
        group = StudyGroup(
            name="Achievement Group",
            leader_id=sample_users[0].id,
            current_members=3,
            total_xp_earned=5000,  # Group achievement threshold
            quests_completed=10,
            is_active=True
        )
        db.add(group)
        db.commit()
        
        # Check and distribute group achievement rewards
        achievements = multiplayer_service.check_group_achievements(
            group_id=group.id,
            db=db
        )
        
        if achievements:
            for achievement in achievements:
                if achievement.name == "Power Squad":
                    assert achievement.rewards['gold'] >= 200
                    assert achievement.rewards['group_badge'] is not None
                    
                    # All members should receive rewards
                    assert len(achievement.recipients) == 3


class TestMultiplayerAPI:
    """Test multiplayer API endpoints"""
    
    def test_get_active_battles(
        self, client: TestClient, normal_user_token: str, db: Session
    ):
        """Test getting list of active battles"""
        response = client.get(
            "/api/v1/multiplayer/battles",
            headers={"Authorization": f"Bearer {normal_user_token}"},
            params={"status": "waiting", "limit": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "battles" in data
        assert "total" in data
    
    def test_create_battle_api(
        self, client: TestClient, normal_user_token: str
    ):
        """Test creating battle via API"""
        response = client.post(
            "/api/v1/multiplayer/battles",
            headers={"Authorization": f"Bearer {normal_user_token}"},
            json={
                "title": "API Battle Test",
                "subject": "math",
                "difficulty": "medium",
                "max_rounds": 5,
                "time_per_round": 30
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "API Battle Test"
        assert data["status"] == "waiting"
        assert "join_code" in data
    
    def test_websocket_battle_events(
        self, client: TestClient, normal_user_token: str
    ):
        """Test WebSocket events during battle"""
        # This would be tested in websocket integration tests
        pass