import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
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
  minimal?: boolean;
  loading?: boolean;
}

const categoryConfig = {
  authentication: {
    icon: 'lock-outline',
    color: '#F59E0B',
    backgroundColor: '#FEF3C7',
  },
  authorization: {
    icon: 'block',
    color: '#F97316',
    backgroundColor: '#FED7AA',
  },
  validation: {
    icon: 'error-outline',
    color: '#EF4444',
    backgroundColor: '#FEE2E2',
  },
  network: {
    icon: 'wifi-off',
    color: '#6B7280',
    backgroundColor: '#F3F4F6',
  },
  server: {
    icon: 'cloud-off',
    color: '#EF4444',
    backgroundColor: '#FEE2E2',
  },
  business: {
    icon: 'info-outline',
    color: '#3B82F6',
    backgroundColor: '#DBEAFE',
  },
  rate_limit: {
    icon: 'timer',
    color: '#8B5CF6',
    backgroundColor: '#EDE9FE',
  },
  maintenance: {
    icon: 'build',
    color: '#6366F1',
    backgroundColor: '#E0E7FF',
  },
};

export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  error,
  onRetry,
  onGoHome,
  minimal = false,
  loading = false,
}) => {
  const config = categoryConfig[error.category] || categoryConfig.server;

  // Minimal display for inline errors
  if (minimal) {
    return (
      <View style={[styles.minimalContainer, { backgroundColor: config.backgroundColor }]}>
        <Icon name={config.icon} size={20} color={config.color} style={styles.minimalIcon} />
        <View style={styles.minimalContent}>
          <Text style={[styles.minimalMessage, { color: config.color }]}>
            {error.user_message}
          </Text>
          {error.action && (
            <Text style={styles.minimalAction}>{error.action}</Text>
          )}
        </View>
      </View>
    );
  }

  // Full error display
  return (
    <View style={styles.container}>
      <View style={[styles.card, { backgroundColor: config.backgroundColor }]}>
        <View style={styles.iconContainer}>
          <Icon name={config.icon} size={48} color={config.color} />
        </View>
        
        <Text style={[styles.title, { color: config.color }]}>
          {error.user_message}
        </Text>
        
        <Text style={styles.action}>{error.action}</Text>
        
        {/* Field-specific errors for validation */}
        {error.category === 'validation' && error.data?.user_errors && (
          <View style={styles.validationErrors}>
            {error.data.user_errors.map((fieldError: any, index: number) => (
              <View key={index} style={styles.validationError}>
                <Text style={styles.validationErrorText}>
                  • {fieldError.field}: {fieldError.message}
                </Text>
              </View>
            ))}
          </View>
        )}
        
        {/* Retry countdown for rate limiting */}
        {error.category === 'rate_limit' && error.data?.retry_after && (
          <RetryCountdown seconds={error.data.retry_after} onComplete={onRetry} />
        )}
        
        {/* Debug info in development */}
        {__DEV__ && (
          <View style={styles.debugInfo}>
            <Text style={styles.debugText}>Error Code: {error.code}</Text>
            <Text style={styles.debugText}>Technical: {error.message}</Text>
          </View>
        )}
      </View>
      
      <View style={styles.actions}>
        {onRetry && error.category !== 'rate_limit' && (
          <TouchableOpacity
            style={[styles.button, styles.retryButton]}
            onPress={onRetry}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator size="small" color="#FFFFFF" />
            ) : (
              <>
                <Icon name="refresh" size={20} color="#FFFFFF" />
                <Text style={styles.buttonText}>다시 시도</Text>
              </>
            )}
          </TouchableOpacity>
        )}
        
        {onGoHome && (
          <TouchableOpacity
            style={[styles.button, styles.homeButton]}
            onPress={onGoHome}
          >
            <Icon name="home" size={20} color="#6B7280" />
            <Text style={[styles.buttonText, styles.homeButtonText]}>홈으로</Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
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
    <View style={styles.countdown}>
      <Text style={styles.countdownText}>
        {remaining}초 후에 다시 시도할 수 있습니다...
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  card: {
    width: '100%',
    borderRadius: 12,
    padding: 24,
    alignItems: 'center',
    marginBottom: 20,
  },
  iconContainer: {
    marginBottom: 16,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    textAlign: 'center',
    marginBottom: 8,
  },
  action: {
    fontSize: 14,
    color: '#4B5563',
    textAlign: 'center',
    marginBottom: 16,
  },
  validationErrors: {
    width: '100%',
    marginTop: 12,
  },
  validationError: {
    marginBottom: 4,
  },
  validationErrorText: {
    fontSize: 12,
    color: '#DC2626',
  },
  countdown: {
    marginTop: 8,
  },
  countdownText: {
    fontSize: 14,
    color: '#6B7280',
  },
  debugInfo: {
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
    width: '100%',
  },
  debugText: {
    fontSize: 10,
    color: '#9CA3AF',
    marginBottom: 2,
  },
  actions: {
    flexDirection: 'row',
    gap: 12,
  },
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
    gap: 8,
  },
  retryButton: {
    backgroundColor: '#3B82F6',
  },
  homeButton: {
    backgroundColor: '#F3F4F6',
  },
  buttonText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#FFFFFF',
  },
  homeButtonText: {
    color: '#6B7280',
  },
  minimalContainer: {
    flexDirection: 'row',
    padding: 12,
    borderRadius: 8,
    marginVertical: 8,
  },
  minimalIcon: {
    marginRight: 8,
  },
  minimalContent: {
    flex: 1,
  },
  minimalMessage: {
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 2,
  },
  minimalAction: {
    fontSize: 12,
    color: '#6B7280',
  },
});