# Testing Guide for Educational RPG Platform

## Overview

This document provides a comprehensive guide to testing the Educational RPG Platform. Our testing strategy includes unit tests, integration tests, component tests, and end-to-end tests.

## Test Structure

```
project/
├── backend/
│   └── tests/
│       ├── test_*.py           # Unit tests
│       └── test_integration_*.py # Integration tests
├── frontend/
│   └── src/
│       ├── __tests__/          # Integration tests
│       ├── components/*/__tests__/ # Component tests
│       ├── services/__tests__/ # Service tests
│       ├── hooks/__tests__/    # Hook tests
│       └── utils/__tests__/    # Utility tests
├── e2e/
│   └── *.spec.ts              # End-to-end tests
└── TESTING.md                 # This file
```

## Quick Start

### Running All Tests

```bash
# Install dependencies
npm install
cd backend && pip install -r requirements.txt
cd frontend && npm install

# Run all tests
npm test

# Run specific test suites
npm run test:backend
npm run test:frontend
npm run test:e2e
```

## Backend Testing (Python/pytest)

### Setup

```bash
cd backend
pip install pytest pytest-cov pytest-asyncio
```

### Running Tests

```bash
# Run all backend tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run specific test
pytest tests/test_auth.py::TestLogin::test_login_success

# Run by marker
pytest -m unit
pytest -m integration
```

### Test Categories

1. **Unit Tests**
   - `test_security.py` - Password hashing, JWT tokens
   - `test_auth.py` - Authentication endpoints
   - `test_error_handling.py` - Error handling
   - `test_gamification.py` - Game mechanics

2. **Integration Tests**
   - `test_integration_auth.py` - Full auth flow
   - `test_integration_gamification.py` - Game features

### Writing Backend Tests

```python
import pytest
from fastapi.testclient import TestClient

def test_example(client: TestClient, test_user: User):
    response = client.get("/api/endpoint")
    assert response.status_code == 200
    assert response.json()["field"] == "expected"
```

## Frontend Testing (React/Jest)

### Setup

```bash
cd frontend
npm install
```

### Running Tests

```bash
# Run all frontend tests
npm test

# Run in watch mode
npm test -- --watch

# Run with coverage
npm test -- --coverage

# Update snapshots
npm test -- -u
```

### Test Categories

1. **Unit Tests**
   - Service tests (`services/__tests__`)
   - Utility tests (`utils/__tests__`)
   - Hook tests (`hooks/__tests__`)
   - Store tests (`store/__tests__`)

2. **Component Tests**
   - Auth components
   - Common components
   - Gamification components

3. **Integration Tests**
   - Full user flows

### Writing Frontend Tests

```typescript
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

test('component test', async () => {
  const user = userEvent.setup();
  render(<Component />);
  
  await user.click(screen.getByRole('button'));
  expect(screen.getByText(/success/i)).toBeInTheDocument();
});
```

## E2E Testing (Playwright)

### Setup

```bash
npm install
npm run playwright:install
```

### Running Tests

```bash
# Run all E2E tests
npm run test:e2e

# Run in UI mode (recommended)
npm run test:e2e:ui

# Run specific test
npx playwright test auth.spec.ts

# Debug mode
npm run test:e2e:debug
```

### Test Scenarios

1. **Authentication Flow** (`auth.spec.ts`)
   - Login/logout
   - Registration
   - Session management

2. **Gamification** (`gamification.spec.ts`)
   - Quest completion
   - Achievements
   - Badges
   - Leaderboards

3. **Learning Flow** (`learning-flow.spec.ts`)
   - Complete lessons
   - Track progress
   - AI tutor interaction

4. **Parent Dashboard** (`parent-dashboard.spec.ts`)
   - Monitor children
   - Set goals
   - View reports

## Testing Best Practices

### 1. Test Pyramid

```
        /\
       /E2E\      (Few)
      /------\
     /  UI    \   (Some)
    /----------\
   /Integration \  (More)
  /--------------\
 /   Unit Tests   \ (Many)
/------------------\
```

### 2. What to Test

- **User Interactions**: Click, type, navigate
- **Business Logic**: Calculations, validations
- **Error Handling**: Invalid inputs, network errors
- **Edge Cases**: Empty states, limits
- **Accessibility**: ARIA labels, keyboard nav

### 3. What NOT to Test

- Implementation details
- Third-party libraries
- Styling (unless critical)
- Framework internals

### 4. Test Organization

```typescript
describe('Feature', () => {
  describe('Scenario', () => {
    it('should do something specific', () => {
      // Arrange
      // Act
      // Assert
    });
  });
});
```

### 5. Naming Conventions

- Descriptive test names
- Use "should" for clarity
- Group related tests
- Name by behavior, not implementation

## Coverage Requirements

### Backend (Python)
- Minimum: 80% overall
- Critical paths: 90%
- New code: 85%

### Frontend (React)
- Minimum: 70% overall
- Components: 80%
- Services: 90%
- Utils: 95%

### View Coverage Reports

```bash
# Backend
cd backend
pytest --cov=app --cov-report=html
open htmlcov/index.html

# Frontend
cd frontend
npm test -- --coverage
open coverage/lcov-report/index.html
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Tests

on: [push, pull_request]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: |
          cd backend
          pip install -r requirements.txt
          pytest --cov

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: |
          cd frontend
          npm ci
          npm test -- --coverage

  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: |
          npm ci
          npx playwright install --with-deps
          npm run test:e2e
```

## Test Data Management

### Backend Test Data

```python
# Use fixtures for test data
@pytest.fixture
def test_user(db):
    return User(username="test", ...)

# Reset database between tests
@pytest.fixture(autouse=True)
def reset_db(db):
    yield
    db.rollback()
```

### Frontend Test Data

```typescript
// Use mock data generators
import { mockUser, mockQuest } from '../test-utils';

const user = mockUser({ role: 'admin' });
```

### E2E Test Data

```typescript
// Create test accounts
beforeEach(async ({ page }) => {
  await createTestUser(page, 'testuser');
});
```

## Debugging Tests

### Backend Debugging

```bash
# Run with verbose output
pytest -vv

# Drop into debugger
pytest --pdb

# Show print statements
pytest -s
```

### Frontend Debugging

```typescript
// Debug specific elements
screen.debug();
screen.logTestingPlaygroundURL();

// Check available queries
screen.getByRole('button');
```

### E2E Debugging

```bash
# UI mode
npm run test:e2e:ui

# Debug mode
npm run test:e2e:debug

# View trace
npx playwright show-trace trace.zip
```

## Performance Testing

### Load Testing

```python
# Use locust for load testing
from locust import HttpUser, task

class WebsiteUser(HttpUser):
    @task
    def index(self):
        self.client.get("/")
```

### Frontend Performance

```typescript
// Measure render time
const start = performance.now();
render(<Component />);
const renderTime = performance.now() - start;
expect(renderTime).toBeLessThan(100);
```

## Security Testing

### Authentication Tests
- Token validation
- Password strength
- Session timeout
- CORS headers

### Authorization Tests
- Role-based access
- Resource ownership
- API permissions

### Input Validation
- SQL injection
- XSS prevention
- File upload limits

## Accessibility Testing

### Automated Tests

```typescript
// Check ARIA labels
expect(screen.getByRole('button')).toHaveAccessibleName();

// Keyboard navigation
await userEvent.tab();
expect(screen.getByRole('link')).toHaveFocus();
```

### Manual Testing
- Screen reader compatibility
- Keyboard-only navigation
- Color contrast
- Focus indicators

## Test Maintenance

### Regular Tasks
1. Update test data monthly
2. Review flaky tests weekly
3. Update snapshots after UI changes
4. Monitor test execution time
5. Keep coverage above thresholds

### Test Review Checklist
- [ ] Tests are descriptive
- [ ] No hardcoded values
- [ ] Proper cleanup
- [ ] No test interdependencies
- [ ] Follows naming conventions

## Troubleshooting

### Common Issues

1. **Timeout Errors**
   - Increase timeout limits
   - Check async operations
   - Verify API responses

2. **Flaky Tests**
   - Add proper waits
   - Check race conditions
   - Mock time-dependent code

3. **Setup Failures**
   - Verify dependencies
   - Check database state
   - Clear test cache

### Getting Help

- Check test logs first
- Search existing issues
- Ask in team chat
- Create detailed bug reports

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Jest Documentation](https://jestjs.io/)
- [React Testing Library](https://testing-library.com/react)
- [Playwright Documentation](https://playwright.dev/)
- [Testing Best Practices](https://testingjavascript.com/)