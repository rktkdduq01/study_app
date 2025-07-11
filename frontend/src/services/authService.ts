import api from './api';
import { LoginRequest, LoginResponse, RegisterRequest, User } from '../types/user';

interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

class AuthService {
  private static TOKEN_KEY = 'access_token';
  private static REFRESH_TOKEN_KEY = 'refresh_token';
  private static USER_KEY = 'user';

  async login(credentials: LoginRequest): Promise<TokenResponse> {
    const formData = new URLSearchParams();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);
    
    const response = await api.post<TokenResponse>('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    
    // Store tokens
    if (response.data.access_token) {
      localStorage.setItem(AuthService.TOKEN_KEY, response.data.access_token);
      localStorage.setItem(AuthService.REFRESH_TOKEN_KEY, response.data.refresh_token);
    }
    
    // Get and store user info
    const user = await this.getCurrentUser();
    localStorage.setItem(AuthService.USER_KEY, JSON.stringify(user));
    
    return response.data;
  }

  async register(userData: RegisterRequest): Promise<User> {
    const response = await api.post<User>('/auth/register', userData);
    return response.data;
  }

  async getCurrentUser(): Promise<User> {
    const response = await api.get<User>('/auth/me');
    return response.data;
  }

  async refreshToken(): Promise<string | null> {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) {
      return null;
    }

    try {
      const response = await api.post<TokenResponse>('/auth/refresh', {
        refresh_token: refreshToken
      });
      
      if (response.data.access_token) {
        localStorage.setItem(AuthService.TOKEN_KEY, response.data.access_token);
        return response.data.access_token;
      }
      
      return null;
    } catch (error) {
      // If refresh fails, clear auth and redirect to login
      this.clearAuth();
      throw error;
    }
  }

  async logout(): Promise<void> {
    try {
      const refreshToken = this.getRefreshToken();
      
      // Call logout endpoint to revoke tokens
      await api.post('/auth/logout', refreshToken ? { refresh_token: refreshToken } : {});
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear local storage regardless
      this.clearAuth();
    }
  }

  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    await api.post('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
  }

  async updateProfile(data: Partial<User>): Promise<User> {
    const response = await api.put<User>('/users/me', data);
    
    // Update stored user
    const currentUser = this.getStoredUser();
    if (currentUser) {
      const updatedUser = { ...currentUser, ...response.data };
      localStorage.setItem(AuthService.USER_KEY, JSON.stringify(updatedUser));
    }
    
    return response.data;
  }

  getToken(): string | null {
    return localStorage.getItem(AuthService.TOKEN_KEY);
  }

  getRefreshToken(): string | null {
    return localStorage.getItem(AuthService.REFRESH_TOKEN_KEY);
  }

  getStoredUser(): User | null {
    const userStr = localStorage.getItem(AuthService.USER_KEY);
    if (!userStr) return null;
    
    try {
      return JSON.parse(userStr);
    } catch {
      return null;
    }
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  private clearAuth(): void {
    localStorage.removeItem(AuthService.TOKEN_KEY);
    localStorage.removeItem(AuthService.REFRESH_TOKEN_KEY);
    localStorage.removeItem(AuthService.USER_KEY);
  }

  // Validate password strength
  validatePassword(password: string): { valid: boolean; errors: string[] } {
    const errors: string[] = [];
    
    if (password.length < 8) {
      errors.push('Password must be at least 8 characters long');
    }
    
    if (!/[A-Z]/.test(password)) {
      errors.push('Password must contain at least one uppercase letter');
    }
    
    if (!/[a-z]/.test(password)) {
      errors.push('Password must contain at least one lowercase letter');
    }
    
    if (!/[0-9]/.test(password)) {
      errors.push('Password must contain at least one digit');
    }
    
    if (!/[!@#$%^&*()_+\-=[\]{}|;:,.<>?]/.test(password)) {
      errors.push('Password must contain at least one special character');
    }
    
    return {
      valid: errors.length === 0,
      errors
    };
  }
}

export default new AuthService();