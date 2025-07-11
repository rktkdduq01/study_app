import { configureStore } from '@reduxjs/toolkit';
import authReducer, {
  setCredentials,
  logout,
  updateUser,
  setLoading,
  setError,
  clearError
} from '../slices/authSlice';
import { AuthState } from '../../types/auth';

describe('authSlice', () => {
  let store: ReturnType<typeof configureStore>;

  beforeEach(() => {
    store = configureStore({
      reducer: {
        auth: authReducer
      }
    });
  });

  it('should have initial state', () => {
    const state = store.getState().auth;
    
    expect(state.user).toBeNull();
    expect(state.token).toBeNull();
    expect(state.isAuthenticated).toBe(false);
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
  });

  describe('setCredentials', () => {
    it('should set user and token', () => {
      const credentials = {
        user: {
          id: 1,
          username: 'testuser',
          email: 'test@example.com',
          full_name: 'Test User',
          role: 'student' as const
        },
        token: 'mock-token'
      };

      store.dispatch(setCredentials(credentials));
      const state = store.getState().auth;

      expect(state.user).toEqual(credentials.user);
      expect(state.token).toBe(credentials.token);
      expect(state.isAuthenticated).toBe(true);
      expect(state.error).toBeNull();
    });

    it('should clear error when setting credentials', () => {
      // Set error first
      store.dispatch(setError('Previous error'));
      
      // Set credentials
      store.dispatch(setCredentials({
        user: { id: 1, username: 'test', email: 'test@example.com', role: 'student' },
        token: 'token'
      }));

      const state = store.getState().auth;
      expect(state.error).toBeNull();
    });
  });

  describe('logout', () => {
    it('should clear user and token', () => {
      // Set credentials first
      store.dispatch(setCredentials({
        user: { id: 1, username: 'test', email: 'test@example.com', role: 'student' },
        token: 'token'
      }));

      // Logout
      store.dispatch(logout());
      const state = store.getState().auth;

      expect(state.user).toBeNull();
      expect(state.token).toBeNull();
      expect(state.isAuthenticated).toBe(false);
    });
  });

  describe('updateUser', () => {
    it('should update user data', () => {
      // Set initial user
      store.dispatch(setCredentials({
        user: {
          id: 1,
          username: 'testuser',
          email: 'test@example.com',
          role: 'student'
        },
        token: 'token'
      }));

      // Update user
      const updates = {
        full_name: 'Updated Name',
        bio: 'New bio'
      };

      store.dispatch(updateUser(updates));
      const state = store.getState().auth;

      expect(state.user).toEqual({
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        role: 'student',
        full_name: 'Updated Name',
        bio: 'New bio'
      });
    });

    it('should not update if user is null', () => {
      store.dispatch(updateUser({ full_name: 'Test' }));
      const state = store.getState().auth;

      expect(state.user).toBeNull();
    });
  });

  describe('loading states', () => {
    it('should set loading state', () => {
      store.dispatch(setLoading(true));
      expect(store.getState().auth.isLoading).toBe(true);

      store.dispatch(setLoading(false));
      expect(store.getState().auth.isLoading).toBe(false);
    });
  });

  describe('error handling', () => {
    it('should set error message', () => {
      const errorMessage = 'Authentication failed';
      store.dispatch(setError(errorMessage));
      
      const state = store.getState().auth;
      expect(state.error).toBe(errorMessage);
    });

    it('should clear error', () => {
      // Set error first
      store.dispatch(setError('Some error'));
      expect(store.getState().auth.error).toBe('Some error');

      // Clear error
      store.dispatch(clearError());
      expect(store.getState().auth.error).toBeNull();
    });
  });

  describe('complex scenarios', () => {
    it('should handle login flow', () => {
      // Start loading
      store.dispatch(setLoading(true));
      expect(store.getState().auth.isLoading).toBe(true);

      // Set credentials on success
      store.dispatch(setCredentials({
        user: {
          id: 1,
          username: 'testuser',
          email: 'test@example.com',
          role: 'student'
        },
        token: 'auth-token'
      }));

      // Stop loading
      store.dispatch(setLoading(false));

      const state = store.getState().auth;
      expect(state.isAuthenticated).toBe(true);
      expect(state.isLoading).toBe(false);
      expect(state.error).toBeNull();
    });

    it('should handle login error flow', () => {
      // Start loading
      store.dispatch(setLoading(true));

      // Set error on failure
      store.dispatch(setError('Invalid credentials'));

      // Stop loading
      store.dispatch(setLoading(false));

      const state = store.getState().auth;
      expect(state.isAuthenticated).toBe(false);
      expect(state.isLoading).toBe(false);
      expect(state.error).toBe('Invalid credentials');
    });

    it('should handle token refresh', () => {
      // Initial auth state
      store.dispatch(setCredentials({
        user: {
          id: 1,
          username: 'testuser',
          email: 'test@example.com',
          role: 'student'
        },
        token: 'old-token'
      }));

      // Refresh token
      store.dispatch(setCredentials({
        user: store.getState().auth.user!,
        token: 'new-token'
      }));

      const state = store.getState().auth;
      expect(state.token).toBe('new-token');
      expect(state.user?.username).toBe('testuser');
    });
  });
});