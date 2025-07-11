# WebSocket and Multiplayer Integration Testing

## Overview

Comprehensive integration tests for real-time WebSocket communication and multiplayer gaming features. These tests ensure reliable real-time interactions, proper event handling, and scalable multiplayer functionality.

## Test Structure

### WebSocket Integration Tests (`test_websocket_integration.py`)

#### 1. **Connection Management**
- Authentication validation
- Token-based connection
- Automatic reconnection
- Disconnection cleanup
- Connection state tracking

#### 2. **Learning Events**
- Real-time progress updates
- Quest completion notifications
- Achievement notifications
- Level up alerts with rewards
- Learning analytics streaming

#### 3. **Multiplayer Events**
- Room creation and management
- Player joining/leaving
- Battle flow (start to finish)
- Invitation system
- Real-time game state sync

#### 4. **Parent Monitoring**
- Child activity notifications
- Real-time progress tracking
- Achievement alerts
- Study time monitoring

#### 5. **Room Management**
- Auto-join personal rooms
- Study group rooms
- Battle/tournament rooms
- Broadcast rooms
- Private rooms with codes

#### 6. **Chat System**
- Real-time messaging
- Typing indicators
- Message reactions
- Read receipts
- Room-based chat

#### 7. **Analytics Streaming**
- Real-time metrics
- Leaderboard updates
- User activity tracking
- Performance monitoring

#### 8. **Error Handling**
- Invalid event handling
- Rate limiting
- Connection errors
- Authentication failures

#### 9. **Scalability Tests**
- Concurrent connections (10-20 clients)
- Broadcast performance
- Message throughput
- Room capacity

### Multiplayer Integration Tests (`test_multiplayer_integration.py`)

#### 1. **Battle System**
- Battle creation
- Player joining
- Ready system
- Round flow
- Answer submission
- Scoring system
- Battle completion
- Reward distribution

#### 2. **Tournament System**
- Tournament creation
- Registration process
- Bracket generation
- Match progression
- Prize distribution
- Elimination tracking

#### 3. **Study Groups**
- Group creation
- Member management
- Collaborative activities
- Resource sharing
- Group achievements
- Communication features

#### 4. **Matchmaking**
- Skill-based matching
- Quick match
- Private matches
- Join codes
- Preference matching

#### 5. **Reward System**
- Battle rewards
- Tournament prizes
- Group achievements
- Performance bonuses
- Rating changes

## Running Tests

### Prerequisites

```bash
# Install test dependencies
pip install pytest pytest-asyncio python-socketio[asyncio_client]

# Set up test environment
export TESTING=true
export DATABASE_URL="postgresql://user:pass@localhost/quest_test"
```

### Running WebSocket Tests

```bash
# Run all WebSocket tests
pytest tests/test_websocket_integration.py -v

# Run specific test class
pytest tests/test_websocket_integration.py::TestMultiplayerEvents -v

# Run with async support
pytest tests/test_websocket_integration.py -v --asyncio-mode=auto
```

### Running Multiplayer Tests

```bash
# Run all multiplayer tests
pytest tests/test_multiplayer_integration.py -v

# Run battle tests only
pytest tests/test_multiplayer_integration.py::TestBattleSystem -v

# Run with coverage
pytest tests/test_multiplayer_integration.py --cov=app.services.multiplayer
```

## Test Implementation Details

### WebSocket Test Client Setup

```python
@pytest.fixture
async def websocket_client():
    """Create test WebSocket client"""
    client = socketio.AsyncClient()
    yield client
    if client.connected:
        await client.disconnect()
```

### Multiple Client Testing

```python
# Test with multiple concurrent clients
async def test_multiplayer_interaction():
    clients = []
    for i in range(4):
        client = socketio.AsyncClient()
        await client.connect(url, auth={"token": tokens[i]})
        clients.append(client)
    
    # Test interactions between clients
    await clients[0].emit('create_room')
    await clients[1].emit('join_room')
```

### Event Handling

```python
# Set up event listeners
@websocket_client.on('battle_started')
async def on_battle_start(data):
    assert data['status'] == 'in_progress'
    
# Emit and wait for response
await websocket_client.emit('start_battle', {'room_id': room_id})
await asyncio.wait_for(battle_started.wait(), timeout=1.0)
```

### Mock Strategies

#### Mock Redis for Analytics
```python
@pytest.fixture
def mock_redis():
    with patch('app.services.analytics_websocket.redis') as mock:
        redis_instance = AsyncMock()
        redis_instance.publish = AsyncMock()
        yield redis_instance
```

#### Mock Question Generation
```python
with patch.object(service, '_generate_battle_question') as mock:
    mock.return_value = {
        'question': 'What is 2+2?',
        'options': ['3', '4', '5', '6'],
        'correct_answer': '4'
    }
```

## Test Scenarios

### Complete Battle Flow Test

1. **Room Creation**
   - Player 1 creates battle room
   - Receives room ID and join code

2. **Player Joining**
   - Player 2 joins with room ID
   - Both receive player_joined event

3. **Ready System**
   - Both players mark ready
   - Battle automatically starts

4. **Round Flow**
   - Question sent to both players
   - Players submit answers
   - Scores updated in real-time
   - Round winner announced

5. **Battle Completion**
   - Final scores calculated
   - Winner determined
   - Rewards distributed
   - Events sent to both players

### Tournament Progression Test

1. **Registration Phase**
   - Players register for tournament
   - Capacity tracking
   - Registration closes when full

2. **Bracket Generation**
   - Seeds assigned by skill
   - First round matchups created
   - Bracket visualization ready

3. **Match Progression**
   - Winners advance
   - Losers eliminated
   - Next round generated
   - Finals reached

4. **Prize Distribution**
   - Final standings determined
   - Prizes distributed by rank
   - Special achievements awarded

### Study Group Collaboration Test

1. **Group Formation**
   - Leader creates group
   - Sets requirements
   - Members join

2. **Activity Start**
   - Collaborative quest selected
   - All members notified
   - Progress tracking begins

3. **Contributions**
   - Members answer questions
   - Points accumulated
   - Real-time updates

4. **Completion**
   - Activity finished
   - Contributions calculated
   - Rewards distributed proportionally

## Performance Benchmarks

### WebSocket Metrics

- **Connection Time**: < 100ms
- **Message Latency**: < 50ms
- **Broadcast to 20 clients**: < 1s
- **Concurrent connections**: 100+
- **Messages per second**: 1000+

### Multiplayer Metrics

- **Battle creation**: < 200ms
- **Matchmaking**: < 2s
- **Round processing**: < 100ms
- **Leaderboard query**: < 100ms
- **Tournament bracket**: < 500ms

## Common Issues and Solutions

### Issue: WebSocket Connection Timeouts

**Solution**: Increase timeout in test fixtures
```python
await asyncio.wait_for(
    websocket_client.connect(url),
    timeout=5.0  # Increase from default 1.0
)
```

### Issue: Event Order Dependencies

**Solution**: Use event synchronization
```python
event_received = asyncio.Event()

@client.on('specific_event')
async def handler(data):
    # Process data
    event_received.set()

await event_received.wait()
```

### Issue: Race Conditions in Multiplayer Tests

**Solution**: Add proper delays and synchronization
```python
# Ensure all players joined before starting
await asyncio.gather(*[
    player.emit('join_room', room_id) 
    for player in players
])
await asyncio.sleep(0.1)  # Allow propagation
```

### Issue: Database State Between Tests

**Solution**: Use transactions and cleanup
```python
@pytest.fixture
def battle_cleanup(db):
    yield
    # Cleanup battles after test
    db.query(Battle).delete()
    db.query(BattleParticipant).delete()
    db.commit()
```

## Test Coverage Goals

### WebSocket Coverage
- Connection lifecycle: 100%
- Event handlers: 95%+
- Error scenarios: 90%+
- Room management: 95%+
- Broadcasting: 90%+

### Multiplayer Coverage
- Battle system: 95%+
- Tournament logic: 90%+
- Study groups: 85%+
- Matchmaking: 90%+
- Rewards: 95%+

## CI/CD Integration

### GitHub Actions Configuration

```yaml
name: WebSocket & Multiplayer Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:13
      redis:
        image: redis:6
    
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest-asyncio python-socketio[asyncio_client]
      - name: Run WebSocket tests
        run: pytest tests/test_websocket_integration.py -v
      - name: Run Multiplayer tests
        run: pytest tests/test_multiplayer_integration.py -v
```

## Future Improvements

### Enhanced Testing

1. **Load Testing**
   - Simulate 1000+ concurrent connections
   - Stress test message throughput
   - Test failover scenarios

2. **Integration Testing**
   - Full user journey tests
   - Cross-feature interactions
   - Mobile client testing

3. **Performance Testing**
   - Latency under load
   - Database query optimization
   - Caching effectiveness

### New Test Scenarios

1. **Network Conditions**
   - Packet loss simulation
   - High latency testing
   - Disconnection recovery

2. **Security Testing**
   - Authentication edge cases
   - Authorization boundaries
   - Input validation

3. **Compatibility Testing**
   - Different client versions
   - Browser compatibility
   - Mobile platform testing

## Best Practices

1. **Async Testing**
   - Always use pytest-asyncio
   - Proper timeout handling
   - Event-driven assertions

2. **Client Management**
   - Clean disconnection
   - Resource cleanup
   - State isolation

3. **Mock External Services**
   - Mock Redis pub/sub
   - Mock external APIs
   - Control timing

4. **Data Integrity**
   - Transaction usage
   - Proper cleanup
   - Fixture isolation

5. **Debugging**
   - Enable debug logging
   - Capture WebSocket frames
   - Use event monitoring