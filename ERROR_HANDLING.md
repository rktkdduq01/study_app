# Error Handling and Logging Guide

## 🛡️ Error Handling System

### Overview
The application implements a comprehensive error handling system with:
- Custom exception classes for different error scenarios
- Centralized error handling middleware
- Standardized error responses
- Detailed logging for debugging and monitoring

### Error Response Format

All API errors follow a consistent format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "status_code": 400,
    "request_id": "unique-request-id",
    "data": {
      // Additional error details
    }
  }
}
```

### Custom Exception Classes

#### Backend (Python)

```python
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
    ConflictError,
    BusinessLogicError,
    DatabaseError,
    ExternalServiceError,
    RateLimitError
)

# Example usage
if not user:
    raise NotFoundError("User", user_id)

if not has_permission:
    raise AuthorizationError("Insufficient permissions to access this resource")

if email_exists:
    raise ConflictError("User with this email already exists", field="email")
```

#### Frontend (TypeScript)

```typescript
import { parseError, getUserFriendlyMessage, isAuthError } from '@/utils/errorHandler';

try {
  const result = await api.get('/some-endpoint');
} catch (error) {
  const appError = parseError(error);
  
  if (isAuthError(appError)) {
    // Handle authentication error
    router.push('/login');
  }
  
  // Show user-friendly message
  toast.error(getUserFriendlyMessage(appError));
}
```

## 📊 Logging System

### Log Format

Logs are structured as JSON for easy parsing:

```json
{
  "timestamp": "2024-01-09T12:34:56.789Z",
  "level": "INFO",
  "logger": "app",
  "message": "User logged in successfully",
  "module": "auth",
  "function": "login",
  "line": 42,
  "request_id": "unique-request-id",
  "user_id": 123,
  "ip_address": "192.168.1.1",
  "extra_fields": {
    // Additional context
  }
}
```

### Log Levels

- **DEBUG**: Detailed information for debugging
- **INFO**: General informational messages
- **WARNING**: Warning messages for potentially harmful situations
- **ERROR**: Error messages for problems that occurred
- **CRITICAL**: Critical messages for severe problems

### Logging Examples

#### Backend

```python
from app.core.logger import logger

# Simple logging
logger.info("User logged in", user_id=user.id, email=user.email)

# Log with context
logger.error(
    "Payment failed",
    user_id=user.id,
    amount=100.00,
    error_code="PAYMENT_DECLINED",
    exc_info=True  # Include exception traceback
)

# Log business events
logger.log_business_event(
    event_type="purchase_completed",
    description="User completed purchase",
    user_id=user.id,
    data={"item_id": item.id, "amount": 100.00}
)

# Log performance metrics
logger.log_performance(
    operation="database_query",
    duration=0.123,
    metadata={"query": "SELECT * FROM users", "rows": 100}
)
```

#### Using Decorators

```python
from app.core.logger import log_function_call

@log_function_call(log_args=True, log_result=True)
async def process_payment(user_id: int, amount: float):
    # Function will be automatically logged
    return {"success": True, "transaction_id": "123"}
```

### Log Files

- **app.log**: All application logs
- **error.log**: Error-level logs only
- **security.log**: Security-related events

## 🚨 Error Handling Best Practices

### 1. Use Specific Exceptions

```python
# ❌ Bad
raise Exception("Something went wrong")

# ✅ Good
raise BusinessLogicError(
    "Cannot cancel order in current state",
    error_code="ORDER_NOT_CANCELLABLE"
)
```

### 2. Provide Context

```python
# ❌ Bad
logger.error("Failed to process")

# ✅ Good
logger.error(
    "Failed to process order",
    order_id=order.id,
    user_id=user.id,
    error_type="payment_failed",
    payment_method="credit_card"
)
```

### 3. Handle Errors at the Right Level

```typescript
// Component level
const { handleError } = useErrorHandler({
  onAuthError: () => router.push('/login'),
  onNetworkError: () => setOfflineMode(true)
});

try {
  await saveData();
} catch (error) {
  handleError(error, 'SaveData');
}
```

### 4. Use Error Boundaries

```typescript
// Wrap components that might throw errors
<ErrorBoundary fallback={<ErrorFallback />}>
  <RiskyComponent />
</ErrorBoundary>
```

## 🔍 Monitoring and Debugging

### Request Tracking

Every request gets a unique ID for tracing:

```bash
curl -i http://localhost:8000/api/v1/users

# Response headers
X-Request-ID: 550e8400-e29b-41d4-a716-446655440000
X-Response-Time: 123ms
```

### Debugging Tips

1. **Check Request ID**: Use the request ID to find all related logs
2. **Enable Debug Mode**: Set `DEBUG=True` in development
3. **Check Multiple Logs**: 
   - Application logs for general errors
   - Security logs for auth issues
   - Performance logs for slow requests

### Log Analysis

```bash
# Find all logs for a specific request
grep "request_id.*550e8400" logs/app.log

# Find all errors for a user
grep "user_id.*123.*ERROR" logs/app.log

# Find slow requests
grep "duration_ms.*[0-9]\{4,\}" logs/app.log
```

## 🧪 Testing Error Handling

Run the test script to verify error handling:

```bash
cd backend
python test_error_handling.py
```

This will test:
- All error types
- Validation errors
- Rate limiting
- Logging functionality

## 📈 Performance Monitoring

The system automatically logs:
- Request duration
- Memory usage (if psutil is installed)
- Slow queries
- External API calls

Performance headers are added to all responses:
```
X-Response-Time: 123ms
```

## 🔐 Security Logging

Security events are automatically logged:
- Login attempts (success/failure)
- Permission denials
- Suspicious activities
- Rate limit violations

These logs are stored separately in `logs/security.log` for audit purposes.