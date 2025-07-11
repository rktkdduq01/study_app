import React, { createContext, useContext, useState, ReactNode } from 'react';
import { Snackbar, Alert, AlertTitle, IconButton, Collapse } from '@mui/material';
import { Close as CloseIcon, ExpandMore as ExpandMoreIcon } from '@mui/icons-material';
import { AppError, getUserFriendlyMessage } from '../utils/errorHandler';

interface ErrorToastContextType {
  showError: (error: unknown) => void;
  showSuccess: (message: string) => void;
  showWarning: (message: string) => void;
  showInfo: (message: string) => void;
}

const ErrorToastContext = createContext<ErrorToastContextType | undefined>(undefined);

export const useErrorToast = () => {
  const context = useContext(ErrorToastContext);
  if (!context) {
    throw new Error('useErrorToast must be used within ErrorToastProvider');
  }
  return context;
};

interface ToastMessage {
  id: number;
  type: 'error' | 'success' | 'warning' | 'info';
  title?: string;
  message: string;
  details?: string;
  requestId?: string;
}

interface ErrorToastProviderProps {
  children: ReactNode;
}

export const ErrorToastProvider: React.FC<ErrorToastProviderProps> = ({ children }) => {
  const [messages, setMessages] = useState<ToastMessage[]>([]);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const addMessage = (message: Omit<ToastMessage, 'id'>) => {
    const id = Date.now();
    setMessages((prev) => [...prev, { ...message, id }]);
    
    // Auto-remove success messages after 5 seconds
    if (message.type === 'success') {
      setTimeout(() => {
        removeMessage(id);
      }, 5000);
    }
  };

  const removeMessage = (id: number) => {
    setMessages((prev) => prev.filter((msg) => msg.id !== id));
    if (expandedId === id) {
      setExpandedId(null);
    }
  };

  const showError = (error: unknown) => {
    if (error instanceof AppError) {
      addMessage({
        type: 'error',
        title: 'Error',
        message: getUserFriendlyMessage(error),
        details: process.env.NODE_ENV === 'development' ? error.message : undefined,
      });
    } else if (error instanceof Error) {
      addMessage({
        type: 'error',
        title: 'Error',
        message: 'An unexpected error occurred',
        details: process.env.NODE_ENV === 'development' ? error.message : undefined,
      });
    } else {
      addMessage({
        type: 'error',
        title: 'Error',
        message: 'An unexpected error occurred',
      });
    }
  };

  const showSuccess = (message: string) => {
    addMessage({
      type: 'success',
      message,
    });
  };

  const showWarning = (message: string) => {
    addMessage({
      type: 'warning',
      message,
    });
  };

  const showInfo = (message: string) => {
    addMessage({
      type: 'info',
      message,
    });
  };

  const toggleExpand = (id: number) => {
    setExpandedId(expandedId === id ? null : id);
  };

  return (
    <ErrorToastContext.Provider value={{ showError, showSuccess, showWarning, showInfo }}>
      {children}
      {messages.map((message, index) => (
        <Snackbar
          key={message.id}
          open={true}
          anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
          sx={{ top: `${(index + 1) * 80}px !important` }}
        >
          <Alert
            severity={message.type}
            variant="filled"
            sx={{ minWidth: 300, maxWidth: 500 }}
            action={
              <>
                {(message.details || message.requestId) && (
                  <IconButton
                    size="small"
                    color="inherit"
                    onClick={() => toggleExpand(message.id)}
                  >
                    <ExpandMoreIcon
                      sx={{
                        transform: expandedId === message.id ? 'rotate(180deg)' : 'rotate(0deg)',
                        transition: 'transform 0.3s',
                      }}
                    />
                  </IconButton>
                )}
                <IconButton
                  size="small"
                  color="inherit"
                  onClick={() => removeMessage(message.id)}
                >
                  <CloseIcon />
                </IconButton>
              </>
            }
          >
            {message.title && <AlertTitle>{message.title}</AlertTitle>}
            {message.message}
            <Collapse in={expandedId === message.id}>
              {(message.details || message.requestId) && (
                <Box sx={{ mt: 1, fontSize: '0.875rem' }}>
                  {message.details && (
                    <div>
                      <strong>Details:</strong> {message.details}
                    </div>
                  )}
                  {message.requestId && (
                    <div>
                      <strong>Request ID:</strong> {message.requestId}
                    </div>
                  )}
                </Box>
              )}
            </Collapse>
          </Alert>
        </Snackbar>
      ))}
    </ErrorToastContext.Provider>
  );
};

// Hook for using error toast in async operations
export const useAsyncError = () => {
  const { showError } = useErrorToast();
  
  return (error: unknown) => {
    showError(error);
  };
};

// Higher-order component for adding error toast
export function withErrorToast<P extends object>(
  Component: React.ComponentType<P>
): React.FC<P> {
  return (props: P) => (
    <ErrorToastProvider>
      <Component {...props} />
    </ErrorToastProvider>
  );
}

import { Box } from '@mui/material';