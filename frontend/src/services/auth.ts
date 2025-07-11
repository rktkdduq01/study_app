import api from './api';
import { LoginRequest, RegisterRequest, AuthResponse, User } from '../types/user';

let currentUser: User | null = null;
let authToken: string | null = null;

export const authService = {
  login: async (data: LoginRequest): Promise<AuthResponse> => {
    const response = await api.post<AuthResponse>('/auth/login', data);
    if (response.data.user) {
      currentUser = response.data.user;
    }
    if (response.data.access_token) {
      authToken = response.data.access_token;
      localStorage.setItem('token', authToken);
    }
    return response.data;
  },

  register: async (data: RegisterRequest): Promise<AuthResponse> => {
    const response = await api.post<AuthResponse>('/auth/register', data);
    if (response.data.user) {
      currentUser = response.data.user;
    }
    if (response.data.access_token) {
      authToken = response.data.access_token;
      localStorage.setItem('token', authToken);
    }
    return response.data;
  },

  logout: async (): Promise<void> => {
    await api.post('/auth/logout');
    currentUser = null;
    authToken = null;
    localStorage.removeItem('token');
  },

  getMe: async (): Promise<User> => {
    const response = await api.get<User>('/auth/me');
    currentUser = response.data;
    return response.data;
  },

  refreshToken: async (): Promise<AuthResponse> => {
    const response = await api.post<AuthResponse>('/auth/refresh');
    if (response.data.access_token) {
      authToken = response.data.access_token;
      localStorage.setItem('token', authToken);
    }
    return response.data;
  },

  getCurrentUser: (): User | null => {
    return currentUser;
  },

  isAuthenticated: (): boolean => {
    return !!authToken || !!localStorage.getItem('token');
  },

  getToken: (): string | null => {
    return authToken || localStorage.getItem('token');
  },

  getRefreshToken: (): string | null => {
    return localStorage.getItem('refreshToken');
  },

  updateProfile: async (data: Partial<User>): Promise<User> => {
    const response = await api.patch<User>('/auth/profile', data);
    currentUser = response.data;
    return response.data;
  },

  changePassword: async (data: { currentPassword: string; newPassword: string }): Promise<void> => {
    await api.post('/auth/change-password', data);
  }
};

export default authService;