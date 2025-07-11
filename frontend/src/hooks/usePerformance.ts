/**
 * Performance monitoring and optimization hooks for React
 */
import { useEffect, useRef, useCallback, useMemo, useState } from 'react';
import { useDispatch } from 'react-redux';

interface PerformanceMetrics {
  renderTime: number;
  renderCount: number;
  lastRenderTimestamp: number;
  slowRenders: number;
  averageRenderTime: number;
}

interface PerformanceOptions {
  enableLogging?: boolean;
  slowRenderThreshold?: number;
  trackRenderReasons?: boolean;
}

/**
 * Hook to monitor component performance
 * 
 * Usage:
 * const metrics = usePerformanceMonitor('MyComponent', {
 *   slowRenderThreshold: 16, // 60fps = 16ms per frame
 *   enableLogging: true
 * });
 */
export function usePerformanceMonitor(
  componentName: string,
  options: PerformanceOptions = {}
) {
  const {
    enableLogging = process.env.NODE_ENV === 'development',
    slowRenderThreshold = 16,
    trackRenderReasons = false
  } = options;

  const metricsRef = useRef<PerformanceMetrics>({
    renderTime: 0,
    renderCount: 0,
    lastRenderTimestamp: 0,
    slowRenders: 0,
    averageRenderTime: 0
  });

  const renderStartTime = useRef<number>(0);
  const previousProps = useRef<any>({});

  // Track render start
  renderStartTime.current = performance.now();

  useEffect(() => {
    // Calculate render time
    const renderEndTime = performance.now();
    const renderTime = renderEndTime - renderStartTime.current;
    
    // Update metrics
    const metrics = metricsRef.current;
    metrics.renderCount++;
    metrics.renderTime = renderTime;
    metrics.lastRenderTimestamp = renderEndTime;
    
    // Track slow renders
    if (renderTime > slowRenderThreshold) {
      metrics.slowRenders++;
      
      if (enableLogging) {
        console.warn(
          `[Performance] Slow render detected in ${componentName}:`,
          {
            renderTime: `${renderTime.toFixed(2)}ms`,
            threshold: `${slowRenderThreshold}ms`,
            renderCount: metrics.renderCount
          }
        );
      }
    }

    // Calculate average render time
    metrics.averageRenderTime = 
      (metrics.averageRenderTime * (metrics.renderCount - 1) + renderTime) / 
      metrics.renderCount;

    // Log performance metrics in development
    if (enableLogging && metrics.renderCount % 10 === 0) {
      console.log(
        `[Performance] ${componentName} metrics:`,
        {
          averageRenderTime: `${metrics.averageRenderTime.toFixed(2)}ms`,
          renderCount: metrics.renderCount,
          slowRenders: metrics.slowRenders,
          slowRenderPercentage: `${((metrics.slowRenders / metrics.renderCount) * 100).toFixed(1)}%`
        }
      );
    }
  });

  // Track render reasons (why component re-rendered)
  useEffect(() => {
    if (trackRenderReasons && enableLogging) {
      const currentProps = { ...previousProps.current };
      const changedProps: string[] = [];

      Object.keys(currentProps).forEach(key => {
        if (currentProps[key] !== previousProps.current[key]) {
          changedProps.push(key);
        }
      });

      if (changedProps.length > 0) {
        console.log(
          `[Performance] ${componentName} re-rendered due to props change:`,
          changedProps
        );
      }

      previousProps.current = currentProps;
    }
  });

  return metricsRef.current;
}

/**
 * Hook for lazy loading components with intersection observer
 * 
 * Usage:
 * const { ref, isVisible } = useLazyLoad({ threshold: 0.1 });
 * return <div ref={ref}>{isVisible && <ExpensiveComponent />}</div>
 */
export function useLazyLoad(options: IntersectionObserverInit = {}) {
  const [isVisible, setIsVisible] = useState(false);
  const elementRef = useRef<HTMLElement | null>(null);
  const observerRef = useRef<IntersectionObserver | null>(null);

  const setRef = useCallback((element: HTMLElement | null) => {
    // Cleanup previous observer
    if (observerRef.current) {
      observerRef.current.disconnect();
    }

    // Create new observer
    if (element) {
      observerRef.current = new IntersectionObserver(
        ([entry]) => {
          if (entry.isIntersecting) {
            setIsVisible(true);
            // Disconnect after becoming visible (one-time load)
            observerRef.current?.disconnect();
          }
        },
        {
          threshold: 0.1,
          rootMargin: '50px',
          ...options
        }
      );

      observerRef.current.observe(element);
    }

    elementRef.current = element;
  }, [options]);

  useEffect(() => {
    return () => {
      observerRef.current?.disconnect();
    };
  }, []);

  return { ref: setRef, isVisible };
}

/**
 * Hook for debouncing expensive operations
 * 
 * Usage:
 * const debouncedSearch = useDebounce(searchTerm, 300);
 */
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

/**
 * Hook for throttling frequent updates
 * 
 * Usage:
 * const throttledScroll = useThrottle(scrollPosition, 100);
 */
export function useThrottle<T>(value: T, limit: number): T {
  const [throttledValue, setThrottledValue] = useState<T>(value);
  const lastRun = useRef(Date.now());

  useEffect(() => {
    const handler = setTimeout(() => {
      if (Date.now() - lastRun.current >= limit) {
        setThrottledValue(value);
        lastRun.current = Date.now();
      }
    }, limit - (Date.now() - lastRun.current));

    return () => {
      clearTimeout(handler);
    };
  }, [value, limit]);

  return throttledValue;
}

/**
 * Hook for virtual scrolling large lists
 * 
 * Usage:
 * const { visibleItems, containerProps, spacerProps } = useVirtualScroll({
 *   items: largeArray,
 *   itemHeight: 50,
 *   containerHeight: 500
 * });
 */
interface VirtualScrollOptions<T> {
  items: T[];
  itemHeight: number;
  containerHeight: number;
  overscan?: number;
  getItemKey?: (item: T, index: number) => string | number;
}

export function useVirtualScroll<T>({
  items,
  itemHeight,
  containerHeight,
  overscan = 3,
  getItemKey = (_, index) => index
}: VirtualScrollOptions<T>) {
  const [scrollTop, setScrollTop] = useState(0);
  
  const visibleRange = useMemo(() => {
    const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
    const endIndex = Math.min(
      items.length,
      Math.ceil((scrollTop + containerHeight) / itemHeight) + overscan
    );
    
    return { startIndex, endIndex };
  }, [scrollTop, itemHeight, containerHeight, overscan, items.length]);

  const visibleItems = useMemo(() => {
    return items
      .slice(visibleRange.startIndex, visibleRange.endIndex)
      .map((item, index) => ({
        item,
        index: visibleRange.startIndex + index,
        key: getItemKey(item, visibleRange.startIndex + index),
        style: {
          position: 'absolute' as const,
          top: (visibleRange.startIndex + index) * itemHeight,
          height: itemHeight,
          width: '100%'
        }
      }));
  }, [items, visibleRange, itemHeight, getItemKey]);

  const totalHeight = items.length * itemHeight;

  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    setScrollTop((e.target as HTMLDivElement).scrollTop);
  }, []);

  return {
    visibleItems,
    containerProps: {
      onScroll: handleScroll,
      style: {
        height: containerHeight,
        overflow: 'auto' as const,
        position: 'relative' as const
      }
    },
    spacerProps: {
      style: {
        height: totalHeight,
        width: '100%',
        position: 'relative' as const
      }
    }
  };
}

/**
 * Hook for monitoring and reporting Web Vitals
 * 
 * Usage:
 * useWebVitals((metric) => {
 *   console.log(metric.name, metric.value);
 *   analytics.track('web_vital', metric);
 * });
 */
export function useWebVitals(onReport: (metric: any) => void) {
  useEffect(() => {
    if ('web-vitals' in window) {
      import('web-vitals').then(({ getCLS, getFID, getFCP, getLCP, getTTFB }) => {
        getCLS(onReport);
        getFID(onReport);
        getFCP(onReport);
        getLCP(onReport);
        getTTFB(onReport);
      });
    }
  }, [onReport]);
}

/**
 * Hook for code splitting and lazy loading routes
 * 
 * Usage:
 * const LazyComponent = useLazyComponent(() => import('./HeavyComponent'));
 */
export function useLazyComponent<T extends React.ComponentType<any>>(
  importFn: () => Promise<{ default: T }>
) {
  const [Component, setComponent] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const module = await importFn();
      setComponent(() => module.default);
    } catch (err) {
      setError(err as Error);
      console.error('Failed to load component:', err);
    } finally {
      setLoading(false);
    }
  }, [importFn]);

  useEffect(() => {
    load();
  }, [load]);

  return { Component, loading, error, retry: load };
}

/**
 * Hook for optimizing Redux selectors with memoization
 * 
 * Usage:
 * const data = useOptimizedSelector(state => 
 *   expensiveComputation(state.someData),
 *   [dependency]
 * );
 */
export function useOptimizedSelector<T>(
  selector: (state: any) => T,
  dependencies: React.DependencyList = []
): T {
  const memoizedSelector = useMemo(
    () => selector,
    // eslint-disable-next-line react-hooks/exhaustive-deps
    dependencies
  );

  return useSelector(memoizedSelector);
}

// Helper function (assuming useSelector is imported)
import { useSelector } from 'react-redux';

/**
 * Performance monitoring context for the entire app
 */
export interface AppPerformanceMetrics {
  pageLoadTime: number;
  timeToInteractive: number;
  apiCallCount: number;
  apiErrorCount: number;
  slowApiCalls: number;
  memoryUsage?: number;
}

export const useAppPerformance = () => {
  const [metrics, setMetrics] = useState<AppPerformanceMetrics>({
    pageLoadTime: 0,
    timeToInteractive: 0,
    apiCallCount: 0,
    apiErrorCount: 0,
    slowApiCalls: 0
  });

  useEffect(() => {
    // Page load time
    if (window.performance && window.performance.timing) {
      const loadTime = 
        window.performance.timing.loadEventEnd - 
        window.performance.timing.navigationStart;
      
      setMetrics(prev => ({ ...prev, pageLoadTime: loadTime }));
    }

    // Memory usage (if available)
    if ('memory' in performance) {
      const memoryUsage = (performance as any).memory.usedJSHeapSize / 1048576; // MB
      setMetrics(prev => ({ ...prev, memoryUsage }));
    }
  }, []);

  const trackApiCall = useCallback((duration: number, isError: boolean = false) => {
    setMetrics(prev => ({
      ...prev,
      apiCallCount: prev.apiCallCount + 1,
      apiErrorCount: isError ? prev.apiErrorCount + 1 : prev.apiErrorCount,
      slowApiCalls: duration > 1000 ? prev.slowApiCalls + 1 : prev.slowApiCalls
    }));
  }, []);

  return { metrics, trackApiCall };
};