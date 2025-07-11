"""
Test endpoints for error handling and logging.
Only available in DEBUG mode.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.api import deps
from app.core.config import settings
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
from app.core.logger import logger, log_function_call

router = APIRouter()

# Only enable these endpoints in debug mode
if not settings.DEBUG:
    router = APIRouter()  # Empty router in production


@router.get("/test-success")
async def test_success():
    """Test successful response"""
    logger.info("Test success endpoint called")
    return {"message": "Success", "status": "ok"}


@router.get("/test-authentication-error")
async def test_authentication_error():
    """Test authentication error"""
    logger.warning("Testing authentication error")
    raise AuthenticationError("Invalid credentials provided")


@router.get("/test-authorization-error")
async def test_authorization_error():
    """Test authorization error"""
    logger.warning("Testing authorization error")
    raise AuthorizationError("You don't have permission to access this resource")


@router.get("/test-not-found")
async def test_not_found(resource_id: int = Query(...)):
    """Test not found error"""
    logger.warning(f"Testing not found error for ID: {resource_id}")
    raise NotFoundError("User", resource_id)


@router.get("/test-validation-error")
async def test_validation_error():
    """Test validation error"""
    logger.warning("Testing validation error")
    raise ValidationError("Email format is invalid", field="email")


@router.get("/test-conflict-error")
async def test_conflict_error():
    """Test conflict error"""
    logger.warning("Testing conflict error")
    raise ConflictError("User with this email already exists", field="email")


@router.get("/test-business-logic-error")
async def test_business_logic_error():
    """Test business logic error"""
    logger.warning("Testing business logic error")
    raise BusinessLogicError(
        "Cannot perform this action in current state",
        error_code="INVALID_STATE_TRANSITION"
    )


@router.get("/test-database-error")
async def test_database_error():
    """Test database error"""
    logger.error("Testing database error")
    raise DatabaseError("Connection to database lost")


@router.get("/test-external-service-error")
async def test_external_service_error():
    """Test external service error"""
    logger.error("Testing external service error")
    raise ExternalServiceError("OpenAI API", "Rate limit exceeded")


@router.get("/test-rate-limit-error")
async def test_rate_limit_error():
    """Test rate limit error"""
    logger.warning("Testing rate limit error")
    raise RateLimitError("Too many requests", retry_after=60)


@router.get("/test-unhandled-error")
async def test_unhandled_error():
    """Test unhandled exception"""
    logger.error("Testing unhandled error")
    # This will cause a division by zero error
    result = 1 / 0
    return {"result": result}


@router.get("/test-logging")
@log_function_call(log_args=True, log_result=True)
async def test_logging(
    param1: str = Query(..., description="First parameter"),
    param2: Optional[int] = Query(None, description="Second parameter")
):
    """Test logging decorator"""
    logger.info("Inside test logging function", param1=param1, param2=param2)
    
    # Test different log levels
    logger.debug("Debug message", extra_data={"debug": True})
    logger.info("Info message", extra_data={"info": True})
    logger.warning("Warning message", extra_data={"warning": True})
    
    # Test business event logging
    logger.log_business_event(
        event_type="test_event",
        description="Test business event occurred",
        data={"param1": param1, "param2": param2}
    )
    
    return {"param1": param1, "param2": param2, "logged": True}


@router.get("/test-slow-endpoint")
async def test_slow_endpoint(delay: float = Query(2.0, description="Delay in seconds")):
    """Test slow endpoint for performance logging"""
    import asyncio
    logger.info(f"Starting slow operation with {delay}s delay")
    await asyncio.sleep(delay)
    return {"message": f"Operation completed after {delay} seconds"}


@router.post("/test-audit-logging")
async def test_audit_logging(
    data: dict,
    current_user: deps.User = Depends(deps.get_current_active_user)
):
    """Test audit logging for sensitive operations"""
    logger.info(
        "Sensitive operation performed",
        user_id=current_user.id,
        operation="test_audit",
        data=data
    )
    return {"message": "Audit logged", "user": current_user.username}