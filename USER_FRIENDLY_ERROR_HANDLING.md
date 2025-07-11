# User-Friendly Error Handling System

## Overview

A comprehensive error handling system that provides clear, actionable messages to users while maintaining detailed technical information for developers. The system categorizes errors, provides localized messages in Korean, and suggests specific actions users can take.

## Architecture

### 1. Error Categories

Errors are categorized to provide appropriate UI treatment and user guidance:

- **Authentication** - Login/session related errors
- **Authorization** - Permission/access errors
- **Validation** - Input/form validation errors
- **Network** - Connection/timeout errors
- **Server** - Backend processing errors
- **Business** - Business logic violations
- **Rate Limit** - Too many requests
- **Maintenance** - Service unavailable

### 2. Error Structure

```typescript
interface ErrorResponse {
  error: {
    code: string;              // Error code (e.g., "AUTH001")
    message: string;           // Technical message for developers
    user_message: string;      // User-friendly message in Korean
    action: string;            // Suggested action for users
    category: ErrorCategory;   // Error category
    status_code: number;       // HTTP status code
    request_id?: string;       // Request tracking ID
    data?: {                   // Additional error data
      user_errors?: Array<{    // User-friendly field errors
        field: string;
        message: string;
      }>;
      retry_after?: number;    // Seconds to wait (rate limiting)
    };
  };
}
```

### 3. Error Codes

Standardized error codes for consistent handling:

#### Authentication (AUTH)
- `AUTH001` - 로그인이 필요합니다
- `AUTH002` - 로그인 정보가 만료되었습니다  
- `AUTH003` - 잘못된 이메일 또는 비밀번호입니다
- `AUTH004` - 계정이 잠겼습니다
- `AUTH005` - 이메일 인증이 필요합니다

#### Authorization (PERM)
- `PERM001` - 접근 권한이 없습니다
- `PERM002` - 프리미엄 기능입니다
- `PERM003` - 연령 제한 콘텐츠입니다

#### Validation (VAL)
- `VAL001` - 입력 정보를 확인해주세요
- `VAL002` - 필수 정보가 누락되었습니다
- `VAL003` - 올바른 이메일 형식이 아닙니다
- `VAL004` - 비밀번호가 너무 약합니다

#### Network (NET)
- `NET001` - 인터넷 연결을 확인해주세요
- `NET002` - 서버에 연결할 수 없습니다
- `NET003` - 요청 시간이 초과되었습니다

#### Server (SRV)
- `SRV001` - 일시적인 오류가 발생했습니다
- `SRV002` - 서비스 점검 중입니다
- `SRV003` - 파일 업로드에 실패했습니다

#### Business Logic (BIZ)
- `BIZ001` - 이미 존재하는 계정입니다
- `BIZ002` - 퀘스트를 완료할 수 없습니다
- `BIZ003` - 포인트가 부족합니다
- `BIZ004` - 이미 참여한 활동입니다

#### Rate Limiting (RATE)
- `RATE001` - 너무 많은 요청을 보냈습니다
- `RATE002` - 로그인 시도 횟수를 초과했습니다

## Implementation

### Backend (Python/FastAPI)

#### 1. Error Messages Configuration
```python
# backend/app/core/error_messages.py
ERROR_MESSAGES = {
    "AUTH001": {
        "message": "로그인이 필요합니다",
        "category": ErrorCategory.AUTHENTICATION,
        "action": "다시 로그인해주세요"
    },
    # ... more error codes
}
```

#### 2. Custom Exception Classes
```python
# backend/app/core/exceptions.py
class BaseAPIException(HTTPException):
    def __init__(self, status_code, detail, error_code, user_message=None):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code
        
        # Get user-friendly message
        if error_code:
            message_info = get_user_message(error_code, user_message)
            self.user_message = message_info["message"]
            self.action = message_info["action"]
            self.category = message_info["category"]
```

#### 3. Error Handler Middleware
```python
# backend/app/middleware/error_handler.py
# Automatically adds user-friendly messages to all errors
# Handles validation errors with field-specific messages
# Includes request tracking and logging
```

### Frontend (React/TypeScript)

#### 1. Error Display Component
```tsx
// frontend/src/components/ErrorDisplay.tsx
<ErrorDisplay
  error={error}
  onRetry={() => refetch()}
  onGoHome={() => navigate('/')}
  minimal={false}
/>
```

Features:
- Category-based styling
- Retry functionality
- Rate limit countdown
- Field-specific validation errors
- Debug information in development

#### 2. Error Handling Utilities
```typescript
// frontend/src/utils/errorHandler.ts
const error = parseError(axiosError);
if (isAuthError(error)) {
  // Redirect to login
} else if (isNetworkError(error)) {
  // Show offline message
} else {
  // Show error display
}
```

### Mobile (React Native)

#### 1. Error Display Component
```tsx
// mobile/src/components/ErrorDisplay.tsx
<ErrorDisplay
  error={error}
  onRetry={handleRetry}
  minimal={true}
/>
```

#### 2. Error Alerts
```typescript
// mobile/src/utils/errorHandler.ts
showErrorAlert(error, () => {
  // Retry action
});
```

## Usage Examples

### Backend - Throwing Errors

```python
# Authentication error
raise AuthenticationError(error_code="AUTH003")

# Business logic error with context
raise BusinessLogicError(
    error_code="BIZ003",
    detail="Insufficient points for purchase"
)

# Validation error
raise ValidationError(
    error_code="VAL003",
    field="email"
)

# Rate limiting with retry info
raise RateLimitError(
    error_code="RATE001",
    retry_after=60
)
```

### Frontend - Handling Errors

```typescript
try {
  await api.post('/login', credentials);
} catch (error) {
  const appError = parseError(error);
  
  // Display error to user
  setError(appError);
  
  // Or show in toast
  toast.error(appError.user_message);
  
  // Log for debugging
  logError(error, 'Login');
}
```

### Mobile - Error Handling

```typescript
try {
  await loginUser(credentials);
} catch (error) {
  // Show alert with retry option
  showErrorAlert(error, async () => {
    await loginUser(credentials);
  });
  
  // Or display inline
  setError(parseError(error));
}
```

## Best Practices

### 1. Always Use Error Codes
```python
# Good
raise AuthenticationError(error_code="AUTH001")

# Bad
raise AuthenticationError(detail="Authentication required")
```

### 2. Provide Context for Dynamic Errors
```python
raise RateLimitError(
    error_code="RATE001",
    retry_after=60  # Dynamically set retry time
)
```

### 3. Handle Validation Errors Properly
```python
# Backend
errors = []
if not email_valid:
    errors.append({"field": "email", "type": "invalid"})
if errors:
    raise ValidationError(error_code="VAL001", data={"errors": errors})
```

### 4. Use Appropriate Categories
- Use `AUTHENTICATION` for login/session issues
- Use `AUTHORIZATION` for permission issues
- Use `VALIDATION` for user input errors
- Use `NETWORK` for connectivity issues
- Use `BUSINESS` for business rule violations

### 5. Log Errors Appropriately
```python
# Backend
logger.error("Critical error", exc_info=True)
logger.warning("Client error", error_code=exc.error_code)

# Frontend
logError(error, 'ComponentName');
```

## Testing

### Backend Tests
```python
def test_error_handling():
    response = client.post("/invalid")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH001"
    assert response.json()["error"]["user_message"] == "로그인이 필요합니다"
```

### Frontend Tests
```typescript
test('displays user-friendly error', () => {
  const error = new UserFriendlyError({
    code: 'AUTH001',
    user_message: '로그인이 필요합니다',
    action: '다시 로그인해주세요',
    category: ErrorCategory.AUTHENTICATION
  });
  
  render(<ErrorDisplay error={error} />);
  expect(screen.getByText('로그인이 필요합니다')).toBeInTheDocument();
});
```

## Localization

Error messages are currently in Korean. To add more languages:

1. Create language-specific error message files
2. Update `get_user_message()` to accept locale parameter
3. Pass user's locale from request context

## Monitoring

Errors are automatically logged with:
- Request ID for tracing
- User ID (if authenticated)
- Error code and category
- Response time
- Stack trace (for 500 errors)

Use these for:
- Error rate monitoring
- Common error analysis
- User experience improvement
- Performance tracking

## Future Enhancements

1. **Multi-language Support**
   - Add English and other language translations
   - Auto-detect user locale

2. **Error Recovery**
   - Automatic retry for transient errors
   - Offline queue for network errors
   - State recovery after errors

3. **Enhanced Analytics**
   - Error funnel analysis
   - User journey tracking
   - A/B testing error messages

4. **Smart Error Handling**
   - ML-based error prediction
   - Proactive error prevention
   - Context-aware suggestions