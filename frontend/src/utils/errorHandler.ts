/**
 * Error handling utilities for the frontend
 */
import { ErrorCategory, ErrorResponse, UserFriendlyError } from '../types/error';

export { UserFriendlyError as AppError } from '../types/error';

/**
 * Extract error information from various error types
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
 * Get user-friendly error message based on error code
 * @deprecated Use error.user_message directly
 */
export function getUserFriendlyMessage(error: UserFriendlyError): string {
  return error.user_message || error.message;
}

/**
 * Check if error is a specific type
 */
export function isErrorType(error: unknown, code: string): boolean {
  if (error instanceof UserFriendlyError) {
    return error.code === code;
  }
  return false;
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
 * Check if error is a server error
 */
export function isServerError(error: unknown): boolean {
  if (error instanceof UserFriendlyError) {
    return error.category === ErrorCategory.SERVER || error.status_code >= 500;
  }
  return false;
}

/**
 * Get validation error details
 */
export function getValidationErrors(error: UserFriendlyError): Record<string, string[]> {
  if (!isValidationError(error) || !error.data?.user_errors) {
    return {};
  }

  const errors: Record<string, string[]> = {};
  
  // Use user-friendly errors if available
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
  
  console.group(`🚨 Error${context ? ` in ${context}` : ''}`);
  console.error('Message:', appError.message);
  console.error('User Message:', appError.user_message);
  console.error('Action:', appError.action);
  console.error('Code:', appError.code);
  console.error('Category:', appError.category);
  console.error('Status:', appError.status_code);
  if (appError.data?.request_id) {
    console.error('Request ID:', appError.data.request_id);
  }
  if (appError.data) {
    console.error('Data:', appError.data);
  }
  console.trace('Stack trace');
  console.groupEnd();
}

/**
 * Create a formatted error message for forms
 */
export function formatFormError(error: UserFriendlyError): string {
  if (isValidationError(error)) {
    const errors = getValidationErrors(error);
    const messages = Object.entries(errors)
      .map(([field, msgs]) => msgs.join(', '))
      .join('\n');
    return messages || error.user_message;
  }
  
  return error.user_message;
}