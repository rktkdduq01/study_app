# Production Logging System Documentation

## Overview
This document describes the centralized logging system implemented across all applications (backend, frontend, and mobile) to replace console.log/error statements in production.

## Implementation Details

### 1. Backend Logging

#### Configuration
- **Location**: `/backend/app/utils/logger.py` and `/backend/app/core/logging_config.py`
- **Log Files**:
  - `logs/app.log` - General application logs
  - `logs/security.log` - Security-specific events
  - `logs/error.log` - Error logs

#### Usage
```python
from app.utils.logger import get_logger, api_logger, service_logger

# Create a logger for your module
logger = get_logger("app.my_module")

# Log messages
logger.debug("Debug message", key="value")
logger.info("Info message", user_id=123)
logger.warning("Warning message", context={"key": "value"})
logger.error("Error message", error=exception, request_id="abc123")
```

#### Decorators
```python
from app.utils.logger import log_api_request, log_service_call

@log_api_request
async def my_api_endpoint(request: Request):
    # Automatically logs API requests
    pass

@log_service_call("MyService")
async def my_service_method():
    # Automatically logs service method calls
    pass
```

### 2. Frontend Logging

#### Configuration
- **Location**: `/frontend/src/utils/logger.ts`
- **Features**:
  - Environment-aware (only logs to console in development)
  - Buffered logging for batch sending
  - Global error handlers
  - Automatic log flushing on page unload

#### Usage
```typescript
import { logger, logDebug, logInfo, logWarn, logError } from '@/utils/logger';

// Log messages
logDebug('Debug message', { userId: 123 });
logInfo('User action', { action: 'click', target: 'button' });
logWarn('Deprecation warning', { feature: 'oldAPI' });
logError('Operation failed', error, { context: 'data' });

// Direct logger usage
logger.info('Message', { key: 'value' });
logger.error('Error occurred', error);

// Get recent logs for debugging
const recentLogs = logger.getRecentLogs();
```

### 3. Mobile Logging

#### Configuration
- **Location**: `/mobile/src/utils/logger.ts`
- **Features**:
  - React Native specific implementation
  - Device information collection
  - AsyncStorage persistence
  - Offline support
  - Event and screen tracking

#### Usage
```typescript
import { logger, logDebug, logInfo, logWarn, logError, logTrack, logScreen } from '@/utils/logger';

// Log messages
logDebug('Debug message', { data: 'value' });
logInfo('User action', { action: 'tap' });
logWarn('Low memory warning');
logError('Network request failed', error);

// Track events
logTrack('button_clicked', { button: 'submit' });
logScreen('ProfileScreen', { userId: 123 });

// Configure logger
logger.configure({
  enableInProduction: true,
  logToServer: true,
  serverEndpoint: 'https://api.example.com/logs'
});

// Get logs for debugging
const logs = await logger.getRecentLogs();
```

## Production Configuration

### Environment Variables

#### Backend
```bash
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
ENVIRONMENT=production
```

#### Frontend
```bash
NODE_ENV=production
REACT_APP_LOG_ENDPOINT=https://api.example.com/logs
```

#### Mobile
```bash
LOG_SERVER_ENDPOINT=https://api.example.com/logs
```

### ESLint Configuration

To enforce no console usage in production:

#### Frontend/Mobile
```json
// .eslintrc.production.json
{
  "extends": ["./.eslintrc.json"],
  "rules": {
    "no-console": ["error", { "allow": ["warn", "error"] }],
    "no-debugger": "error",
    "no-alert": "error"
  }
}
```

Run production lint:
```bash
eslint --config .eslintrc.production.json src/
```

## Log Formats

### Backend (Structured JSON)
```json
{
  "timestamp": "2024-01-20T10:15:30.123Z",
  "level": "INFO",
  "message": "User login successful",
  "logger": "app.api.auth",
  "environment": "production",
  "context": {
    "user_id": 123,
    "ip": "192.168.1.1"
  }
}
```

### Frontend/Mobile
```json
{
  "level": "info",
  "message": "Button clicked",
  "timestamp": "2024-01-20T10:15:30.123Z",
  "context": {
    "component": "Header",
    "action": "logout"
  },
  "platform": "ios",  // Mobile only
  "deviceId": "abc123",  // Mobile only
  "appVersion": "1.0.0"  // Mobile only
}
```

## Log Rotation

### Backend
- Configured in `logging_config.py`
- Max file size: 10MB
- Backup count: 5-10 files
- Automatic rotation when size limit reached

### Frontend/Mobile
- Buffer size limits prevent memory issues
- Logs are sent to server and cleared periodically

## Security Considerations

1. **No Sensitive Data**: Never log passwords, tokens, or PII
2. **Sanitization**: Sanitize user input before logging
3. **Access Control**: Restrict access to log files
4. **Encryption**: Use HTTPS for log transmission
5. **Retention**: Define log retention policies

## Monitoring and Alerts

### Log Aggregation
Consider using:
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Splunk
- Datadog
- New Relic

### Alert Examples
```python
# Backend
if error_count > threshold:
    logger.critical("High error rate detected", 
                   error_count=error_count,
                   threshold=threshold)
```

## Migration Guide

### Finding Console Statements
```bash
# Backend
grep -r "print(" --include="*.py" app/

# Frontend/Mobile
grep -r "console\." --include="*.ts" --include="*.tsx" src/
```

### Replacement Examples

#### Before
```javascript
console.log('User logged in', userId);
console.error('Login failed:', error);
```

#### After
```javascript
logger.info('User logged in', { userId });
logger.error('Login failed', error);
```

## Best Practices

1. **Use Appropriate Log Levels**:
   - DEBUG: Detailed information for debugging
   - INFO: General information about app flow
   - WARN: Warning messages for potential issues
   - ERROR: Error messages for failures

2. **Structure Your Logs**:
   - Include context (user ID, request ID, etc.)
   - Use consistent message formats
   - Add timestamps and source information

3. **Performance**:
   - Don't log in tight loops
   - Use debug level for verbose logging
   - Consider log sampling for high-traffic endpoints

4. **Testing**:
   ```bash
   # Test log output
   LOG_LEVEL=DEBUG python app/main.py
   
   # Verify no console statements
   npm run lint:production
   ```

## Troubleshooting

### Logs Not Appearing
1. Check log level configuration
2. Verify file permissions for log directory
3. Check if logger is properly imported

### Performance Issues
1. Reduce log verbosity in production
2. Implement log sampling
3. Use async logging where possible

### Missing Logs
1. Check log rotation settings
2. Verify disk space
3. Check network connectivity (for remote logging)