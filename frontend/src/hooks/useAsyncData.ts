import { useState, useEffect, useCallback, useRef } from 'react';

interface UseAsyncDataOptions {
  immediate?: boolean; // Execute immediately on mount
  onSuccess?: (data: any) => void;
  onError?: (error: Error) => void;
}

interface UseAsyncDataReturn<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  execute: (...args: any[]) => Promise<T | null>;
  reset: () => void;
}

/**
 * Custom hook for managing async data fetching with loading and error states
 * @param asyncFunction - The async function to execute
 * @param options - Configuration options
 * @returns Object with data, loading, error states and control functions
 */
export function useAsyncData<T>(
  asyncFunction: (...args: any[]) => Promise<T>,
  options: UseAsyncDataOptions = {}
): UseAsyncDataReturn<T> {
  const { immediate = true, onSuccess, onError } = options;
  
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  
  // Track if component is mounted to prevent state updates on unmounted components
  const isMountedRef = useRef(true);
  
  useEffect(() => {
    return () => {
      isMountedRef.current = false;
    };
  }, []);
  
  const execute = useCallback(
    async (...args: any[]): Promise<T | null> => {
      try {
        setLoading(true);
        setError(null);
        
        const result = await asyncFunction(...args);
        
        if (isMountedRef.current) {
          setData(result);
          onSuccess?.(result);
        }
        
        return result;
      } catch (err) {
        const error = err instanceof Error ? err : new Error('An unknown error occurred');
        
        if (isMountedRef.current) {
          setError(error);
          onError?.(error);
        }
        
        return null;
      } finally {
        if (isMountedRef.current) {
          setLoading(false);
        }
      }
    },
    [asyncFunction, onSuccess, onError]
  );
  
  const reset = useCallback(() => {
    setData(null);
    setLoading(false);
    setError(null);
  }, []);
  
  useEffect(() => {
    if (immediate) {
      execute();
    }
  }, [immediate]); // eslint-disable-line react-hooks/exhaustive-deps
  
  return { data, loading, error, execute, reset };
}

/**
 * Specialized version for API calls that don't need immediate execution
 */
export function useApiCall<T>(
  apiFunction: (...args: any[]) => Promise<T>
): UseAsyncDataReturn<T> {
  return useAsyncData(apiFunction, { immediate: false });
}