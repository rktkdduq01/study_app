import { Alert } from 'react-native';
import { ErrorCategory, ErrorResponse, UserFriendlyError } from '../types/error';
import logger from './logger';

/**
 * Parse various error types into UserFriendlyError
 */
export function parseError(error: unknown): UserFriendlyError {
  // Already a UserFriendlyError
  if (error instanceof UserFriendlyError) {
    return error;
  }

  // Axios error with API response
  if (
    typeof error === 'object' &&
    error !== null &&
    'response' in error &&
    typeof (error as any).response === 'object'
  ) {
    const response = (error as any).response;
    
    // Check if it's our standard error format
    if (response.data && response.data.error) {
      return new UserFriendlyError(response.data.error);
    }
    
    // Fallback for non-standard error responses
    return new UserFriendlyError({
      code: 'HTTP_ERROR',
      message: response.data?.detail || response.data?.message || 'An error occurred',
      user_message: '오류가 발생했습니다',
      action: '잠시 후 다시 시도해주세요',
      category: ErrorCategory.SERVER,
      status_code: response.status || 500,
      data: response.data
    });
  }

  // Network error or timeout
  if (
    typeof error === 'object' &&
    error !== null &&
    'message' in error &&
    'code' in error &&
    (error as any).code === 'ECONNABORTED'
  ) {
    return new UserFriendlyError({
      code: 'NET003',
      message: 'Request timed out',
      user_message: '요청 시간이 초과되었습니다',
      action: '네트워크 상태를 확인하고 다시 시도해주세요',
      category: ErrorCategory.NETWORK,
      status_code: 0
    });
  }

  // Network error
  if (
    typeof error === 'object' &&
    error !== null &&
    'message' in error &&
    ((error as any).message === 'Network Error' ||
     (error as any).message?.includes('fetch'))
  ) {
    return new UserFriendlyError({
      code: 'NET001',
      message: 'Network error',
      user_message: '인터넷 연결을 확인해주세요',
      action: '네트워크 연결 후 다시 시도해주세요',
      category: ErrorCategory.NETWORK,
      status_code: 0
    });
  }

  // Standard Error object
  if (error instanceof Error) {
    return new UserFriendlyError({
      code: 'UNKNOWN_ERROR',
      message: error.message,
      user_message: '예상치 못한 오류가 발생했습니다',
      action: '잠시 후 다시 시도해주세요',
      category: ErrorCategory.SERVER,
      status_code: 500
    });
  }

  // Unknown error type
  return new UserFriendlyError({
    code: 'UNKNOWN_ERROR',
    message: 'An unexpected error occurred',
    user_message: '예상치 못한 오류가 발생했습니다',
    action: '잠시 후 다시 시도해주세요',
    category: ErrorCategory.SERVER,
    status_code: 500,
    data: { originalError: String(error) }
  });
}

/**
 * Show error alert
 */
export function showErrorAlert(error: unknown, onRetry?: () => void): void {
  const appError = parseError(error);
  
  const buttons = [
    {
      text: '확인',
      style: 'default' as const,
    }
  ];
  
  if (onRetry && appError.category !== ErrorCategory.RATE_LIMIT) {
    buttons.unshift({
      text: '다시 시도',
      style: 'default' as const,
      onPress: onRetry
    });
  }
  
  Alert.alert(
    appError.user_message,
    appError.action,
    buttons
  );
}

/**
 * Check if error is authentication related
 */
export function isAuthError(error: unknown): boolean {
  if (error instanceof UserFriendlyError) {
    return error.category === ErrorCategory.AUTHENTICATION || 
           ['AUTH001', 'AUTH002', 'AUTH003', 'AUTH004', 'AUTH005'].includes(error.code);
  }
  return false;
}

/**
 * Check if error is network related
 */
export function isNetworkError(error: unknown): boolean {
  if (error instanceof UserFriendlyError) {
    return error.category === ErrorCategory.NETWORK || error.status_code === 0;
  }
  return false;
}

/**
 * Check if error is validation related
 */
export function isValidationError(error: unknown): boolean {
  if (error instanceof UserFriendlyError) {
    return error.category === ErrorCategory.VALIDATION || error.status_code === 422;
  }
  return false;
}

/**
 * Get validation errors for form fields
 */
export function getValidationErrors(error: UserFriendlyError): Record<string, string[]> {
  if (!isValidationError(error) || !error.data?.user_errors) {
    return {};
  }

  const errors: Record<string, string[]> = {};
  
  for (const err of error.data.user_errors) {
    const field = err.field || 'general';
    if (!errors[field]) {
      errors[field] = [];
    }
    errors[field].push(err.message);
  }
  
  return errors;
}

/**
 * Log error for debugging
 */
export function logError(error: unknown, context?: string): void {
  const appError = parseError(error);
  
  logger.error(
    `Error${context ? ` in ${context}` : ''}`,
    {
      message: appError.message,
      user_message: appError.user_message,
      action: appError.action,
      code: appError.code,
      category: appError.category,
      status: appError.status_code,
      data: appError.data,
      stack: appError.stack
    }
  );
}

/**
 * Handle error with retry logic
 */
export async function handleErrorWithRetry<T>(
  operation: () => Promise<T>,
  maxRetries: number = 3,
  context?: string
): Promise<T> {
  let lastError: unknown;
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error;
      const appError = parseError(error);
      
      // Don't retry certain errors
      if (
        appError.category === ErrorCategory.AUTHENTICATION ||
        appError.category === ErrorCategory.AUTHORIZATION ||
        appError.category === ErrorCategory.VALIDATION ||
        appError.category === ErrorCategory.BUSINESS
      ) {
        throw error;
      }
      
      // Log retry attempt
      logger.warn(
        `Retry attempt ${attempt}/${maxRetries} for ${context || 'operation'}`,
        {
          error: appError.message,
          code: appError.code
        }
      );
      
      // Wait before retry (exponential backoff)
      if (attempt < maxRetries) {
        await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
      }
    }
  }
  
  throw lastError;
}