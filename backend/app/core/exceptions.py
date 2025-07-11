"""
Custom exception classes for the application.
"""
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from app.core.error_messages import get_user_message, ErrorCategory


class BaseAPIException(HTTPException):
    """Base exception class for API errors"""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code or self.__class__.__name__
        self.data = data or {}
        
        # Get user-friendly message
        if error_code:
            message_info = get_user_message(error_code, user_message)
            self.user_message = message_info["message"]
            self.action = message_info["action"]
            self.category = message_info["category"]
        else:
            self.user_message = user_message or detail
            self.action = "다시 시도해주세요"
            self.category = ErrorCategory.SERVER


class AuthenticationError(BaseAPIException):
    """Raised when authentication fails"""
    
    def __init__(self, detail: str = "Authentication failed", error_code: str = "AUTH001"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code=error_code,
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthorizationError(BaseAPIException):
    """Raised when user lacks required permissions"""
    
    def __init__(self, detail: str = "Insufficient permissions", error_code: str = "PERM001", required_role: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code=error_code,
            data={"required_role": required_role} if required_role else {}
        )


class NotFoundError(BaseAPIException):
    """Raised when requested resource is not found"""
    
    def __init__(self, resource: str, resource_id: Any = None):
        detail = f"{resource} not found"
        if resource_id:
            detail = f"{resource} with id {resource_id} not found"
        
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="RESOURCE_NOT_FOUND",
            data={"resource": resource, "resource_id": str(resource_id) if resource_id else None}
        )


class ValidationError(BaseAPIException):
    """Raised when input validation fails"""
    
    def __init__(self, detail: str, field: Optional[str] = None, error_code: str = "VAL001"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code=error_code,
            data={"field": field} if field else {}
        )


class ConflictError(BaseAPIException):
    """Raised when there's a conflict with existing data"""
    
    def __init__(self, detail: str, field: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code="CONFLICT_ERROR",
            data={"field": field} if field else {}
        )


class RateLimitError(BaseAPIException):
    """Raised when rate limit is exceeded"""
    
    def __init__(self, detail: str = "Rate limit exceeded", retry_after: Optional[int] = None, error_code: str = "RATE001"):
        headers = {}
        if retry_after:
            headers["Retry-After"] = str(retry_after)
        
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            error_code=error_code,
            headers=headers,
            data={"retry_after": retry_after} if retry_after else {}
        )


class BusinessLogicError(BaseAPIException):
    """Raised when business logic validation fails"""
    
    def __init__(self, detail: str, error_code: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code=error_code or "BUSINESS_LOGIC_ERROR"
        )


class ExternalServiceError(BaseAPIException):
    """Raised when external service call fails"""
    
    def __init__(self, service: str, detail: str = "External service error"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{service}: {detail}",
            error_code="EXTERNAL_SERVICE_ERROR",
            data={"service": service}
        )


class DatabaseError(BaseAPIException):
    """Raised when database operation fails"""
    
    def __init__(self, detail: str = "Database operation failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="DATABASE_ERROR"
        )


class TokenError(BaseAPIException):
    """Raised when token validation fails"""
    
    def __init__(self, detail: str = "Invalid or expired token"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="TOKEN_ERROR",
            headers={"WWW-Authenticate": "Bearer"}
        )


class TokenExpiredError(TokenError):
    """Raised when token has expired"""
    
    def __init__(self, token_type: str = "access"):
        super().__init__(
            detail=f"{token_type.capitalize()} token has expired",
        )
        self.error_code = "AUTH002"


class TokenBlacklistedError(TokenError):
    """Raised when token is blacklisted"""
    
    def __init__(self, token_type: str = "access"):
        super().__init__(
            detail=f"{token_type.capitalize()} token has been revoked",
        )
        self.error_code = "TOKEN_BLACKLISTED"


class InvalidTokenTypeError(TokenError):
    """Raised when token type doesn't match expected type"""
    
    def __init__(self, expected: str, actual: str):
        super().__init__(
            detail=f"Invalid token type. Expected '{expected}', got '{actual}'",
        )
        self.error_code = "INVALID_TOKEN_TYPE"


class EncryptionError(BaseAPIException):
    """Raised when encryption fails"""
    
    def __init__(self, detail: str = "Encryption operation failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="ENCRYPTION_ERROR"
        )


class DecryptionError(BaseAPIException):
    """Raised when decryption fails"""
    
    def __init__(self, detail: str = "Decryption operation failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="DECRYPTION_ERROR"
        )


class FileOperationError(BaseAPIException):
    """Raised when file operation fails"""
    
    def __init__(self, detail: str, operation: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="FILE_OPERATION_ERROR",
            data={"operation": operation}
        )


class WebSocketError(BaseAPIException):
    """Raised when WebSocket operation fails"""
    
    def __init__(self, detail: str, connection_id: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="WEBSOCKET_ERROR",
            data={"connection_id": connection_id} if connection_id else {}
        )


# Backward compatibility aliases
BadRequestException = BusinessLogicError
UnauthorizedException = AuthenticationError
ForbiddenException = AuthorizationError
NotFoundException = NotFoundError
ConflictException = ConflictError
UnprocessableEntityException = ValidationError
InternalServerException = DatabaseError


# Error code to exception mapping for easy lookup
ERROR_CODE_MAP = {
    "AUTHENTICATION_ERROR": AuthenticationError,
    "AUTHORIZATION_ERROR": AuthorizationError,
    "RESOURCE_NOT_FOUND": NotFoundError,
    "VALIDATION_ERROR": ValidationError,
    "CONFLICT_ERROR": ConflictError,
    "RATE_LIMIT_EXCEEDED": RateLimitError,
    "BUSINESS_LOGIC_ERROR": BusinessLogicError,
    "EXTERNAL_SERVICE_ERROR": ExternalServiceError,
    "DATABASE_ERROR": DatabaseError,
    "TOKEN_ERROR": TokenError,
    "FILE_OPERATION_ERROR": FileOperationError,
    "WEBSOCKET_ERROR": WebSocketError,
}


def create_error_response(exception: BaseAPIException) -> Dict[str, Any]:
    """Create standardized error response"""
    return {
        "error": {
            "code": exception.error_code,
            "message": exception.detail,
            "user_message": getattr(exception, 'user_message', exception.detail),
            "action": getattr(exception, 'action', 'Please try again'),
            "category": getattr(exception, 'category', ErrorCategory.SERVER),
            "status_code": exception.status_code,
            "data": exception.data
        }
    }