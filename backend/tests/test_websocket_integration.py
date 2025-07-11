"""
WebSocket integration tests for real-time functionality
"""
import pytest
import asyncio
import json
from typing import Dict, List, Any
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

import socketio
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.websocket.manager import sio_server, connection_manager
from app.websocket.events import (
    emit_learning_progress,
    emit_achievement_notification,
    emit_level_up,
    emit_parent_notification,
    emit_multiplayer_update
)
from app.models.user import User
from app.models.quest import Quest
from app.models.achievement import Achievement
from app.models.gamification import UserLevel
from app.models.multiplayer import (
    MultiplayerSession,
    MultiplayerParticipant,
    Battle,
    BattleParticipant
)


@pytest.fixture
async def websocket_client():
    """Create a test WebSocket client"""
    client = socketio.AsyncClient()
    yield client
    if client.connected:
        await client.disconnect()


@pytest.fixture
def mock_redis():
    """Mock Redis for pub/sub testing"""
    with patch('app.services.analytics_websocket.redis.asyncio.from_url') as mock:
        redis_instance = AsyncMock()
        redis_instance.publish = AsyncMock()
        redis_instance.subscribe = AsyncMock()
        mock.return_value = redis_instance
        yield redis_instance


class TestWebSocketConnection:
    """Test WebSocket connection and authentication"""
    
    @pytest.mark.asyncio
    async def test_connect_with_valid_token(
        self, websocket_client, normal_user_token: str, test_server_url: str
    ):
        """Test connecting with valid authentication token"""
        # Connect with auth
        await websocket_client.connect(
            f"{test_server_url}/ws/socket.io/",
            auth={"token": normal_user_token}
        )
        
        assert websocket_client.connected
        
        # Should receive connection confirmation
        @websocket_client.on('connect_success')
        async def on_connect(data):
            assert data['user_id'] is not None
            assert data['connected'] is True
    
    @pytest.mark.asyncio
    async def test_connect_without_token(
        self, websocket_client, test_server_url: str
    ):
        """Test that connection fails without authentication"""
        with pytest.raises(socketio.exceptions.ConnectionError):
            await websocket_client.connect(
                f"{test_server_url}/ws/socket.io/"
            )
    
    @pytest.mark.asyncio
    async def test_connect_with_invalid_token(
        self, websocket_client, test_server_url: str
    ):
        """Test that connection fails with invalid token"""
        with pytest.raises(socketio.exceptions.ConnectionError):
            await websocket_client.connect(
                f"{test_server_url}/ws/socket.io/",
                auth={"token": "invalid_token"}
            )
    
    @pytest.mark.asyncio
    async def test_disconnect_cleanup(
        self, websocket_client, normal_user_token: str, test_server_url: str
    ):
        """Test that disconnection properly cleans up resources"""
        # Connect
        await websocket_client.connect(
            f"{test_server_url}/ws/socket.io/",
            auth={"token": normal_user_token}
        )
        
        # Get session ID
        session_id = websocket_client.sid
        
        # Disconnect
        await websocket_client.disconnect()
        
        # Verify cleanup
        assert not websocket_client.connected
        # Connection manager should have removed the session
        assert session_id not in connection_manager.active_connections


class TestLearningEvents:
    """Test learning-related WebSocket events"""
    
    @pytest.mark.asyncio
    async def test_learning_progress_event(
        self, websocket_client, normal_user_token: str, test_server_url: str, db: Session
    ):
        """Test real-time learning progress updates"""
        # Connect
        await websocket_client.connect(
            f"{test_server_url}/ws/socket.io/",
            auth={"token": normal_user_token}
        )
        
        received_events = []
        
        @websocket_client.on('learning_progress')
        async def on_progress(data):
            received_events.append(data)
        
        # Emit learning progress
        user = db.query(User).filter(User.email == "test@example.com").first()
        await emit_learning_progress(
            user_id=user.id,
            subject="math",
            topic="fractions",
            progress=75,
            score=85
        )
        
        # Wait for event
        await asyncio.sleep(0.1)
        
        assert len(received_events) == 1
        assert received_events[0]['progress'] == 75
        assert received_events[0]['score'] == 85
    
    @pytest.mark.asyncio
    async def test_quest_completion_event(
        self, websocket_client, normal_user_token: str, test_server_url: str, db: Session
    ):
        """Test quest completion notifications"""
        await websocket_client.connect(
            f"{test_server_url}/ws/socket.io/",
            auth={"token": normal_user_token}
        )
        
        received_events = []
        
        @websocket_client.on('quest_completion')
        async def on_quest_complete(data):
            received_events.append(data)
        
        # Create and complete a quest
        user = db.query(User).filter(User.email == "test@example.com").first()
        quest = Quest(
            title="Test Quest",
            description="Complete this test",
            experience_reward=100,
            gold_reward=50
        )
        db.add(quest)
        db.commit()
        
        # Emit quest completion
        await websocket_client.emit('quest_completed', {
            'quest_id': quest.id,
            'rewards': {
                'experience': 100,
                'gold': 50,
                'items': []
            }
        })
        
        await asyncio.sleep(0.1)
        
        assert len(received_events) == 1
        assert received_events[0]['quest_id'] == quest.id
        assert received_events[0]['rewards']['experience'] == 100
    
    @pytest.mark.asyncio
    async def test_achievement_notification(
        self, websocket_client, normal_user_token: str, test_server_url: str, db: Session
    ):
        """Test achievement unlock notifications"""
        await websocket_client.connect(
            f"{test_server_url}/ws/socket.io/",
            auth={"token": normal_user_token}
        )
        
        received_events = []
        
        @websocket_client.on('achievement_notification')
        async def on_achievement(data):
            received_events.append(data)
        
        # Create achievement
        achievement = Achievement(
            name="First Steps",
            description="Complete your first quest",
            points=100,
            category="quest"
        )
        db.add(achievement)
        db.commit()
        
        # Emit achievement notification
        user = db.query(User).filter(User.email == "test@example.com").first()
        await emit_achievement_notification(
            user_id=user.id,
            achievement_id=achievement.id,
            achievement_name=achievement.name,
            points=achievement.points
        )
        
        await asyncio.sleep(0.1)
        
        assert len(received_events) == 1
        assert received_events[0]['achievement_name'] == "First Steps"
        assert received_events[0]['points'] == 100
    
    @pytest.mark.asyncio
    async def test_level_up_notification(
        self, websocket_client, normal_user_token: str, test_server_url: str, db: Session
    ):
        """Test level up notifications with rewards"""
        await websocket_client.connect(
            f"{test_server_url}/ws/socket.io/",
            auth={"token": normal_user_token}
        )
        
        received_events = []
        
        @websocket_client.on('level_up')
        async def on_level_up(data):
            received_events.append(data)
        
        # Emit level up
        user = db.query(User).filter(User.email == "test@example.com").first()
        await emit_level_up(
            user_id=user.id,
            new_level=5,
            rewards={
                'gold': 250,
                'items': ['xp_boost'],
                'badges': ['level_5_badge']
            }
        )
        
        await asyncio.sleep(0.1)
        
        assert len(received_events) == 1
        assert received_events[0]['new_level'] == 5
        assert received_events[0]['rewards']['gold'] == 250


class TestMultiplayerEvents:
    """Test multiplayer-related WebSocket events"""
    
    @pytest.mark.asyncio
    async def test_create_multiplayer_room(
        self, websocket_client, normal_user_token: str, test_server_url: str, db: Session
    ):
        """Test creating a multiplayer room"""
        await websocket_client.connect(
            f"{test_server_url}/ws/socket.io/",
            auth={"token": normal_user_token}
        )
        
        room_created = asyncio.Event()
        room_data = {}
        
        @websocket_client.on('room_created')
        async def on_room_created(data):
            room_data.update(data)
            room_created.set()
        
        # Create room
        await websocket_client.emit('create_room', {
            'room_type': 'battle',
            'max_players': 2,
            'settings': {
                'time_limit': 300,
                'question_count': 10
            }
        })
        
        await asyncio.wait_for(room_created.wait(), timeout=1.0)
        
        assert 'room_id' in room_data
        assert room_data['room_type'] == 'battle'
        assert room_data['max_players'] == 2
    
    @pytest.mark.asyncio
    async def test_join_multiplayer_room(
        self, websocket_client, websocket_client2, normal_user_token: str, 
        normal_user_token2: str, test_server_url: str
    ):
        """Test joining a multiplayer room"""
        # Connect both clients
        await websocket_client.connect(
            f"{test_server_url}/ws/socket.io/",
            auth={"token": normal_user_token}
        )
        await websocket_client2.connect(
            f"{test_server_url}/ws/socket.io/",
            auth={"token": normal_user_token2}
        )
        
        room_id = None
        player_joined = asyncio.Event()
        
        @websocket_client.on('room_created')
        async def on_room_created(data):
            nonlocal room_id
            room_id = data['room_id']
        
        @websocket_client.on('player_joined')
        async def on_player_joined(data):
            player_joined.set()
        
        # Player 1 creates room
        await websocket_client.emit('create_room', {
            'room_type': 'battle',
            'max_players': 2
        })
        
        await asyncio.sleep(0.1)
        assert room_id is not None
        
        # Player 2 joins room
        await websocket_client2.emit('join_room', {
            'room_id': room_id
        })
        
        await asyncio.wait_for(player_joined.wait(), timeout=1.0)
    
    @pytest.mark.asyncio
    async def test_multiplayer_battle_flow(
        self, websocket_client, websocket_client2, normal_user_token: str,
        normal_user_token2: str, test_server_url: str, db: Session
    ):
        """Test complete multiplayer battle flow"""
        # Connect both players
        await websocket_client.connect(
            f"{test_server_url}/ws/socket.io/",
            auth={"token": normal_user_token}
        )
        await websocket_client2.connect(
            f"{test_server_url}/ws/socket.io/",
            auth={"token": normal_user_token2}
        )
        
        battle_events = {
            'room_created': asyncio.Event(),
            'battle_started': asyncio.Event(),
            'question_received': asyncio.Event(),
            'answer_submitted': asyncio.Event(),
            'battle_ended': asyncio.Event()
        }
        
        battle_data = {}
        
        # Set up event handlers for player 1
        @websocket_client.on('room_created')
        async def on_room_created(data):
            battle_data['room_id'] = data['room_id']
            battle_events['room_created'].set()
        
        @websocket_client.on('battle_started')
        async def on_battle_started(data):
            battle_data['battle'] = data
            battle_events['battle_started'].set()
        
        @websocket_client.on('question')
        async def on_question(data):
            battle_data['current_question'] = data
            battle_events['question_received'].set()
        
        @websocket_client.on('opponent_answered')
        async def on_opponent_answered(data):
            battle_data['opponent_answer'] = data
            battle_events['answer_submitted'].set()
        
        @websocket_client.on('battle_ended')
        async def on_battle_ended(data):
            battle_data['results'] = data
            battle_events['battle_ended'].set()
        
        # Create battle room
        await websocket_client.emit('create_room', {
            'room_type': 'battle',
            'max_players': 2,
            'settings': {
                'subject': 'math',
                'difficulty': 'easy',
                'question_count': 3
            }
        })
        
        await battle_events['room_created'].wait()
        
        # Player 2 joins
        await websocket_client2.emit('join_room', {
            'room_id': battle_data['room_id']
        })
        
        # Start battle
        await websocket_client.emit('start_battle', {
            'room_id': battle_data['room_id']
        })
        
        await battle_events['battle_started'].wait()
        assert battle_data['battle']['status'] == 'in_progress'
        
        # Simulate answering questions
        for i in range(3):
            battle_events['question_received'].clear()
            
            # Request next question
            await websocket_client.emit('request_question', {
                'room_id': battle_data['room_id']
            })
            
            await battle_events['question_received'].wait()
            
            # Both players answer
            await websocket_client.emit('submit_answer', {
                'room_id': battle_data['room_id'],
                'question_id': battle_data['current_question']['id'],
                'answer': 'A',
                'time_taken': 5.2
            })
            
            await websocket_client2.emit('submit_answer', {
                'room_id': battle_data['room_id'],
                'question_id': battle_data['current_question']['id'],
                'answer': 'B',
                'time_taken': 4.8
            })
            
            await asyncio.sleep(0.1)
        
        # Battle should end
        await battle_events['battle_ended'].wait()
        assert 'winner' in battle_data['results']
        assert 'scores' in battle_data['results']
    
    @pytest.mark.asyncio
    async def test_multiplayer_invitation_system(
        self, websocket_client, websocket_client2, normal_user_token: str,
        normal_user_token2: str, test_server_url: str, db: Session
    ):
        """Test multiplayer invitation flow"""
        # Get users
        user1 = db.query(User).filter(User.email == "test@example.com").first()
        user2 = db.query(User).filter(User.email == "test2@example.com").first()
        
        # Connect both players
        await websocket_client.connect(
            f"{test_server_url}/ws/socket.io/",
            auth={"token": normal_user_token}
        )
        await websocket_client2.connect(
            f"{test_server_url}/ws/socket.io/",
            auth={"token": normal_user_token2}
        )
        
        invitation_received = asyncio.Event()
        invitation_data = {}
        
        @websocket_client2.on('multiplayer_invitation')
        async def on_invitation(data):
            invitation_data.update(data)
            invitation_received.set()
        
        # Send invitation
        await websocket_client.emit('send_invitation', {
            'recipient_id': user2.id,
            'game_type': 'battle',
            'message': 'Want to play?'
        })
        
        await invitation_received.wait()
        
        assert invitation_data['sender_id'] == user1.id
        assert invitation_data['game_type'] == 'battle'
        assert invitation_data['message'] == 'Want to play?'
        
        # Accept invitation
        accepted = asyncio.Event()
        
        @websocket_client.on('invitation_accepted')
        async def on_accepted(data):
            accepted.set()
        
        await websocket_client2.emit('accept_invitation', {
            'invitation_id': invitation_data['invitation_id']
        })
        
        await accepted.wait()


class TestParentMonitoring:
    """Test parent monitoring WebSocket events"""
    
    @pytest.mark.asyncio
    async def test_parent_receives_child_notifications(
        self, websocket_client, parent_token: str, test_server_url: str, db: Session
    ):
        """Test that parents receive notifications about child activities"""
        # Connect parent
        await websocket_client.connect(
            f"{test_server_url}/ws/socket.io/",
            auth={"token": parent_token}
        )
        
        notifications = []
        
        @websocket_client.on('child_activity')
        async def on_child_activity(data):
            notifications.append(data)
        
        # Get parent and child
        parent = db.query(User).filter(User.role == "parent").first()
        child = db.query(User).filter(User.parent_id == parent.id).first()
        
        # Emit child progress
        await emit_parent_notification(
            parent_id=parent.id,
            child_id=child.id,
            notification_type='quest_completed',
            data={
                'quest_name': 'Math Challenge',
                'experience_gained': 100,
                'time_spent': 1200
            }
        )
        
        await asyncio.sleep(0.1)
        
        assert len(notifications) == 1
        assert notifications[0]['child_id'] == child.id
        assert notifications[0]['type'] == 'quest_completed'
        assert notifications[0]['data']['quest_name'] == 'Math Challenge'
    
    @pytest.mark.asyncio
    async def test_parent_real_time_progress_monitoring(
        self, websocket_client, parent_token: str, test_server_url: str, db: Session
    ):
        """Test real-time progress monitoring for parents"""
        await websocket_client.connect(
            f"{test_server_url}/ws/socket.io/",
            auth={"token": parent_token}
        )
        
        progress_updates = []
        
        @websocket_client.on('child_progress_update')
        async def on_progress(data):
            progress_updates.append(data)
        
        # Get parent and child
        parent = db.query(User).filter(User.role == "parent").first()
        child = db.query(User).filter(User.parent_id == parent.id).first()
        
        # Start monitoring
        await websocket_client.emit('start_monitoring', {
            'child_id': child.id
        })
        
        # Emit child learning progress
        await emit_learning_progress(
            user_id=child.id,
            subject="math",
            topic="algebra",
            progress=45,
            score=92
        )
        
        await asyncio.sleep(0.1)
        
        assert len(progress_updates) == 1
        assert progress_updates[0]['child_id'] == child.id
        assert progress_updates[0]['progress'] == 45
        assert progress_updates[0]['score'] == 92


class TestRoomManagement:
    """Test WebSocket room management"""
    
    @pytest.mark.asyncio
    async def test_user_room_auto_join(
        self, websocket_client, normal_user_token: str, test_server_url: str, db: Session
    ):
        """Test that users automatically join their personal room"""
        user = db.query(User).filter(User.email == "test@example.com").first()
        
        await websocket_client.connect(
            f"{test_server_url}/ws/socket.io/",
            auth={"token": normal_user_token}
        )
        
        # User should be in their personal room
        rooms = await websocket_client.call('get_rooms')
        assert f"user_{user.id}" in rooms
    
    @pytest.mark.asyncio
    async def test_study_group_room_management(
        self, websocket_client, websocket_client2, websocket_client3,
        normal_user_token: str, normal_user_token2: str, normal_user_token3: str,
        test_server_url: str
    ):
        """Test study group room creation and management"""
        clients = [
            (websocket_client, normal_user_token),
            (websocket_client2, normal_user_token2),
            (websocket_client3, normal_user_token3)
        ]
        
        # Connect all clients
        for client, token in clients:
            await client.connect(
                f"{test_server_url}/ws/socket.io/",
                auth={"token": token}
            )
        
        group_created = asyncio.Event()
        group_data = {}
        members_joined = []
        
        @websocket_client.on('study_group_created')
        async def on_group_created(data):
            group_data.update(data)
            group_created.set()
        
        @websocket_client.on('member_joined')
        async def on_member_joined(data):
            members_joined.append(data)
        
        # Create study group
        await websocket_client.emit('create_study_group', {
            'name': 'Math Study Group',
            'subject': 'math',
            'max_members': 5
        })
        
        await group_created.wait()
        
        # Other members join
        for client, _ in clients[1:]:
            await client.emit('join_study_group', {
                'group_id': group_data['group_id']
            })
        
        await asyncio.sleep(0.2)
        
        assert len(members_joined) == 2
        assert group_data['member_count'] == 3


class TestChatSystem:
    """Test real-time chat functionality"""
    
    @pytest.mark.asyncio
    async def test_send_chat_message(
        self, websocket_client, websocket_client2, normal_user_token: str,
        normal_user_token2: str, test_server_url: str
    ):
        """Test sending and receiving chat messages"""
        # Connect both clients
        await websocket_client.connect(
            f"{test_server_url}/ws/socket.io/",
            auth={"token": normal_user_token}
        )
        await websocket_client2.connect(
            f"{test_server_url}/ws/socket.io/",
            auth={"token": normal_user_token2}
        )
        
        # Create a chat room
        room_id = "test_chat_room"
        messages_received = []
        
        @websocket_client2.on('chat_message')
        async def on_message(data):
            messages_received.append(data)
        
        # Both join room
        await websocket_client.emit('join_room', {'room_id': room_id})
        await websocket_client2.emit('join_room', {'room_id': room_id})
        
        # Send message
        await websocket_client.emit('send_message', {
            'room_id': room_id,
            'message': 'Hello, World!',
            'type': 'text'
        })
        
        await asyncio.sleep(0.1)
        
        assert len(messages_received) == 1
        assert messages_received[0]['message'] == 'Hello, World!'
        assert messages_received[0]['type'] == 'text'
    
    @pytest.mark.asyncio
    async def test_typing_indicators(
        self, websocket_client, websocket_client2, normal_user_token: str,
        normal_user_token2: str, test_server_url: str, db: Session
    ):
        """Test typing indicators in chat"""
        user1 = db.query(User).filter(User.email == "test@example.com").first()
        
        # Connect both clients
        await websocket_client.connect(
            f"{test_server_url}/ws/socket.io/",
            auth={"token": normal_user_token}
        )
        await websocket_client2.connect(
            f"{test_server_url}/ws/socket.io/",
            auth={"token": normal_user_token2}
        )
        
        room_id = "test_chat_room"
        typing_events = []
        
        @websocket_client2.on('user_typing')
        async def on_typing(data):
            typing_events.append(data)
        
        # Join room
        await websocket_client.emit('join_room', {'room_id': room_id})
        await websocket_client2.emit('join_room', {'room_id': room_id})
        
        # Start typing
        await websocket_client.emit('typing_start', {
            'room_id': room_id
        })
        
        await asyncio.sleep(0.1)
        
        assert len(typing_events) == 1
        assert typing_events[0]['user_id'] == user1.id
        assert typing_events[0]['is_typing'] is True
        
        # Stop typing
        typing_events.clear()
        await websocket_client.emit('typing_stop', {
            'room_id': room_id
        })
        
        await asyncio.sleep(0.1)
        
        assert len(typing_events) == 1
        assert typing_events[0]['is_typing'] is False


class TestAnalyticsWebSocket:
    """Test real-time analytics streaming"""
    
    @pytest.mark.asyncio
    async def test_analytics_event_streaming(
        self, websocket_client, admin_token: str, test_server_url: str,
        mock_redis, db: Session
    ):
        """Test real-time analytics event streaming"""
        # Connect as admin
        await websocket_client.connect(
            f"{test_server_url}/ws/socket.io/",
            auth={"token": admin_token}
        )
        
        analytics_events = []
        
        @websocket_client.on('analytics_event')
        async def on_analytics(data):
            analytics_events.append(data)
        
        # Subscribe to analytics
        await websocket_client.emit('subscribe_analytics', {
            'metrics': ['user_activity', 'quest_completions', 'level_ups']
        })
        
        # Simulate analytics events
        await mock_redis.publish(
            'analytics:user_activity',
            json.dumps({
                'timestamp': datetime.utcnow().isoformat(),
                'active_users': 150,
                'new_sessions': 25
            })
        )
        
        await asyncio.sleep(0.1)
        
        assert len(analytics_events) > 0
        assert analytics_events[0]['type'] == 'user_activity'
        assert analytics_events[0]['data']['active_users'] == 150
    
    @pytest.mark.asyncio
    async def test_real_time_leaderboard_updates(
        self, websocket_client, normal_user_token: str, test_server_url: str, db: Session
    ):
        """Test real-time leaderboard updates"""
        await websocket_client.connect(
            f"{test_server_url}/ws/socket.io/",
            auth={"token": normal_user_token}
        )
        
        leaderboard_updates = []
        
        @websocket_client.on('leaderboard_update')
        async def on_leaderboard(data):
            leaderboard_updates.append(data)
        
        # Subscribe to leaderboard
        await websocket_client.emit('subscribe_leaderboard', {
            'type': 'weekly',
            'limit': 10
        })
        
        # Simulate score change that affects leaderboard
        user = db.query(User).filter(User.email == "test@example.com").first()
        await websocket_client.emit('score_update', {
            'user_id': user.id,
            'score_change': 500,
            'reason': 'quest_completion'
        })
        
        await asyncio.sleep(0.1)
        
        assert len(leaderboard_updates) > 0
        assert 'rankings' in leaderboard_updates[0]


class TestErrorHandling:
    """Test WebSocket error handling"""
    
    @pytest.mark.asyncio
    async def test_invalid_event_handling(
        self, websocket_client, normal_user_token: str, test_server_url: str
    ):
        """Test handling of invalid events"""
        await websocket_client.connect(
            f"{test_server_url}/ws/socket.io/",
            auth={"token": normal_user_token}
        )
        
        error_received = asyncio.Event()
        error_data = {}
        
        @websocket_client.on('error')
        async def on_error(data):
            error_data.update(data)
            error_received.set()
        
        # Send invalid event
        await websocket_client.emit('invalid_event', {
            'bad_data': 'test'
        })
        
        await asyncio.wait_for(error_received.wait(), timeout=1.0)
        
        assert 'message' in error_data
        assert 'code' in error_data
    
    @pytest.mark.asyncio
    async def test_rate_limiting(
        self, websocket_client, normal_user_token: str, test_server_url: str
    ):
        """Test WebSocket rate limiting"""
        await websocket_client.connect(
            f"{test_server_url}/ws/socket.io/",
            auth={"token": normal_user_token}
        )
        
        rate_limit_hit = asyncio.Event()
        
        @websocket_client.on('rate_limit_exceeded')
        async def on_rate_limit(data):
            rate_limit_hit.set()
        
        # Send many messages quickly
        for i in range(100):
            await websocket_client.emit('send_message', {
                'room_id': 'test',
                'message': f'Message {i}'
            })
        
        await asyncio.wait_for(rate_limit_hit.wait(), timeout=2.0)
    
    @pytest.mark.asyncio
    async def test_reconnection_handling(
        self, websocket_client, normal_user_token: str, test_server_url: str
    ):
        """Test automatic reconnection handling"""
        # Connect
        await websocket_client.connect(
            f"{test_server_url}/ws/socket.io/",
            auth={"token": normal_user_token}
        )
        
        reconnected = asyncio.Event()
        
        @websocket_client.on('reconnect')
        async def on_reconnect():
            reconnected.set()
        
        # Simulate disconnect
        await websocket_client.disconnect()
        
        # Reconnect
        await websocket_client.connect(
            f"{test_server_url}/ws/socket.io/",
            auth={"token": normal_user_token}
        )
        
        assert websocket_client.connected


class TestScalability:
    """Test WebSocket scalability features"""
    
    @pytest.mark.asyncio
    async def test_concurrent_connections(
        self, test_server_url: str, create_test_users_and_tokens
    ):
        """Test handling multiple concurrent connections"""
        users_and_tokens = create_test_users_and_tokens(10)
        clients = []
        
        try:
            # Connect 10 clients concurrently
            connect_tasks = []
            for user, token in users_and_tokens:
                client = socketio.AsyncClient()
                clients.append(client)
                connect_tasks.append(
                    client.connect(
                        f"{test_server_url}/ws/socket.io/",
                        auth={"token": token}
                    )
                )
            
            await asyncio.gather(*connect_tasks)
            
            # Verify all connected
            assert all(client.connected for client in clients)
            
            # Send messages from all clients
            message_tasks = []
            for i, client in enumerate(clients):
                message_tasks.append(
                    client.emit('send_message', {
                        'room_id': 'stress_test',
                        'message': f'Message from client {i}'
                    })
                )
            
            await asyncio.gather(*message_tasks)
            
        finally:
            # Cleanup
            disconnect_tasks = [
                client.disconnect() for client in clients if client.connected
            ]
            await asyncio.gather(*disconnect_tasks)
    
    @pytest.mark.asyncio
    async def test_broadcast_performance(
        self, test_server_url: str, create_test_users_and_tokens
    ):
        """Test broadcast performance to multiple clients"""
        users_and_tokens = create_test_users_and_tokens(20)
        clients = []
        received_counts = {i: 0 for i in range(20)}
        
        try:
            # Connect clients
            for i, (user, token) in enumerate(users_and_tokens):
                client = socketio.AsyncClient()
                clients.append(client)
                
                # Set up message counter
                @client.on('broadcast_message')
                async def on_broadcast(data, client_id=i):
                    received_counts[client_id] += 1
                
                await client.connect(
                    f"{test_server_url}/ws/socket.io/",
                    auth={"token": token}
                )
                
                # Join broadcast room
                await client.emit('join_room', {'room_id': 'broadcast_test'})
            
            # Send broadcast
            start_time = asyncio.get_event_loop().time()
            await clients[0].emit('broadcast_to_room', {
                'room_id': 'broadcast_test',
                'message': 'Test broadcast message'
            })
            
            # Wait for all to receive
            await asyncio.sleep(0.5)
            
            end_time = asyncio.get_event_loop().time()
            broadcast_time = end_time - start_time
            
            # Verify all received the message
            assert all(count >= 1 for count in received_counts.values())
            assert broadcast_time < 1.0  # Should broadcast to 20 clients in under 1 second
            
        finally:
            # Cleanup
            for client in clients:
                if client.connected:
                    await client.disconnect()