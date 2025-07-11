# Frontend Test Suite

## Overview

This directory contains the test suite for the React frontend application, including unit tests, component tests, and integration tests.

## Test Structure

```
src/
├── __tests__/
│   ├── integration/         # Integration tests
│   │   └── AuthFlow.test.tsx
│   └── README.md
├── components/
│   ├── auth/__tests__/     # Auth component tests
│   ├── common/__tests__/   # Common component tests
│   └── gamification/__tests__/ # Gamification component tests
├── services/__tests__/     # Service layer tests
├── hooks/__tests__/        # Custom hook tests
├── store/__tests__/        # Redux store tests
├── utils/__tests__/        # Utility function tests
└── test-utils/            # Test utilities and helpers
```

## Running Tests

### Prerequisites

```bash
npm install
```

### Test Commands

```bash
# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run tests with coverage
npm test -- --coverage

# Update snapshots
npm test -- -u

# Run specific test file
npm test LoginForm.test.tsx

# Run tests matching pattern
npm test -- --testNamePattern="should login"
```

### Using the Test Runner

```bash
# Run all tests with summary
node run_tests.js

# Run in watch mode
node run_tests.js watch

# Run with coverage
node run_tests.js coverage

# Run only unit tests
node run_tests.js unit

# Run only component tests
node run_tests.js component
```

## Test Categories

### Unit Tests

Tests for individual functions and services:

- **Services**: API service methods (`auth.test.ts`, `websocket.test.ts`)
- **Utils**: Utility functions (`errorHandler.test.ts`)
- **Hooks**: Custom React hooks (`useAuth.test.tsx`)
- **Store**: Redux slices and actions (`authSlice.test.ts`)

### Component Tests

Tests for React components using React Testing Library:

- **Auth Components**: Login, Register forms
- **Common Components**: ErrorBoundary, Loading, etc.
- **Gamification Components**: LevelProgress, BadgeDisplay, etc.

### Integration Tests

End-to-end user flow tests:

- **AuthFlow**: Complete authentication flow
- **GameFlow**: Quest completion and rewards
- **ParentDashboard**: Parent-child interaction

## Writing Tests

### Component Test Example

```typescript
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../../test-utils';
import MyComponent from '../MyComponent';

describe('MyComponent', () => {
  it('should handle user interaction', async () => {
    const user = userEvent.setup();
    const onSubmit = jest.fn();
    
    renderWithProviders(
      <MyComponent onSubmit={onSubmit} />
    );
    
    const button = screen.getByRole('button', { name: /submit/i });
    await user.click(button);
    
    expect(onSubmit).toHaveBeenCalled();
  });
});
```

### Service Test Example

```typescript
import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';
import myService from '../myService';

const mock = new MockAdapter(axios);

describe('MyService', () => {
  afterEach(() => {
    mock.reset();
  });

  it('should fetch data', async () => {
    const mockData = { id: 1, name: 'Test' };
    mock.onGet('/api/data').reply(200, mockData);
    
    const result = await myService.getData();
    
    expect(result).toEqual(mockData);
  });
});
```

### Hook Test Example

```typescript
import { renderHook, act } from '@testing-library/react';
import { renderWithProviders } from '../../test-utils';
import useMyHook from '../useMyHook';

describe('useMyHook', () => {
  it('should update state', () => {
    const { result } = renderHook(() => useMyHook(), {
      wrapper: ({ children }) => renderWithProviders(children)
    });
    
    act(() => {
      result.current.updateValue('new value');
    });
    
    expect(result.current.value).toBe('new value');
  });
});
```

## Test Utilities

### Custom Render Function

Use `renderWithProviders` for components that need Redux/Router/Theme:

```typescript
import { renderWithProviders } from '../test-utils';

renderWithProviders(<MyComponent />, {
  preloadedState: {
    auth: { user: mockUser(), isAuthenticated: true }
  },
  route: '/dashboard'
});
```

### Mock Data Generators

```typescript
import { mockUser, mockQuest, mockBadge } from '../test-utils';

const user = mockUser({ username: 'customuser' });
const quest = mockQuest({ difficulty: 'hard' });
```

### Common Assertions

```typescript
import { expectToBeDisabled, expectToBeEnabled } from '../test-utils';

expectToBeDisabled(submitButton);
expectToBeEnabled(cancelButton);
```

## Best Practices

1. **Test User Behavior**: Test what users do, not implementation details
2. **Use Semantic Queries**: Prefer `getByRole`, `getByLabelText` over `getByTestId`
3. **Async Operations**: Always use `userEvent` for user interactions
4. **Wait for Elements**: Use `waitFor` or `find*` queries for async content
5. **Mock External Dependencies**: Mock API calls and external services
6. **Test Accessibility**: Ensure components are accessible
7. **Avoid Implementation Details**: Don't test state, test behavior

## Debugging Tests

```bash
# Run single test in debug mode
npm test -- --runInBand LoginForm.test.tsx

# Use debug function
import { screen, debug } from '@testing-library/react';
debug(); // Prints current DOM

# Use screen.debug for specific elements
screen.debug(screen.getByRole('button'));

# Check what's available
screen.logTestingPlaygroundURL();
```

## Coverage Reports

After running tests with coverage:

```bash
npm test -- --coverage

# View HTML report
open coverage/lcov-report/index.html
```

Coverage thresholds are configured in `jest.config.ts`:
- Branches: 70%
- Functions: 70%
- Lines: 70%
- Statements: 70%

## Common Issues

### Module Resolution

If you get module resolution errors:
```typescript
// Use path aliases in tests
import Component from '@/components/Component';
```

### Async Warnings

Always wait for async operations:
```typescript
// ❌ Bad
userEvent.click(button);
expect(screen.getByText('Success')).toBeInTheDocument();

// ✅ Good
await userEvent.click(button);
await waitFor(() => {
  expect(screen.getByText('Success')).toBeInTheDocument();
});
```

### Memory Leaks

Clean up after tests:
```typescript
afterEach(() => {
  cleanup(); // Automatically done by testing-library
  jest.clearAllMocks();
});
```