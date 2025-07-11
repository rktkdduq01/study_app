import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';
import authService from '../auth';
import { LoginRequest, RegisterRequest } from '../../types/user';

// Create axios mock
const mock = new MockAdapter(axios);

describe('AuthService', () => {
  afterEach(() => {
    mock.reset();
    localStorage.clear();
  });

  describe('login', () => {
    it('should login successfully and store tokens', async () => {
      const loginData: LoginRequest = {
        username: 'testuser',
        password: 'password123'
      };

      const mockResponse = {
        access_token: 'mock-access-token',
        refresh_token: 'mock-refresh-token',
        token_type: 'bearer',
        user: {
          id: 1,
          username: 'testuser',
          email: 'test@example.com',
          role: 'student'
        }
      };

      mock.onPost('/auth/login').reply(200, mockResponse);

      const result = await authService.login(loginData);

      expect(result).toEqual(mockResponse);
      expect(localStorage.getItem('access_token')).toBe('mock-access-token');
      expect(localStorage.getItem('refresh_token')).toBe('mock-refresh-token');
      expect(authService.getToken()).toBe('mock-access-token');
    });

    it('should handle login error', async () => {
      const loginData: LoginRequest = {
        username: 'testuser',
        password: 'wrongpassword'
      };

      mock.onPost('/auth/login').reply(401, {
        error: {
          code: 'AUTHENTICATION_ERROR',
          message: 'Invalid credentials'
        }
      });

      await expect(authService.login(loginData)).rejects.toThrow();
    });
  });

  describe('register', () => {
    it('should register successfully', async () => {
      const registerData: RegisterRequest = {
        username: 'newuser',
        email: 'new@example.com',
        password: 'Password123!',
        full_name: 'New User'
      };

      const mockResponse = {
        id: 1,
        username: 'newuser',
        email: 'new@example.com',
        full_name: 'New User',
        role: 'student',
        created_at: '2024-01-09T12:00:00Z'
      };

      mock.onPost('/auth/register').reply(201, mockResponse);

      const result = await authService.register(registerData);

      expect(result).toEqual(mockResponse);
    });

    it('should handle registration error for duplicate username', async () => {
      const registerData: RegisterRequest = {
        username: 'existinguser',
        email: 'new@example.com',
        password: 'Password123!',
        full_name: 'New User'
      };

      mock.onPost('/auth/register').reply(409, {
        error: {
          code: 'CONFLICT',
          message: 'Username already exists'
        }
      });

      await expect(authService.register(registerData)).rejects.toThrow();
    });
  });

  describe('logout', () => {
    it('should logout and clear tokens', async () => {
      // Set tokens
      localStorage.setItem('access_token', 'mock-token');
      localStorage.setItem('refresh_token', 'mock-refresh');

      mock.onPost('/auth/logout').reply(200, {
        message: 'Successfully logged out'
      });

      await authService.logout();

      expect(localStorage.getItem('access_token')).toBeNull();
      expect(localStorage.getItem('refresh_token')).toBeNull();
      expect(authService.getToken()).toBeNull();
    });
  });

  describe('getCurrentUser', () => {
    it('should get current user info', async () => {
      const mockUser = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        full_name: 'Test User',
        role: 'student'
      };

      mock.onGet('/auth/me').reply(200, mockUser);

      const result = await authService.getCurrentUser();

      expect(result).toEqual(mockUser);
    });

    it('should handle unauthorized error', async () => {
      mock.onGet('/auth/me').reply(401, {
        error: {
          code: 'AUTHENTICATION_ERROR',
          message: 'Token expired'
        }
      });

      await expect(authService.getCurrentUser()).rejects.toThrow();
    });
  });

  describe('refreshToken', () => {
    it('should refresh access token', async () => {
      localStorage.setItem('refresh_token', 'mock-refresh-token');

      const mockResponse = {
        access_token: 'new-access-token',
        token_type: 'bearer'
      };

      mock.onPost('/auth/refresh').reply(200, mockResponse);

      const result = await authService.refreshToken();

      expect(result).toEqual(mockResponse);
      expect(localStorage.getItem('access_token')).toBe('new-access-token');
    });

    it('should return null if no refresh token', async () => {
      const result = await authService.refreshToken();
      expect(result).toBeNull();
    });
  });

  describe('updateProfile', () => {
    it('should update user profile', async () => {
      const updateData = {
        full_name: 'Updated Name',
        bio: 'New bio'
      };

      const mockResponse = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        full_name: 'Updated Name',
        bio: 'New bio',
        role: 'student'
      };

      mock.onPut('/auth/me').reply(200, mockResponse);

      const result = await authService.updateProfile(updateData);

      expect(result).toEqual(mockResponse);
    });
  });

  describe('changePassword', () => {
    it('should change password successfully', async () => {
      const passwordData = {
        current_password: 'oldpassword',
        new_password: 'NewPassword123!'
      };

      mock.onPost('/auth/change-password').reply(200, {
        message: 'Password changed successfully'
      });

      await authService.changePassword(passwordData);

      // Should not throw
      expect(true).toBe(true);
    });

    it('should handle incorrect current password', async () => {
      const passwordData = {
        current_password: 'wrongpassword',
        new_password: 'NewPassword123!'
      };

      mock.onPost('/auth/change-password').reply(400, {
        error: {
          code: 'BUSINESS_LOGIC_ERROR',
          message: 'Current password is incorrect'
        }
      });

      await expect(authService.changePassword(passwordData)).rejects.toThrow();
    });
  });

  describe('token management', () => {
    it('should check if user is authenticated', () => {
      expect(authService.isAuthenticated()).toBe(false);

      localStorage.setItem('access_token', 'mock-token');
      expect(authService.isAuthenticated()).toBe(true);
    });

    it('should get token from localStorage', () => {
      expect(authService.getToken()).toBeNull();

      localStorage.setItem('access_token', 'mock-token');
      expect(authService.getToken()).toBe('mock-token');
    });

    it('should get refresh token from localStorage', () => {
      expect(authService.getRefreshToken()).toBeNull();

      localStorage.setItem('refresh_token', 'mock-refresh');
      expect(authService.getRefreshToken()).toBe('mock-refresh');
    });

    it('should set auth header', () => {
      localStorage.setItem('access_token', 'mock-token');
      authService.setAuthHeader();

      expect(axios.defaults.headers.common['Authorization']).toBe('Bearer mock-token');
    });
  });
});