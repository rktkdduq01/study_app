import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig, AxiosResponse } from 'axios';
import authService from './authService';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Flag to prevent multiple simultaneous refresh attempts
let isRefreshing = false;
let refreshSubscribers: ((token: string) => void)[] = [];

// Helper to add requests to queue during token refresh
const subscribeTokenRefresh = (cb: (token: string) => void) => {
  refreshSubscribers.push(cb);
};

// Helper to retry queued requests after token refresh
const onTokenRefreshed = (token: string) => {
  refreshSubscribers.forEach(cb => cb(token));
  refreshSubscribers = [];
};

// Request interceptor to add auth token
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = authService.getToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling and token refresh
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    
    // Handle 401 errors (unauthorized)
    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      // Don't try to refresh for auth endpoints
      if (originalRequest.url?.includes('/auth/')) {
        (authService as any).clearAuth();
        window.location.href = '/login';
        return Promise.reject(error);
      }
      
      if (!isRefreshing) {
        isRefreshing = true;
        originalRequest._retry = true;
        
        try {
          const newToken = await authService.refreshToken();
          
          if (newToken) {
            isRefreshing = false;
            onTokenRefreshed(newToken);
            
            // Retry original request with new token
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
            return api(originalRequest);
          }
        } catch (refreshError) {
          isRefreshing = false;
          refreshSubscribers = [];
          
          // Refresh failed, redirect to login
          (authService as any).clearAuth();
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      }
      
      // Token is being refreshed, queue this request
      return new Promise((resolve) => {
        subscribeTokenRefresh((token: string) => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          resolve(api(originalRequest));
        });
      });
    }
    
    // Handle 403 errors (forbidden)
    if (error.response?.status === 403) {
      const message = error.response?.data && typeof error.response.data === 'object' && 'detail' in error.response.data
        ? (error.response.data as any).detail
        : 'You do not have permission to perform this action';
      
      // You might want to show a notification here
      console.error('Permission denied:', message);
    }
    
    // Handle 429 errors (rate limit)
    if (error.response?.status === 429) {
      const retryAfter = error.response.headers['retry-after'];
      const message = `Rate limit exceeded. Please try again ${retryAfter ? `in ${retryAfter} seconds` : 'later'}.`;
      
      // You might want to show a notification here
      console.error('Rate limit:', message);
    }
    
    // Extract error message
    const message = error.response?.data && typeof error.response.data === 'object' && 'detail' in error.response.data
      ? (error.response.data as any).detail
      : error.message || 'An error occurred';
    
    return Promise.reject(new Error(message));
  }
);

// Helper function to handle file uploads with proper headers
export const uploadFile = async (url: string, file: File, onProgress?: (progress: number) => void) => {
  const formData = new FormData();
  formData.append('file', file);
  
  return api.post(url, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(progress);
      }
    },
  });
};

// Helper to check API health
export const checkApiHealth = async (): Promise<boolean> => {
  try {
    await axios.get(`${API_BASE_URL.replace('/api/v1', '')}/health`);
    return true;
  } catch {
    return false;
  }
};

export default api;