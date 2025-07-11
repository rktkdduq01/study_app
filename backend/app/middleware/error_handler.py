"""
Global error handler middleware.
"""
import time
import uuid
from typing import Callable, Optional
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError

from app.core.logger import logger
from app.core.exceptions import (
    BaseAPIException,
    ValidationError as CustomValidationError,
    DatabaseError,
    create_error_response
)
from app.core.error_messages import get_user_message, get_field_error_message, ErrorCategory
from app.utils.security_logger import get_client_ip


async def error_handler_middleware(request: Request, call_next: Callable) -> Response:
    """Global error handler middleware"""
    # Generate request ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Get user info if available
    user_id = None
    if hasattr(request.state, "user") and request.state.user:
        user_id = request.state.user.id
    
    # Get client IP
    client_ip = get_client_ip(request)
    
    # Start timer
    start_time = time.time()
    
    try:
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log successful request
        logger.log_request(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration=duration,
            request_id=request_id,
            user_id=user_id,
            ip_address=client_ip
        )
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response
        
    except Exception as exc:
        # Calculate duration
        duration = time.time() - start_time
        
        # Handle the exception
        response = await handle_exception(exc, request, request_id, duration)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response


async def handle_exception(
    exc: Exception,
    request: Request,
    request_id: str,
    duration: float
) -> JSONResponse:
    """Handle different types of exceptions"""
    
    # Get user info and client IP
    user_id = None
    if hasattr(request.state, "user") and request.state.user:
        user_id = request.state.user.id
    
    client_ip = get_client_ip(request)
    
    # Default error response
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_response = {
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "status_code": status_code,
            "request_id": request_id,
            "data": {}
        }
    }
    
    # Handle custom API exceptions
    if isinstance(exc, BaseAPIException):
        status_code = exc.status_code
        error_response = create_error_response(exc)
        error_response["error"]["request_id"] = request_id
        
        # Log based on severity
        if status_code >= 500:
            logger.error(
                f"Server error: {exc.detail}",
                request_id=request_id,
                user_id=user_id,
                ip_address=client_ip,
                path=request.url.path,
                method=request.method,
                status_code=status_code,
                error_code=exc.error_code,
                duration_ms=round(duration * 1000, 2)
            )
        else:
            logger.warning(
                f"Client error: {exc.detail}",
                request_id=request_id,
                user_id=user_id,
                ip_address=client_ip,
                path=request.url.path,
                method=request.method,
                status_code=status_code,
                error_code=exc.error_code,
                duration_ms=round(duration * 1000, 2)
            )
    
    # Handle FastAPI/Starlette HTTP exceptions
    elif isinstance(exc, (HTTPException, StarletteHTTPException)):
        status_code = exc.status_code
        
        # Map common HTTP errors to user-friendly messages
        if status_code == 401:
            user_msg = get_user_message("AUTH001")
        elif status_code == 403:
            user_msg = get_user_message("PERM001")
        elif status_code == 404:
            user_msg = get_user_message("SRV001", "요청한 페이지를 찾을 수 없습니다")
        elif status_code == 429:
            user_msg = get_user_message("RATE001")
        else:
            user_msg = get_user_message("SRV001")
        
        error_response = {
            "error": {
                "code": "HTTP_ERROR",
                "message": exc.detail,
                "user_message": user_msg["message"],
                "action": user_msg["action"],
                "category": user_msg["category"],
                "status_code": status_code,
                "request_id": request_id,
                "data": {}
            }
        }
        
        logger.warning(
            f"HTTP exception: {exc.detail}",
            request_id=request_id,
            user_id=user_id,
            ip_address=client_ip,
            path=request.url.path,
            method=request.method,
            status_code=status_code,
            duration_ms=round(duration * 1000, 2)
        )
    
    # Handle Pydantic validation errors
    elif isinstance(exc, RequestValidationError):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        errors = []
        user_friendly_errors = []
        
        for error in exc.errors():
            field_name = ".".join(str(loc) for loc in error["loc"])
            error_type = error["type"]
            
            # Map validation error types to user-friendly messages
            if error_type == "value_error.missing":
                user_msg = get_field_error_message(field_name, "required")
            elif error_type == "value_error.email":
                user_msg = get_field_error_message(field_name, "invalid")
            elif error_type == "value_error.str.regex":
                user_msg = get_field_error_message(field_name, "invalid")
            elif "min_length" in error_type:
                user_msg = get_field_error_message(field_name, "too_short")
            elif "max_length" in error_type:
                user_msg = get_field_error_message(field_name, "too_long")
            else:
                user_msg = get_field_error_message(field_name, "invalid")
            
            errors.append({
                "field": field_name,
                "message": error["msg"],
                "type": error["type"]
            })
            
            user_friendly_errors.append({
                "field": field_name,
                "message": user_msg
            })
        
        user_msg = get_user_message("VAL001")
        error_response = {
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "user_message": user_msg["message"],
                "action": user_msg["action"],
                "category": user_msg["category"],
                "status_code": status_code,
                "request_id": request_id,
                "data": {
                    "errors": errors,
                    "user_errors": user_friendly_errors
                }
            }
        }
        
        logger.warning(
            "Request validation error",
            request_id=request_id,
            user_id=user_id,
            ip_address=client_ip,
            path=request.url.path,
            method=request.method,
            validation_errors=errors,
            duration_ms=round(duration * 1000, 2)
        )
    
    # Handle Pydantic validation errors (model validation)
    elif isinstance(exc, ValidationError):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        errors = []
        
        for error in exc.errors():
            field_name = ".".join(str(loc) for loc in error["loc"])
            errors.append({
                "field": field_name,
                "message": error["msg"],
                "type": error["type"]
            })
        
        error_response = {
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Data validation failed",
                "status_code": status_code,
                "request_id": request_id,
                "data": {"errors": errors}
            }
        }
        
        logger.warning(
            "Data validation error",
            request_id=request_id,
            user_id=user_id,
            ip_address=client_ip,
            path=request.url.path,
            method=request.method,
            validation_errors=errors,
            duration_ms=round(duration * 1000, 2)
        )
    
    # Handle database errors
    elif isinstance(exc, IntegrityError):
        status_code = status.HTTP_409_CONFLICT
        
        # Check for common integrity errors
        error_str = str(exc).lower()
        if "duplicate" in error_str or "unique" in error_str:
            user_msg = get_user_message("BIZ001")
        else:
            user_msg = get_user_message("SRV001")
        
        error_response = {
            "error": {
                "code": "DATABASE_INTEGRITY_ERROR",
                "message": "Database constraint violation",
                "user_message": user_msg["message"],
                "action": user_msg["action"],
                "category": user_msg["category"],
                "status_code": status_code,
                "request_id": request_id,
                "data": {}
            }
        }
        
        logger.error(
            "Database integrity error",
            request_id=request_id,
            user_id=user_id,
            ip_address=client_ip,
            path=request.url.path,
            method=request.method,
            error_details=str(exc),
            duration_ms=round(duration * 1000, 2)
        )
    
    elif isinstance(exc, SQLAlchemyError):
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        user_msg = get_user_message("SRV001")
        
        error_response = {
            "error": {
                "code": "DATABASE_ERROR",
                "message": "Database operation failed",
                "user_message": user_msg["message"],
                "action": user_msg["action"],
                "category": user_msg["category"],
                "status_code": status_code,
                "request_id": request_id,
                "data": {}
            }
        }
        
        logger.error(
            "Database error",
            request_id=request_id,
            user_id=user_id,
            ip_address=client_ip,
            path=request.url.path,
            method=request.method,
            error_type=type(exc).__name__,
            error_details=str(exc),
            duration_ms=round(duration * 1000, 2)
        )
    
    # Handle all other exceptions
    else:
        user_msg = get_user_message("SRV001")
        error_response["error"].update({
            "user_message": user_msg["message"],
            "action": user_msg["action"],
            "category": user_msg["category"]
        })
        
        logger.critical(
            f"Unhandled exception: {type(exc).__name__}",
            request_id=request_id,
            user_id=user_id,
            ip_address=client_ip,
            path=request.url.path,
            method=request.method,
            error_type=type(exc).__name__,
            error_details=str(exc),
            duration_ms=round(duration * 1000, 2),
            exc_info=True
        )
    
    # Return JSON response
    return JSONResponse(
        status_code=status_code,
        content=error_response
    )


def create_exception_handlers(app):
    """Register exception handlers with the FastAPI app"""
    
    @app.exception_handler(BaseAPIException)
    async def custom_exception_handler(request: Request, exc: BaseAPIException):
        """Handle custom API exceptions"""
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        error_response = create_error_response(exc)
        error_response["error"]["request_id"] = request_id
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response,
            headers={"X-Request-ID": request_id}
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle request validation errors"""
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        
        errors = []
        for error in exc.errors():
            field_name = ".".join(str(loc) for loc in error["loc"])
            errors.append({
                "field": field_name,
                "message": error["msg"],
                "type": error["type"]
            })
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                    "request_id": request_id,
                    "data": {"errors": errors}
                }
            },
            headers={"X-Request-ID": request_id}
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions"""
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": "HTTP_ERROR",
                    "message": exc.detail,
                    "status_code": exc.status_code,
                    "request_id": request_id,
                    "data": {}
                }
            },
            headers={"X-Request-ID": request_id}
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle all unhandled exceptions"""
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        
        logger.critical(
            f"Unhandled exception: {type(exc).__name__}",
            request_id=request_id,
            path=request.url.path,
            method=request.method,
            error_type=type(exc).__name__,
            error_details=str(exc),
            exc_info=True
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred",
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "request_id": request_id,
                    "data": {}
                }
            },
            headers={"X-Request-ID": request_id}
        )