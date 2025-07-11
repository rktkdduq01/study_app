import React from 'react';
import { renderWithProviders, userEvent, screen, waitFor, mockUser } from '../../test-utils';
import App from '../../App';
import authService from '../../services/auth';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';

// Mock auth service
jest.mock('../../services/auth');

// Setup MSW server for API mocking
const server = setupServer(
  http.post('/api/v1/auth/login', () => {
    return HttpResponse.json({
      access_token: 'mock-token',
      refresh_token: 'mock-refresh',
      token_type: 'bearer',
      user: mockUser()
    });
  }),
  http.get('/api/v1/auth/me', ({ request }) => {
    const authHeader = request.headers.get('Authorization');
    if (authHeader === 'Bearer mock-token') {
      return HttpResponse.json(mockUser());
    }
    return new HttpResponse(null, { status: 401 });
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('Authentication Flow Integration', () => {
  beforeEach(() => {
    localStorage.clear();
    jest.clearAllMocks();
  });

  it('should complete full login flow', async () => {
    const user = userEvent.setup();
    
    // Mock successful login
    (authService.login as jest.Mock).mockResolvedValue({
      access_token: 'mock-token',
      refresh_token: 'mock-refresh',
      token_type: 'bearer',
      user: mockUser()
    });

    renderWithProviders(<App />);

    // Should start at login page
    expect(screen.getByText(/로그인/i)).toBeInTheDocument();

    // Fill in login form
    const usernameInput = screen.getByLabelText(/사용자명 또는 이메일/i);
    const passwordInput = screen.getByLabelText(/비밀번호/i);
    
    await user.type(usernameInput, 'testuser');
    await user.type(passwordInput, 'password123');
    
    // Submit form
    const loginButton = screen.getByRole('button', { name: /로그인/i });
    await user.click(loginButton);

    // Should redirect to dashboard
    await waitFor(() => {
      expect(screen.getByText(/대시보드/i)).toBeInTheDocument();
    });

    // Should show user info
    expect(screen.getByText(/Test User/i)).toBeInTheDocument();
    
    // Should have stored tokens
    expect(localStorage.getItem('access_token')).toBe('mock-token');
    expect(localStorage.getItem('refresh_token')).toBe('mock-refresh');
  });

  it('should handle login errors', async () => {
    const user = userEvent.setup();
    
    // Mock failed login
    (authService.login as jest.Mock).mockRejectedValue({
      response: {
        status: 401,
        data: {
          error: {
            code: 'AUTHENTICATION_ERROR',
            message: '잘못된 사용자명 또는 비밀번호입니다'
          }
        }
      }
    });

    renderWithProviders(<App />);

    // Fill in login form
    await user.type(screen.getByLabelText(/사용자명 또는 이메일/i), 'testuser');
    await user.type(screen.getByLabelText(/비밀번호/i), 'wrongpassword');
    
    // Submit form
    await user.click(screen.getByRole('button', { name: /로그인/i }));

    // Should show error message
    await waitFor(() => {
      expect(screen.getByText(/잘못된 사용자명 또는 비밀번호입니다/i)).toBeInTheDocument();
    });

    // Should not redirect
    expect(screen.queryByText(/대시보드/i)).not.toBeInTheDocument();
    
    // Should not store tokens
    expect(localStorage.getItem('access_token')).toBeNull();
  });

  it('should handle logout', async () => {
    const user = userEvent.setup();
    
    // Setup authenticated state
    localStorage.setItem('access_token', 'mock-token');
    localStorage.setItem('refresh_token', 'mock-refresh');
    
    (authService.getCurrentUser as jest.Mock).mockResolvedValue(mockUser());
    (authService.isAuthenticated as jest.Mock).mockReturnValue(true);
    (authService.logout as jest.Mock).mockResolvedValue(undefined);

    renderWithProviders(<App />, {
      preloadedState: {
        auth: {
          user: mockUser(),
          token: 'mock-token',
          isAuthenticated: true,
          isLoading: false,
          error: null
        }
      }
    });

    // Should be on dashboard
    await waitFor(() => {
      expect(screen.getByText(/대시보드/i)).toBeInTheDocument();
    });

    // Click logout
    const userMenu = screen.getByTestId('user-menu');
    await user.click(userMenu);
    
    const logoutButton = screen.getByText(/로그아웃/i);
    await user.click(logoutButton);

    // Should redirect to login
    await waitFor(() => {
      expect(screen.getByText(/로그인/i)).toBeInTheDocument();
    });

    // Should clear tokens
    expect(localStorage.getItem('access_token')).toBeNull();
    expect(localStorage.getItem('refresh_token')).toBeNull();
  });

  it('should persist authentication on page reload', async () => {
    // Setup authenticated state
    localStorage.setItem('access_token', 'mock-token');
    localStorage.setItem('refresh_token', 'mock-refresh');
    
    (authService.getCurrentUser as jest.Mock).mockResolvedValue(mockUser());
    (authService.isAuthenticated as jest.Mock).mockReturnValue(true);
    (authService.getToken as jest.Mock).mockReturnValue('mock-token');

    renderWithProviders(<App />);

    // Should check auth on mount
    await waitFor(() => {
      expect(authService.getCurrentUser).toHaveBeenCalled();
    });

    // Should redirect to dashboard
    await waitFor(() => {
      expect(screen.getByText(/대시보드/i)).toBeInTheDocument();
    });
  });

  it('should redirect to login when accessing protected routes', async () => {
    // Not authenticated
    (authService.isAuthenticated as jest.Mock).mockReturnValue(false);

    renderWithProviders(<App />, {
      route: '/dashboard'
    });

    // Should redirect to login
    await waitFor(() => {
      expect(screen.getByText(/로그인/i)).toBeInTheDocument();
    });
  });

  it('should handle token refresh', async () => {
    // Setup authenticated state with expired token
    localStorage.setItem('access_token', 'expired-token');
    localStorage.setItem('refresh_token', 'mock-refresh');
    
    // First call fails with 401
    (authService.getCurrentUser as jest.Mock)
      .mockRejectedValueOnce({ response: { status: 401 } })
      .mockResolvedValueOnce(mockUser());
    
    // Refresh token succeeds
    (authService.refreshToken as jest.Mock).mockResolvedValue({
      access_token: 'new-token',
      token_type: 'bearer'
    });

    renderWithProviders(<App />);

    // Should attempt to refresh token
    await waitFor(() => {
      expect(authService.refreshToken).toHaveBeenCalled();
    });

    // Should update token
    expect(localStorage.getItem('access_token')).toBe('new-token');

    // Should successfully get user after refresh
    await waitFor(() => {
      expect(screen.getByText(/대시보드/i)).toBeInTheDocument();
    });
  });

  it('should navigate between login and register', async () => {
    const user = userEvent.setup();
    
    renderWithProviders(<App />);

    // Start at login
    expect(screen.getByText(/로그인/i)).toBeInTheDocument();

    // Click register link
    const registerLink = screen.getByText(/회원가입/i);
    await user.click(registerLink);

    // Should be on register page
    await waitFor(() => {
      expect(screen.getByText(/계정 만들기/i)).toBeInTheDocument();
    });

    // Click login link
    const loginLink = screen.getByText(/이미 계정이 있으신가요?.*로그인/i);
    await user.click(loginLink);

    // Should be back on login page
    await waitFor(() => {
      expect(screen.getByLabelText(/사용자명 또는 이메일/i)).toBeInTheDocument();
    });
  });
});