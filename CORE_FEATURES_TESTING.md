# Core Features Testing Documentation

## Overview

Comprehensive unit and integration tests for the core features: AI Tutor and Gamification System. These tests ensure reliability, performance, and correct behavior of the most critical application features.

## Test Structure

### AI Tutor Tests

#### 1. **Unit Tests** (`test_ai_tutor.py`)
Tests for the AI Tutor service layer including:

- **Learning Style Analysis**
  - Analyzes user session data
  - Identifies learning patterns
  - Provides personalized recommendations

- **Content Generation**
  - Creates personalized learning content
  - Adapts to user's learning style
  - Includes practice problems and interactive elements

- **Feedback System**
  - Analyzes user answers
  - Provides constructive feedback
  - Identifies misconceptions
  - Suggests next steps

- **Practice Questions**
  - Generates questions based on difficulty
  - Supports multiple question types
  - Includes hints and explanations

- **Learning Path Creation**
  - Creates multi-week learning plans
  - Sets milestones and goals
  - Tracks prerequisites

- **Concept Explanation**
  - Generates detailed explanations
  - Provides examples and analogies
  - Includes visual aids suggestions

- **Progressive Hints**
  - Multi-level hint system
  - Gradually reveals solution
  - Tracks hint usage

- **Chat Functionality**
  - Natural language interaction
  - Context-aware responses
  - Session management

#### 2. **API Tests** (`test_ai_tutor_api.py`)
Tests for AI Tutor REST endpoints:

- Authentication requirements
- Request/response validation
- Error handling
- Rate limiting
- OpenAI integration mocking

#### 3. **Key Test Scenarios**

```python
# Test personalized content generation
async def test_generate_personalized_content():
    # Mocks OpenAI response
    # Verifies content structure
    # Checks database persistence
    # Validates personalization

# Test learning analytics update
def test_update_learning_profile():
    # Updates user profile based on performance
    # Tracks weak areas
    # Adjusts difficulty recommendations

# Test error handling
async def test_openai_api_error_handling():
    # Handles API failures gracefully
    # Provides fallback responses
    # Logs errors appropriately
```

### Gamification Tests

#### 1. **Unit Tests** (`test_gamification.py`)
Tests for the Gamification service layer including:

- **Level System**
  - Experience calculation
  - Level progression
  - Level rewards distribution
  - Experience boosts
  - Level cap handling

- **Daily Rewards**
  - Streak tracking
  - Reward claiming
  - Milestone bonuses
  - Streak reset logic
  - Prevention of duplicate claims

- **Badge System**
  - Badge requirement checking
  - Progress tracking
  - Reward distribution
  - No duplicate awards
  - Secret badge handling

- **Inventory Management**
  - Item addition
  - Stack limit enforcement
  - Consumable item usage
  - Boost effects with duration
  - Non-consumable item restrictions

- **User Statistics**
  - Stats tracking
  - Currency management
  - Activity monitoring

- **Quest Rewards**
  - Reward calculation
  - Conditional rewards
  - First-time bonuses
  - Speed bonuses

- **Leaderboards**
  - Ranking calculations
  - Multiple leaderboard types
  - Performance optimization

#### 2. **API Tests** (`test_gamification_api.py`)
Tests for Gamification REST endpoints:

- User data retrieval
- Experience addition (admin only)
- Daily reward claiming
- Badge listings
- Inventory management
- Item usage
- Leaderboard queries

#### 3. **Integration Tests**

```python
# Test complete quest flow
def test_complete_quest_flow():
    # Awards experience
    # Triggers level up
    # Distributes rewards
    # Checks for badges
    # Updates statistics

# Test daily login streak
def test_daily_login_streak_flow():
    # Simulates 7-day streak
    # Awards milestone bonus
    # Triggers badge award
    # Maintains streak data
```

## Running Tests

### Prerequisites

1. **Test Database Setup**
```bash
# Create test database
createdb quest_test

# Set test environment variables
export DATABASE_URL="postgresql://user:password@localhost/quest_test"
export TESTING=true
```

2. **Install Dependencies**
```bash
pip install pytest pytest-asyncio pytest-mock
```

### Running All Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_ai_tutor.py

# Run specific test class
pytest tests/test_gamification.py::TestLevelSystem

# Run specific test
pytest tests/test_ai_tutor.py::test_generate_personalized_content
```

### Test Categories

```bash
# Run only unit tests
pytest -m "not integration"

# Run only integration tests
pytest -m integration

# Run only API tests
pytest tests/test_*_api.py
```

## Mocking External Services

### OpenAI API Mocking

```python
@patch('app.services.ai_tutor.openai.ChatCompletion.acreate')
async def test_with_mocked_openai(mock_openai):
    mock_openai.return_value = {
        "choices": [{
            "message": {
                "content": '{"response": "mocked"}'
            }
        }]
    }
```

### Database Fixtures

```python
@pytest.fixture
def sample_user(db: Session):
    """Creates a test user with profile"""
    user = User(email="test@example.com")
    db.add(user)
    db.commit()
    return user
```

## Test Data Management

### Fixtures Organization

- `conftest.py` - Shared fixtures
- `sample_user` - User with basic setup
- `level_system` - Level progression data
- `daily_rewards` - Daily reward configuration
- `sample_badges` - Test badges
- `sample_items` - Test inventory items

### Database Cleanup

Tests use transactions that are rolled back after each test to ensure isolation.

## Performance Testing

### Load Testing AI Tutor

```python
@pytest.mark.performance
async def test_content_generation_performance():
    start = time.time()
    for _ in range(100):
        await ai_tutor.generate_content(...)
    duration = time.time() - start
    assert duration < 10  # Should handle 100 requests in 10s
```

### Gamification Scaling

```python
@pytest.mark.performance
def test_leaderboard_performance():
    # Create 10,000 users
    # Query leaderboard
    # Assert query time < 100ms
```

## Continuous Integration

### GitHub Actions Configuration

```yaml
name: Test Core Features
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost/test
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          pytest --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v1
```

## Best Practices

### 1. **Test Isolation**
- Each test should be independent
- Use fixtures for setup
- Clean up after tests
- Don't rely on test order

### 2. **Mock External Services**
- Mock OpenAI API calls
- Mock email sending
- Mock payment processing
- Use local file storage for tests

### 3. **Test Data**
- Use realistic test data
- Test edge cases
- Test invalid inputs
- Test concurrent operations

### 4. **Assertions**
- Be specific in assertions
- Test both positive and negative cases
- Verify side effects
- Check database state

### 5. **Performance**
- Set performance benchmarks
- Test with realistic data volumes
- Monitor test execution time
- Profile slow tests

## Common Issues and Solutions

### Issue: Tests Failing Due to OpenAI API

**Solution**: Ensure all OpenAI calls are mocked
```python
with patch('app.services.ai_tutor.openai') as mock_openai:
    # Test code
```

### Issue: Database Connection Errors

**Solution**: Check test database configuration
```bash
# Verify connection
psql $DATABASE_URL -c "SELECT 1"
```

### Issue: Flaky Tests

**Solution**: 
- Add proper waits for async operations
- Use database transactions
- Mock time-dependent operations
- Ensure proper cleanup

### Issue: Slow Test Suite

**Solution**:
- Run tests in parallel: `pytest -n auto`
- Use test database templates
- Mock expensive operations
- Profile slow tests

## Test Coverage Goals

- **Overall Coverage**: > 80%
- **Critical Paths**: > 95%
- **Error Handling**: 100%
- **API Endpoints**: 100%

## Future Improvements

1. **Integration Tests**
   - End-to-end user flows
   - Multi-service interactions
   - Real database testing

2. **Performance Tests**
   - Load testing
   - Stress testing
   - Scalability testing

3. **Security Tests**
   - Authentication flows
   - Authorization checks
   - Input validation

4. **UI Tests**
   - Component testing
   - User interaction flows
   - Visual regression testing