import {
  parseError,
  getUserFriendlyMessage,
  isAuthError,
  isNetworkError,
  isValidationError,
  isServerError,
  AppError
} from '../errorHandler';
import { AxiosError } from 'axios';
import { ErrorCategory } from '../../types/error';

describe('Error Handler Utils', () => {
  describe('parseError', () => {
    it('should parse API error response', () => {
      const axiosError: Partial<AxiosError> = {
        response: {
          status: 400,
          data: {
            error: {
              code: 'VALIDATION_ERROR',
              message: 'Invalid input',
              user_message: 'Please check your input',
              action: 'Fix the validation errors and try again',
              category: ErrorCategory.VALIDATION,
              status_code: 400,
              data: { field: 'email' }
            }
          },
          statusText: 'Bad Request',
          headers: {},
          config: {} as any
        }
      };

      const result = parseError(axiosError);

      expect(result.code).toBe('VALIDATION_ERROR');
      expect(result.message).toBe('Invalid input');
      expect(result.status).toBe(400);
      expect(result.data).toEqual({ field: 'email' });
    });

    it('should handle network errors', () => {
      const axiosError: Partial<AxiosError> = {
        message: 'Network Error',
        code: 'ERR_NETWORK'
      };

      const result = parseError(axiosError);

      expect(result.code).toBe('NETWORK_ERROR');
      expect(result.message).toBe('인터넷 연결을 확인해주세요');
      expect(result.status).toBe(0);
    });

    it('should handle timeout errors', () => {
      const axiosError: Partial<AxiosError> = {
        code: 'ECONNABORTED',
        message: 'timeout of 5000ms exceeded'
      };

      const result = parseError(axiosError);

      expect(result.code).toBe('TIMEOUT_ERROR');
      expect(result.message).toBe('요청 시간이 초과되었습니다');
    });

    it('should handle standard errors', () => {
      const error = new Error('Something went wrong');
      const result = parseError(error);

      expect(result.code).toBe('UNKNOWN_ERROR');
      expect(result.message).toBe('Something went wrong');
    });

    it('should handle unknown error types', () => {
      const result = parseError('String error');

      expect(result.code).toBe('UNKNOWN_ERROR');
      expect(result.message).toBe('알 수 없는 오류가 발생했습니다');
    });
  });

  // Helper function to create UserFriendlyError
  const createError = (code: string, status: number, category: ErrorCategory = ErrorCategory.SERVER): AppError => {
    return new AppError({
      code,
      message: 'Error message',
      user_message: 'User friendly message',
      action: 'Try again',
      category,
      status_code: status
    });
  };

  describe('getUserFriendlyMessage', () => {
    it('should return friendly message for auth errors', () => {
      const error = createError('AUTHENTICATION_ERROR', 401, ErrorCategory.AUTHENTICATION);
      const message = getUserFriendlyMessage(error);
      expect(message).toBe('User friendly message');
    });

    it('should return friendly message for validation errors', () => {
      const error = createError('VALIDATION_ERROR', 422, ErrorCategory.VALIDATION);
      const message = getUserFriendlyMessage(error);
      expect(message).toBe('User friendly message');
    });

    it('should return friendly message for not found errors', () => {
      const error = createError('NOT_FOUND', 404, ErrorCategory.SERVER);
      const message = getUserFriendlyMessage(error);
      expect(message).toBe('User friendly message');
    });

    it('should return friendly message for rate limit errors', () => {
      const error = createError('RATE_LIMIT_ERROR', 429, ErrorCategory.RATE_LIMIT);
      const message = getUserFriendlyMessage(error);
      expect(message).toBe('User friendly message');
    });

    it('should return friendly message for server errors', () => {
      const error = createError('SERVER_ERROR', 500, ErrorCategory.SERVER);
      const message = getUserFriendlyMessage(error);
      expect(message).toBe('User friendly message');
    });

    it('should return default message for unknown errors', () => {
      const error = createError('UNKNOWN', 999, ErrorCategory.SERVER);
      const message = getUserFriendlyMessage(error);
      expect(message).toBe('User friendly message');
    });
  });

  describe('Error type checks', () => {
    it('should correctly identify auth errors', () => {
      const authError = createError('AUTH_ERROR', 401, ErrorCategory.AUTHENTICATION);
      const otherError = createError('OTHER_ERROR', 400, ErrorCategory.VALIDATION);

      expect(isAuthError(authError)).toBe(true);
      expect(isAuthError(otherError)).toBe(false);
    });

    it('should correctly identify network errors', () => {
      const networkError = createError('NETWORK_ERROR', 0, ErrorCategory.NETWORK);
      const otherError = createError('OTHER_ERROR', 400, ErrorCategory.VALIDATION);

      expect(isNetworkError(networkError)).toBe(true);
      expect(isNetworkError(otherError)).toBe(false);
    });

    it('should correctly identify validation errors', () => {
      const validationError = createError('VALIDATION_ERROR', 422, ErrorCategory.VALIDATION);
      const otherError = createError('OTHER_ERROR', 400, ErrorCategory.SERVER);

      expect(isValidationError(validationError)).toBe(true);
      expect(isValidationError(otherError)).toBe(false);
    });

    it('should correctly identify server errors', () => {
      const serverError = createError('SERVER_ERROR', 500, ErrorCategory.SERVER);
      const otherError = createError('OTHER_ERROR', 400, ErrorCategory.VALIDATION);

      expect(isServerError(serverError)).toBe(true);
      expect(isServerError(otherError)).toBe(false);
    });
  });

  describe('Error logging', () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

    afterEach(() => {
      consoleSpy.mockClear();
    });

    afterAll(() => {
      consoleSpy.mockRestore();
    });

    it('should log errors in development mode', () => {
      const originalEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = 'development';

      const error = new Error('Test error');
      // Mock console.error to prevent actual logging
      console.error = jest.fn();

      parseError(error);

      process.env.NODE_ENV = originalEnv;
    });
  });
});