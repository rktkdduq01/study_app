import React from 'react';
import { 
  Button, 
  Alert, 
  AlertTitle, 
  Card, 
  CardContent, 
  CardActions,
  Box,
  Typography,
  Collapse
} from '@mui/material';
import { 
  Error as AlertCircleIcon, 
  Refresh as RefreshCwIcon, 
  Home as HomeIcon, 
  Help as HelpCircleIcon 
} from '@mui/icons-material';
import { ErrorCategory } from '../types/error';

interface ErrorDisplayProps {
  error: {
    code: string;
    message: string;
    user_message: string;
    action: string;
    category: ErrorCategory;
    data?: any;
  };
  onRetry?: () => void;
  onGoHome?: () => void;
  onHelp?: () => void;
  minimal?: boolean;
}

const categoryConfig: Record<string, { severity: 'error' | 'warning' | 'info' | 'success' }> = {
  authentication: { severity: 'warning' },
  authorization: { severity: 'warning' },
  validation: { severity: 'error' },
  network: { severity: 'error' },
  server: { severity: 'error' },
  business: { severity: 'info' },
  rate_limit: { severity: 'warning' },
  maintenance: { severity: 'info' }
};

export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  error,
  onRetry,
  onGoHome,
  onHelp,
  minimal = false
}) => {
  const config = categoryConfig[error.category] || categoryConfig.server;

  // Minimal display for inline errors
  if (minimal) {
    return (
      <Alert severity={config.severity} icon={<AlertCircleIcon />}>
        <AlertTitle>{error.user_message}</AlertTitle>
        {error.action && (
          <Typography variant="body2" color="text.secondary">
            {error.action}
          </Typography>
        )}
      </Alert>
    );
  }

  // Full error display
  return (
    <Card sx={{ border: 2, borderColor: `${config.severity}.main` }}>
      <CardContent sx={{ pt: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
          <Box sx={{ 
            p: 1.5, 
            borderRadius: '50%', 
            bgcolor: `${config.severity}.light`,
            color: `${config.severity}.main`
          }}>
            <AlertCircleIcon sx={{ fontSize: 30 }} />
          </Box>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h6" color={`${config.severity}.main`} gutterBottom>
              {error.user_message}
            </Typography>
            <Typography variant="body1" color="text.secondary" paragraph>
              {error.action}
            </Typography>
            
            {/* Field-specific errors for validation */}
            {error.category === 'validation' && error.data?.user_errors && (
              <Box sx={{ mt: 2 }}>
                {error.data.user_errors.map((fieldError: any, index: number) => (
                  <Box key={index} sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <Typography variant="body2" color="error">•</Typography>
                    <Typography variant="body2" color="text.secondary">
                      <strong>{fieldError.field}:</strong> {fieldError.message}
                    </Typography>
                  </Box>
                ))}
              </Box>
            )}
            
            {/* Retry countdown for rate limiting */}
            {error.category === 'rate_limit' && error.data?.retry_after && (
              <RetryCountdown seconds={error.data.retry_after} onComplete={onRetry} />
            )}
            
            {/* Debug info in development */}
            {process.env.NODE_ENV === 'development' && (
              <Box sx={{ mt: 2 }}>
                <Collapse in={true}>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                    개발자 정보
                  </Typography>
                  <Box sx={{ 
                    bgcolor: 'grey.100', 
                    p: 1, 
                    borderRadius: 1, 
                    overflow: 'auto',
                    fontSize: '0.75rem',
                    fontFamily: 'monospace'
                  }}>
                    <pre style={{ margin: 0 }}>
                      {JSON.stringify({ code: error.code, message: error.message, data: error.data }, null, 2)}
                    </pre>
                  </Box>
                </Collapse>
              </Box>
            )}
          </Box>
        </Box>
      </CardContent>
      
      <CardActions sx={{ gap: 1, p: 2, bgcolor: 'grey.50' }}>
        {onRetry && error.category !== 'rate_limit' && (
          <Button
            variant="outlined"
            size="small"
            onClick={onRetry}
            startIcon={<RefreshCwIcon />}
          >
            다시 시도
          </Button>
        )}
        
        {onGoHome && (
          <Button
            variant="outlined"
            size="small"
            onClick={onGoHome}
            startIcon={<HomeIcon />}
          >
            홈으로
          </Button>
        )}
        
        {onHelp && (
          <Button
            variant="outlined"
            size="small"
            onClick={onHelp}
            startIcon={<HelpCircleIcon />}
          >
            도움말
          </Button>
        )}
      </CardActions>
    </Card>
  );
};

// Retry countdown component for rate limiting
const RetryCountdown: React.FC<{ seconds: number; onComplete?: () => void }> = ({
  seconds,
  onComplete
}) => {
  const [remaining, setRemaining] = React.useState(seconds);

  React.useEffect(() => {
    if (remaining <= 0) {
      onComplete?.();
      return;
    }

    const timer = setTimeout(() => {
      setRemaining(remaining - 1);
    }, 1000);

    return () => clearTimeout(timer);
  }, [remaining, onComplete]);

  return (
    <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
      {remaining}초 후에 다시 시도할 수 있습니다...
    </Typography>
  );
};

// Error fallback for React Error Boundary
export const ErrorFallback: React.FC<{
  error: Error;
  resetErrorBoundary: () => void;
}> = ({ error, resetErrorBoundary }) => {
  const errorDisplay = {
    code: 'REACT_ERROR',
    message: error.message,
    user_message: '페이지를 불러오는 중 오류가 발생했습니다',
    action: '페이지를 새로고침하거나 잠시 후 다시 시도해주세요',
    category: 'server' as ErrorCategory,
    data: {}
  };

  return (
    <Box 
      sx={{ 
        minHeight: '100vh', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center', 
        p: 2 
      }}
    >
      <Box sx={{ maxWidth: 'sm', width: '100%' }}>
        <ErrorDisplay
          error={errorDisplay}
          onRetry={resetErrorBoundary}
          onGoHome={() => window.location.href = '/'}
        />
      </Box>
    </Box>
  );
};