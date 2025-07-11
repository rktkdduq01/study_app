import React, { ReactElement, ReactNode } from 'react';
import { render, RenderOptions, screen, waitForElementToBeRemoved } from '@testing-library/react';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import { configureStore, PreloadedState } from '@reduxjs/toolkit';
import authReducer from '../store/slices/authSlice';
import { RootState } from '../store';
import theme from '../theme';

interface ExtendedRenderOptions extends Omit<RenderOptions, 'queries'> {
  preloadedState?: PreloadedState<RootState>;
  store?: ReturnType<typeof configureStore>;
  route?: string;
}

/**
 * Custom render function that includes all necessary providers
 */
export function renderWithProviders(
  ui: ReactElement,
  {
    preloadedState,
    store = configureStore({
      reducer: {
        auth: authReducer,
      },
      preloadedState
    }),
    route = '/',
    ...renderOptions
  }: ExtendedRenderOptions = {}
) {
  window.history.pushState({}, 'Test page', route);

  function Wrapper({ children }: { children: ReactNode }) {
    return (
      <Provider store={store}>
        <BrowserRouter>
          <ThemeProvider theme={theme}>
            {children}
          </ThemeProvider>
        </BrowserRouter>
      </Provider>
    );
  }

  return {
    store,
    ...render(ui, { wrapper: Wrapper, ...renderOptions })
  };
}

/**
 * Mock data generators
 */
export const mockUser = (overrides = {}) => ({
  id: 1,
  username: 'testuser',
  email: 'test@example.com',
  full_name: 'Test User',
  role: 'student',
  created_at: '2024-01-01T00:00:00Z',
  ...overrides
});

export const mockCharacter = (overrides = {}) => ({
  id: 1,
  user_id: 1,
  name: 'TestHero',
  avatar_url: '/avatars/default.png',
  total_level: 1,
  total_experience: 0,
  coins: 0,
  gems: 0,
  ...overrides
});

export const mockQuest = (overrides = {}) => ({
  id: 1,
  title: 'Test Quest',
  description: 'Complete this test quest',
  quest_type: 'daily',
  difficulty: 'easy',
  subject: 'math',
  objectives: [{ type: 'complete', count: 1 }],
  exp_reward: 100,
  coin_reward: 50,
  gem_reward: 0,
  time_limit_minutes: 30,
  min_level: 1,
  is_active: true,
  ...overrides
});

export const mockAchievement = (overrides = {}) => ({
  id: 1,
  name: 'Test Achievement',
  description: 'Test achievement description',
  category: 'quest',
  rarity: 'common',
  points: 10,
  icon_url: '/achievements/test.png',
  max_progress: 1,
  is_active: true,
  ...overrides
});

export const mockBadge = (overrides = {}) => ({
  id: 1,
  name: 'Test Badge',
  description: 'Test badge description',
  category: 'general',
  rarity: 'common',
  icon_url: '/badges/test.png',
  requirements: {},
  is_active: true,
  unlocked_at: null,
  ...overrides
});

/**
 * Wait utilities
 */
export const waitForLoadingToFinish = () => 
  screen.findByText(/loading/i, {}, { timeout: 3000 }).then(() => 
    waitForElementToBeRemoved(() => screen.queryByText(/loading/i))
  );

/**
 * Custom matchers
 */
export const expectToBeDisabled = (element: HTMLElement) => {
  expect(element).toBeDisabled();
  expect(element).toHaveAttribute('aria-disabled', 'true');
};

export const expectToBeEnabled = (element: HTMLElement) => {
  expect(element).not.toBeDisabled();
  expect(element).not.toHaveAttribute('aria-disabled', 'true');
};

// Re-export everything from React Testing Library
export * from '@testing-library/react';
export { default as userEvent } from '@testing-library/user-event';