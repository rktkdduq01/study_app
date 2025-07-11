# E2E Test Suite

## Overview

This directory contains end-to-end tests using Playwright that test the full user workflows of the Educational RPG Platform.

## Test Structure

```
e2e/
├── auth.spec.ts           # Authentication flow tests
├── gamification.spec.ts   # Gamification features tests
├── learning-flow.spec.ts  # Learning experience tests
├── parent-dashboard.spec.ts # Parent dashboard tests
└── README.md
```

## Setup

### Prerequisites

1. Install Playwright and dependencies:
```bash
npm install
npm run playwright:install
```

2. Ensure backend and frontend are running:
```bash
# In separate terminals
cd backend && uvicorn app.main:app --reload
cd frontend && npm run dev
```

## Running Tests

### Basic Commands

```bash
# Run all tests
npm run test:e2e

# Run tests in UI mode (recommended for development)
npm run test:e2e:ui

# Run tests in headed mode (see browser)
npm run test:e2e:headed

# Run tests in debug mode
npm run test:e2e:debug

# Run specific test file
npx playwright test auth.spec.ts

# Run tests with specific browser
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit
```

### Test Reports

```bash
# Generate and view HTML report
npx playwright show-report

# View trace files
npx playwright show-trace trace.zip
```

## Test Categories

### Authentication Tests (`auth.spec.ts`)
- Login functionality
- Registration flow
- Password visibility toggle
- Session persistence
- Logout functionality
- Error handling
- Session timeout

### Gamification Tests (`gamification.spec.ts`)
- Character display
- Quest navigation and completion
- Achievement system
- Badge collection
- Level progression
- Daily rewards
- Leaderboard
- Quest filtering

### Learning Flow Tests (`learning-flow.spec.ts`)
- Complete learning quests
- Real-time progress updates
- Learning streak tracking
- Subject progress
- AI tutor interaction
- Personalized recommendations
- Study time tracking
- Achievement notifications

### Parent Dashboard Tests (`parent-dashboard.spec.ts`)
- Parent login
- View child progress
- Set learning goals
- View notifications
- Weekly reports
- Account management
- Screen time limits
- Progress comparison
- Export reports

## Writing Tests

### Test Structure

```typescript
import { test, expect } from '@playwright/test';

test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    // Setup before each test
    await page.goto('/');
  });

  test('should do something', async ({ page }) => {
    // Arrange
    await page.getByRole('button', { name: /click me/i }).click();

    // Act
    await page.fill('#input', 'test value');

    // Assert
    await expect(page.getByText(/success/i)).toBeVisible();
  });
});
```

### Best Practices

1. **Use semantic locators**:
```typescript
// ✅ Good
await page.getByRole('button', { name: /submit/i });
await page.getByLabel(/email/i);

// ❌ Avoid
await page.locator('#submit-btn');
await page.locator('.email-input');
```

2. **Wait for elements properly**:
```typescript
// ✅ Good
await expect(page.getByText(/loading/i)).toBeVisible();
await page.waitForURL('**/dashboard');

// ❌ Avoid
await page.waitForTimeout(1000);
```

3. **Use test data attributes when needed**:
```typescript
await page.getByTestId('complex-component');
```

4. **Handle dynamic content**:
```typescript
// Wait for API responses
await page.waitForResponse('**/api/quests');

// Wait for animations
await page.waitForLoadState('networkidle');
```

5. **Test user flows, not implementation**:
```typescript
// Test what users see and do
// Not internal state or API calls
```

## Debugging

### Visual Debugging

```bash
# Run with UI mode
npm run test:e2e:ui

# Run specific test in debug mode
npx playwright test auth.spec.ts --debug
```

### Trace Viewer

```bash
# Run tests with trace
npx playwright test --trace on

# View trace
npx playwright show-trace trace.zip
```

### Screenshots and Videos

Failed tests automatically capture:
- Screenshots
- Trace files
- Videos (if configured)

Find them in: `test-results/`

### Console Logs

```typescript
// Add console logs in tests
console.log('Current URL:', await page.url());
console.log('Page title:', await page.title());

// Capture browser console
page.on('console', msg => console.log(msg.text()));
```

## CI/CD Integration

### GitHub Actions

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npm run test:e2e
      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
```

## Common Issues

### Port Already in Use

If you get port conflicts:
```bash
# Kill processes on ports
lsof -ti:3000 | xargs kill -9
lsof -ti:8000 | xargs kill -9
```

### Browser Installation

If browsers are not installed:
```bash
npx playwright install --with-deps
```

### Flaky Tests

To handle flaky tests:
- Add proper waits
- Use `test.retry()`
- Check for race conditions
- Ensure test isolation

### Slow Tests

Speed up tests by:
- Running in parallel
- Reducing animations
- Using test data
- Mocking external services

## Test Data

### Creating Test Users

```typescript
// Helper to create test user
async function createTestUser(page, username, role = 'student') {
  await page.goto('/register');
  await page.fill('[name="username"]', username);
  await page.fill('[name="email"]', `${username}@test.com`);
  await page.fill('[name="password"]', 'Test123!');
  await page.fill('[name="confirmPassword"]', 'Test123!');
  await page.selectOption('[name="role"]', role);
  await page.click('button[type="submit"]');
}
```

### Resetting Test Data

Before running tests, ensure clean test data:
```bash
# Reset test database
cd backend && python scripts/reset_test_db.py
```

## Performance Testing

Monitor performance during E2E tests:

```typescript
test('should load quickly', async ({ page }) => {
  const startTime = Date.now();
  await page.goto('/dashboard');
  const loadTime = Date.now() - startTime;
  
  expect(loadTime).toBeLessThan(3000); // 3 seconds
});
```

## Accessibility Testing

Include accessibility checks:

```typescript
test('should be accessible', async ({ page }) => {
  await page.goto('/');
  
  // Check for ARIA labels
  await expect(page.getByRole('navigation')).toBeVisible();
  await expect(page.getByRole('main')).toBeVisible();
  
  // Check keyboard navigation
  await page.keyboard.press('Tab');
  await expect(page.locator(':focus')).toBeVisible();
});
```