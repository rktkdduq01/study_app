import { renderHook, act } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { ReactNode } from 'react';
import useAuth from '../useAuth';
import authReducer, { setCredentials } from '../../store/slices/authSlice';
import authService from '../../services/auth';

// Mock auth service
jest.mock('../../services/auth');

describe('useAuth', () => {
  let store: ReturnType<typeof configureStore>;
  let wrapper: ({ children }: { children: ReactNode }) => JSX.Element;

  beforeEach(() => {
    store = configureStore({
      reducer: {
        auth: authReducer
      }
    });

    wrapper = ({ children }: { children: ReactNode }) => (
      <Provider store={store}>{children}</Provider>
    );

    // Clear mocks
    jest.clearAllMocks();
  });

  it('should return initial auth state', () => {
    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  describe('login', () => {
    it('should login successfully', async () => {
      const mockResponse = {
        access_token: 'mock-token',
        refresh_token: 'mock-refresh',
        token_type: 'bearer',
        user: {
          id: 1,
          username: 'testuser',
          email: 'test@example.com',
          role: 'student' as const
        }
      };

      (authService.login as jest.Mock).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await act(async () => {
        await result.current.login({
          username: 'testuser',
          password: 'password123'
        });
      });

      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toEqual(mockResponse.user);
      expect(authService.login).toHaveBeenCalledWith({
        username: 'testuser',
        password: 'password123'
      });
    });

    it('should handle login error', async () => {
      const mockError = new Error('Invalid credentials');
      (authService.login as jest.Mock).mockRejectedValue(mockError);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await act(async () => {
        try {
          await result.current.login({
            username: 'testuser',
            password: 'wrongpassword'
          });
        } catch (error) {
          // Expected to throw
        }
      });

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
      expect(result.current.error).toBe('Invalid credentials');
    });
  });

  describe('register', () => {
    it('should register successfully', async () => {
      const mockUser = {
        id: 1,
        username: 'newuser',
        email: 'new@example.com',
        full_name: 'New User',
        role: 'student' as const
      };

      (authService.register as jest.Mock).mockResolvedValue(mockUser);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await act(async () => {
        await result.current.register({
          username: 'newuser',
          email: 'new@example.com',
          password: 'Password123!',
          full_name: 'New User'
        });
      });

      expect(authService.register).toHaveBeenCalledWith({
        username: 'newuser',
        email: 'new@example.com',
        password: 'Password123!',
        full_name: 'New User'
      });
    });

    it('should handle registration error', async () => {
      const mockError = new Error('Username already exists');
      (authService.register as jest.Mock).mockRejectedValue(mockError);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await act(async () => {
        try {
          await result.current.register({
            username: 'existinguser',
            email: 'new@example.com',
            password: 'Password123!',
            full_name: 'New User'
          });
        } catch (error) {
          // Expected to throw
        }
      });

      expect(result.current.error).toBe('Username already exists');
    });
  });

  describe('logout', () => {
    it('should logout successfully', async () => {
      // Set initial authenticated state
      store.dispatch(setCredentials({
        user: {
          id: 1,
          username: 'testuser',
          email: 'test@example.com',
          role: 'student'
        },
        token: 'mock-token'
      }));

      (authService.logout as jest.Mock).mockResolvedValue(undefined);

      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(result.current.isAuthenticated).toBe(true);

      await act(async () => {
        await result.current.logout();
      });

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
      expect(authService.logout).toHaveBeenCalled();
    });
  });

  describe('updateProfile', () => {
    it('should update profile successfully', async () => {
      // Set initial user
      store.dispatch(setCredentials({
        user: {
          id: 1,
          username: 'testuser',
          email: 'test@example.com',
          role: 'student'
        },
        token: 'mock-token'
      }));

      const updatedUser = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        role: 'student' as const,
        full_name: 'Updated Name',
        bio: 'New bio'
      };

      (authService.updateProfile as jest.Mock).mockResolvedValue(updatedUser);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await act(async () => {
        await result.current.updateProfile({
          full_name: 'Updated Name',
          bio: 'New bio'
        });
      });

      expect(result.current.user?.full_name).toBe('Updated Name');
      expect(result.current.user?.bio).toBe('New bio');
    });
  });

  describe('changePassword', () => {
    it('should change password successfully', async () => {
      (authService.changePassword as jest.Mock).mockResolvedValue(undefined);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await act(async () => {
        await result.current.changePassword({
          current_password: 'oldpassword',
          new_password: 'NewPassword123!'
        });
      });

      expect(authService.changePassword).toHaveBeenCalledWith({
        current_password: 'oldpassword',
        new_password: 'NewPassword123!'
      });
    });

    it('should handle change password error', async () => {
      const mockError = new Error('Current password is incorrect');
      (authService.changePassword as jest.Mock).mockRejectedValue(mockError);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await act(async () => {
        try {
          await result.current.changePassword({
            current_password: 'wrongpassword',
            new_password: 'NewPassword123!'
          });
        } catch (error) {
          // Expected to throw
        }
      });

      expect(result.current.error).toBe('Current password is incorrect');
    });
  });

  describe('checkAuth', () => {
    it('should check authentication status', async () => {
      const mockUser = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        role: 'student' as const
      };

      localStorage.setItem('access_token', 'mock-token');
      (authService.getCurrentUser as jest.Mock).mockResolvedValue(mockUser);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await act(async () => {
        await result.current.checkAuth();
      });

      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toEqual(mockUser);
    });

    it('should handle unauthenticated state', async () => {
      localStorage.removeItem('access_token');

      const { result } = renderHook(() => useAuth(), { wrapper });

      await act(async () => {
        await result.current.checkAuth();
      });

      expect(result.current.isAuthenticated).toBe(false);
      expect(authService.getCurrentUser).not.toHaveBeenCalled();
    });
  });
});