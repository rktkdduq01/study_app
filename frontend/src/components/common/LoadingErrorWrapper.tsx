import React, { ReactNode } from 'react';
import {
  Box,
  CircularProgress,
  Alert,
  AlertTitle,
  Button,
  Typography,
  Paper,
} from '@mui/material';
import { Refresh as RefreshIcon } from '@mui/icons-material';

interface LoadingErrorWrapperProps {
  loading: boolean;
  error: Error | null;
  onRetry?: () => void;
  children: ReactNode;
  loadingMessage?: string;
  errorTitle?: string;
  minHeight?: string | number;
  showErrorDetails?: boolean;
  loadingComponent?: ReactNode;
  emptyState?: {
    show: boolean;
    message: string;
    action?: ReactNode;
  };
}

export const LoadingErrorWrapper: React.FC<LoadingErrorWrapperProps> = ({
  loading,
  error,
  onRetry,
  children,
  loadingMessage = 'Loading...',
  errorTitle = 'Error',
  minHeight = 200,
  showErrorDetails = false,
  loadingComponent,
  emptyState,
}) => {
  // Loading state
  if (loading) {
    if (loadingComponent) {
      return <>{loadingComponent}</>;
    }
    
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight,
          p: 3,
        }}
      >
        <CircularProgress />
        {loadingMessage && (
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            {loadingMessage}
          </Typography>
        )}
      </Box>
    );
  }

  // Error state
  if (error) {
    return (
      <Box sx={{ p: 3, minHeight }}>
        <Alert
          severity="error"
          action={
            onRetry && (
              <Button
                color="inherit"
                size="small"
                onClick={onRetry}
                startIcon={<RefreshIcon />}
              >
                Retry
              </Button>
            )
          }
        >
          <AlertTitle>{errorTitle}</AlertTitle>
          {error.message || 'An unexpected error occurred'}
          {showErrorDetails && error.stack && (
            <Box
              component="pre"
              sx={{
                mt: 2,
                p: 1,
                bgcolor: 'grey.100',
                borderRadius: 1,
                fontSize: '0.75rem',
                overflow: 'auto',
              }}
            >
              {error.stack}
            </Box>
          )}
        </Alert>
      </Box>
    );
  }

  // Empty state
  if (emptyState?.show) {
    return (
      <Paper sx={{ p: 4, textAlign: 'center', minHeight }}>
        <Typography variant="body1" color="text.secondary" gutterBottom>
          {emptyState.message}
        </Typography>
        {emptyState.action}
      </Paper>
    );
  }

  // Normal content
  return <>{children}</>;
};

// Specialized version for full-page loading
export const PageLoadingWrapper: React.FC<LoadingErrorWrapperProps> = (props) => (
  <LoadingErrorWrapper {...props} minHeight="calc(100vh - 200px)" />
);

// Specialized version for card/section loading
export const SectionLoadingWrapper: React.FC<LoadingErrorWrapperProps> = (props) => (
  <LoadingErrorWrapper {...props} minHeight={300} />
);