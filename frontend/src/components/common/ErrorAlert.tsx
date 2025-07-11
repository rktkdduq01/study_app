import React from 'react';
import { Alert, AlertTitle, Button, Box } from '@mui/material';
import { ErrorOutline } from '@mui/icons-material';

interface ErrorAlertProps {
  message: string;
  onRetry?: () => void;
  severity?: 'error' | 'warning';
}

const ErrorAlert: React.FC<ErrorAlertProps> = ({ 
  message, 
  onRetry,
  severity = 'error' 
}) => {
  return (
    <Box sx={{ p: 3 }}>
      <Alert 
        severity={severity}
        icon={<ErrorOutline />}
        action={
          onRetry && (
            <Button color="inherit" size="small" onClick={onRetry}>
              다시 시도
            </Button>
          )
        }
      >
        <AlertTitle>
          {severity === 'error' ? '오류가 발생했습니다' : '주의'}
        </AlertTitle>
        {message}
      </Alert>
    </Box>
  );
};

export default ErrorAlert;