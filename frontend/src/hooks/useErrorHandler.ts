import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useErrorToast } from '../components/ErrorToast';
import { useAppDispatch } from './useAppDispatch';
import { logout } from '../store/slices/authSlice';
import { 
  parseError, 
  isAuthError, 
  isNetworkError,
  AppError 
} from '../utils/errorHandler';

interface UseErrorHandlerOptions {
  onAuthError?: () => void;
  onNetworkError?: () => void;
  showToast?: boolean;
  logError?: boolean;
}

export const useErrorHandler = (options: UseErrorHandlerOptions = {}) => {
  const { showError } = useErrorToast();
  const navigate = useNavigate();
  const dispatch = useAppDispatch();

  const {
    onAuthError,
    onNetworkError,
    showToast = true,
    logError = true,
  } = options;

  const handleError = useCallback(
    (error: unknown, context?: string) => {
      const appError = parseError(error);

      // Log error in development
      if (logError && process.env.NODE_ENV === 'development') {
        console.error(`Error${context ? ` in ${context}` : ''}:`, appError);
      }

      // Show toast notification
      if (showToast) {
        showError(appError);
      }

      // Handle authentication errors
      if (isAuthError(appError)) {
        if (onAuthError) {
          onAuthError();
        } else {
          // Default behavior: logout and redirect to login
          dispatch(logout());
          navigate('/login', { 
            state: { 
              from: window.location.pathname,
              message: 'Your session has expired. Please log in again.'
            }
          });
        }
        return;
      }

      // Handle network errors
      if (isNetworkError(appError)) {
        if (onNetworkError) {
          onNetworkError();
        }
        return;
      }

      // Return the parsed error for additional handling if needed
      return appError;
    },
    [dispatch, navigate, showError, showToast, logError, onAuthError, onNetworkError]
  );

  return { handleError };
};

// Hook for handling async operations with loading state
export const useAsyncOperation = <T = any>(
  options: UseErrorHandlerOptions = {}
) => {
  const { handleError } = useErrorHandler(options);

  const execute = useCallback(
    async (
      operation: () => Promise<T>,
      options?: {
        onSuccess?: (result: T) => void;
        onError?: (error: AppError) => void;
        successMessage?: string;
      }
    ): Promise<T | undefined> => {
      try {
        const result = await operation();
        
        if (options?.onSuccess) {
          options.onSuccess(result);
        }
        
        if (options?.successMessage) {
          const { showSuccess } = useErrorToast();
          showSuccess(options.successMessage);
        }
        
        return result;
      } catch (error) {
        const appError = handleError(error);
        
        if (options?.onError && appError) {
          options.onError(appError);
        }
        
        return undefined;
      }
    },
    [handleError]
  );

  return { execute };
};