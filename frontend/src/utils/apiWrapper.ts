import { AxiosResponse } from 'axios';

/**
 * Generic API wrapper that handles common error patterns
 * @param apiCall - The API call function to execute
 * @param errorMessage - Custom error message for logging
 * @returns The response data
 */
export async function apiWrapper<T>(
  apiCall: () => Promise<AxiosResponse<T>>,
  errorMessage: string
): Promise<T> {
  try {
    const response = await apiCall();
    return response.data;
  } catch (error) {
    console.error(`${errorMessage}:`, error);
    throw error;
  }
}

/**
 * API wrapper with retry logic
 * @param apiCall - The API call function to execute
 * @param errorMessage - Custom error message for logging
 * @param retries - Number of retry attempts (default: 3)
 * @param delay - Delay between retries in ms (default: 1000)
 * @returns The response data
 */
export async function apiWrapperWithRetry<T>(
  apiCall: () => Promise<AxiosResponse<T>>,
  errorMessage: string,
  retries = 3,
  delay = 1000
): Promise<T> {
  let lastError: any;
  
  for (let i = 0; i < retries; i++) {
    try {
      const response = await apiCall();
      return response.data;
    } catch (error: any) {
      lastError = error;
      console.error(`${errorMessage} (attempt ${i + 1}/${retries}):`, error);
      
      // Don't retry on client errors (4xx)
      if (error.response?.status >= 400 && error.response?.status < 500) {
        throw error;
      }
      
      // Wait before retrying
      if (i < retries - 1) {
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }
  
  throw lastError;
}

/**
 * Type-safe API response handler
 */
export interface ApiResponse<T> {
  data: T;
  loading: boolean;
  error: Error | null;
}

/**
 * Creates a standardized API response object
 */
export function createApiResponse<T>(
  data: T | null = null,
  loading = false,
  error: Error | null = null
): ApiResponse<T | null> {
  return { data, loading, error };
}