"""
WebSocket and Multiplayer test configuration and fixtures
"""
import pytest
import asyncio
from typing import List, Tuple
import socketio
from sqlalchemy.orm import Session

from app.models.user import User
from app.db.session import SessionLocal
from app.core.security import create_access_token


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_server_url():
    """WebSocket test server URL"""
    return "http://localhost:8000"


@pytest.fixture
async def websocket_client():
    """Create a test WebSocket client"""
    client = socketio.AsyncClient(
        logger=True,
        engineio_logger=True
    )
    yield client
    if client.connected:
        await client.disconnect()


@pytest.fixture
async def websocket_client2():
    """Create a second test WebSocket client"""
    client = socketio.AsyncClient()
    yield client
    if client.connected:
        await client.disconnect()


@pytest.fixture
async def websocket_client3():
    """Create a third test WebSocket client"""
    client = socketio.AsyncClient()
    yield client
    if client.connected:
        await client.disconnect()


@pytest.fixture
def normal_user_token2(db: Session) -> str:
    """Create a second test user and return token"""
    user = User(
        email="test2@example.com",
        username="testuser2",
        full_name="Test User 2",
        hashed_password="hashed",
        is_active=True,
        role="student"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return create_access_token(
        data={"sub": user.email, "user_id": user.id}
    )


@pytest.fixture
def normal_user_token3(db: Session) -> str:
    """Create a third test user and return token"""
    user = User(
        email="test3@example.com",
        username="testuser3",
        full_name="Test User 3",
        hashed_password="hashed",
        is_active=True,
        role="student"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return create_access_token(
        data={"sub": user.email, "user_id": user.id}
    )


@pytest.fixture
def parent_token(db: Session) -> str:
    """Create a parent user with child and return token"""
    # Create parent
    parent = User(
        email="parent@example.com",
        username="testparent",
        full_name="Test Parent",
        hashed_password="hashed",
        is_active=True,
        role="parent"
    )
    db.add(parent)
    db.commit()
    db.refresh(parent)
    
    # Create child linked to parent
    child = User(
        email="child@example.com",
        username="testchild",
        full_name="Test Child",
        hashed_password="hashed",
        is_active=True,
        role="student",
        parent_id=parent.id
    )
    db.add(child)
    db.commit()
    
    return create_access_token(
        data={"sub": parent.email, "user_id": parent.id}
    )


@pytest.fixture
def create_test_users_and_tokens(db: Session):
    """Factory to create multiple test users with tokens"""
    def _create_users(count: int) -> List[Tuple[User, str]]:
        users_and_tokens = []
        
        for i in range(count):
            user = User(
                email=f"player{i}@example.com",
                username=f"player{i}",
                full_name=f"Player {i}",
                hashed_password="hashed",
                is_active=True,
                role="student",
                level=5 + i
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            token = create_access_token(
                data={"sub": user.email, "user_id": user.id}
            )
            users_and_tokens.append((user, token))
        
        return users_and_tokens
    
    return _create_users


@pytest.fixture
def mock_websocket_server():
    """Mock WebSocket server for testing"""
    from app.websocket.manager import sio_server
    return sio_server


@pytest.fixture
async def connected_clients(
    websocket_client,
    websocket_client2,
    normal_user_token,
    normal_user_token2,
    test_server_url
):
    """Connect two clients and return them"""
    await websocket_client.connect(
        f"{test_server_url}/ws/socket.io/",
        auth={"token": normal_user_token}
    )
    await websocket_client2.connect(
        f"{test_server_url}/ws/socket.io/",
        auth={"token": normal_user_token2}
    )
    
    yield websocket_client, websocket_client2
    
    # Cleanup
    if websocket_client.connected:
        await websocket_client.disconnect()
    if websocket_client2.connected:
        await websocket_client2.disconnect()


@pytest.fixture
def battle_room_data():
    """Sample battle room configuration"""
    return {
        'room_type': 'battle',
        'max_players': 2,
        'settings': {
            'subject': 'math',
            'difficulty': 'medium',
            'time_limit': 300,
            'question_count': 5
        }
    }


@pytest.fixture
def study_group_data():
    """Sample study group configuration"""
    return {
        'name': 'Test Study Group',
        'subject': 'science',
        'max_members': 6,
        'description': 'A test study group for science',
        'is_public': True
    }


@pytest.fixture
async def cleanup_websocket_connections():
    """Cleanup any remaining WebSocket connections after tests"""
    yield
    # This would cleanup any remaining connections
    # Implementation depends on your WebSocket manager


# Async test markers
pytest.mark.asyncio_mode = "auto"