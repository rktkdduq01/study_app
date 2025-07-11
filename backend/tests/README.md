# Backend Test Suite

## Overview

This directory contains the test suite for the backend API, including unit tests and integration tests.

## Test Structure

```
tests/
├── conftest.py              # Pytest configuration and fixtures
├── test_auth.py             # Unit tests for authentication
├── test_security.py         # Unit tests for security module
├── test_error_handling.py   # Unit tests for error handling
├── test_gamification.py     # Unit tests for gamification
├── test_integration_auth.py # Integration tests for auth flow
├── test_integration_gamification.py # Integration tests for gamification
└── test_all.py             # Run all tests with reporting
```

## Running Tests

### Prerequisites

```bash
pip install pytest pytest-cov pytest-asyncio
```

### Run All Tests

```bash
# From backend directory
pytest

# With coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration
```

### Using the Test Runner

```bash
# Run all tests with summary
python tests/test_all.py

# Run tests with coverage
python run_tests.py --coverage
```

## Test Categories

### Unit Tests

Unit tests focus on testing individual components in isolation:

- **test_security.py**: Password hashing, JWT tokens, encryption
- **test_auth.py**: Authentication endpoints (login, register, etc.)
- **test_error_handling.py**: Custom exceptions and error responses
- **test_gamification.py**: Level calculation, rewards, badges, inventory

### Integration Tests

Integration tests verify complete workflows:

- **test_integration_auth.py**: Full authentication flow, token lifecycle
- **test_integration_gamification.py**: Quest completion, achievement unlocking

## Writing Tests

### Test Structure

```python
class TestFeatureName:
    """Test description"""
    
    @pytest.fixture
    def setup_data(self, db: Session):
        """Setup test data"""
        # Create test data
        return data
    
    def test_feature_success(self, client: TestClient, setup_data):
        """Test successful case"""
        response = client.post("/api/endpoint", json=data)
        assert response.status_code == 200
        assert response.json()["field"] == expected_value
    
    def test_feature_error(self, client: TestClient):
        """Test error case"""
        response = client.post("/api/endpoint", json=invalid_data)
        assert response.status_code == 400
```

### Using Fixtures

Common fixtures available in `conftest.py`:

- `db`: Test database session
- `client`: FastAPI test client
- `test_user`: Basic test user
- `test_admin_user`: Admin test user
- `test_user_token_headers`: Auth headers for test user
- `test_character`: Test character
- `test_quest`: Test quest
- `test_achievement`: Test achievement

### Test Markers

```python
@pytest.mark.unit  # Unit test
@pytest.mark.integration  # Integration test
@pytest.mark.slow  # Slow running test
@pytest.mark.requires_db  # Requires database
@pytest.mark.requires_redis  # Requires Redis
```

## Test Coverage

Aim for at least 80% code coverage:

```bash
# Generate coverage report
pytest --cov=app --cov-report=html

# View report
open htmlcov/index.html
```

## Best Practices

1. **Isolation**: Each test should be independent
2. **Clear Names**: Use descriptive test names
3. **Arrange-Act-Assert**: Structure tests clearly
4. **Test Edge Cases**: Include error cases and boundaries
5. **Use Fixtures**: Reuse common test data
6. **Mock External Services**: Don't make real API calls
7. **Clean Database**: Each test gets a fresh database

## Debugging Tests

```bash
# Run with debugging output
pytest -vv --tb=short

# Run specific test
pytest tests/test_auth.py::TestLogin::test_login_success

# Show print statements
pytest -s

# Drop into debugger on failure
pytest --pdb
```

## CI/CD Integration

Tests are automatically run on:
- Pull requests
- Commits to main branch
- Before deployment

See `.github/workflows/test.yml` for CI configuration.