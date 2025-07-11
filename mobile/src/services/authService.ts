import AsyncStorage from '@react-native-async-storage/async-storage';
import { User } from '../types/User';

interface LoginCredentials {
  email: string;
  password: string;
}

interface RegisterData {
  username: string;
  email: string;
  password: string;
  role: string;
}

interface AuthResponse {
  user: User;
  token: string;
  refreshToken: string;
}

const API_BASE_URL = 'http://localhost:8000/api'; // Update this to your backend URL

class AuthService {
  private token: string | null = null;
  private refreshToken: string | null = null;

  constructor() {
    this.loadTokensFromStorage();
  }

  private async loadTokensFromStorage(): Promise<void> {
    try {
      const token = await AsyncStorage.getItem('access_token');
      const refreshToken = await AsyncStorage.getItem('refresh_token');
      
      if (token) this.token = token;
      if (refreshToken) this.refreshToken = refreshToken;
    } catch (error) {
      console.error('Failed to load tokens from storage:', error);
    }
  }

  private async saveTokensToStorage(token: string, refreshToken: string): Promise<void> {
    try {
      await AsyncStorage.setItem('access_token', token);
      await AsyncStorage.setItem('refresh_token', refreshToken);
      this.token = token;
      this.refreshToken = refreshToken;
    } catch (error) {
      console.error('Failed to save tokens to storage:', error);
    }
  }

  private async clearTokensFromStorage(): Promise<void> {
    try {
      await AsyncStorage.removeItem('access_token');
      await AsyncStorage.removeItem('refresh_token');
      this.token = null;
      this.refreshToken = null;
    } catch (error) {
      console.error('Failed to clear tokens from storage:', error);
    }
  }

  private async makeRequest(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<Response> {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    // Handle token refresh if needed
    if (response.status === 401 && this.refreshToken) {
      const refreshed = await this.refreshToken();
      if (refreshed) {
        // Retry the original request with new token
        headers.Authorization = `Bearer ${this.token}`;
        return fetch(url, {
          ...options,
          headers,
        });
      }
    }

    return response;
  }

  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await this.makeRequest('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }

    const data = await response.json();
    await this.saveTokensToStorage(data.access_token, data.refresh_token);
    
    return {
      user: data.user,
      token: data.access_token,
      refreshToken: data.refresh_token,
    };
  }

  async register(userData: RegisterData): Promise<AuthResponse> {
    const response = await this.makeRequest('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Registration failed');
    }

    const data = await response.json();
    await this.saveTokensToStorage(data.access_token, data.refresh_token);
    
    return {
      user: data.user,
      token: data.access_token,
      refreshToken: data.refresh_token,
    };
  }

  async logout(): Promise<void> {
    try {
      await this.makeRequest('/auth/logout', {
        method: 'POST',
      });
    } catch (error) {
      console.error('Logout request failed:', error);
    } finally {
      await this.clearTokensFromStorage();
    }
  }

  async refreshToken(): Promise<boolean> {
    if (!this.refreshToken) return false;

    try {
      const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          refresh_token: this.refreshToken,
        }),
      });

      if (!response.ok) {
        await this.clearTokensFromStorage();
        return false;
      }

      const data = await response.json();
      await this.saveTokensToStorage(data.access_token, data.refresh_token);
      return true;
    } catch (error) {
      console.error('Token refresh failed:', error);
      await this.clearTokensFromStorage();
      return false;
    }
  }

  async getCurrentUser(): Promise<{ user: User; token: string }> {
    const response = await this.makeRequest('/auth/me');

    if (!response.ok) {
      throw new Error('Failed to get current user');
    }

    const data = await response.json();
    return {
      user: data.user,
      token: this.token!,
    };
  }

  async verifyEmail(token: string): Promise<{ message: string }> {
    const response = await this.makeRequest('/auth/verify-email', {
      method: 'POST',
      body: JSON.stringify({ token }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Email verification failed');
    }

    return await response.json();
  }

  async resetPassword(email: string): Promise<{ message: string }> {
    const response = await this.makeRequest('/auth/reset-password', {
      method: 'POST',
      body: JSON.stringify({ email }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Password reset failed');
    }

    return await response.json();
  }

  getToken(): string | null {
    return this.token;
  }

  isAuthenticated(): boolean {
    return this.token !== null;
  }
}

export const authService = new AuthService();