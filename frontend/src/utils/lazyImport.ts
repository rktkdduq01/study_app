import { lazy, Suspense, ComponentType } from 'react';
import { CircularProgress, Box } from '@mui/material';

// Loading component for lazy loaded modules
const LoadingFallback = () => (
  <Box
    sx={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '200px',
    }}
  >
    <CircularProgress />
  </Box>
);

/**
 * Wrapper for lazy loaded components with loading fallback
 * @param importFunc - Dynamic import function
 * @returns Wrapped component with Suspense
 */
export function lazyImport<T extends ComponentType<any>>(
  importFunc: () => Promise<{ default: T }>
): T {
  const LazyComponent = lazy(importFunc);

  return ((props: any) => (
    <Suspense fallback={<LoadingFallback />}>
      <LazyComponent {...props} />
    </Suspense>
  )) as T;
}

/**
 * Named export lazy import helper
 * @param importFunc - Dynamic import function
 * @param exportName - Named export to use
 * @returns Wrapped component with Suspense
 */
export function lazyImportNamed<T extends ComponentType<any>>(
  importFunc: () => Promise<any>,
  exportName: string
): T {
  const LazyComponent = lazy(async () => {
    const module = await importFunc();
    return { default: module[exportName] };
  });

  return ((props: any) => (
    <Suspense fallback={<LoadingFallback />}>
      <LazyComponent {...props} />
    </Suspense>
  )) as T;
}