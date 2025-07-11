"""
Tests for error handling and logging
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import json

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
from app.core.logger import logger


class TestCustomExceptions:
    """Test custom exception classes"""
    
    def test_authentication_error(self):
        """Test AuthenticationError exception"""
        error = AuthenticationError("Invalid credentials")
        assert error.status_code == 401
        assert error.error_code == "AUTHENTICATION_ERROR"
        assert error.message == "Invalid credentials"
        assert error.data is None
        
        # With additional data
        error = AuthenticationError("Token expired", data={"token_type": "access"})
        assert error.data == {"token_type": "access"}
    
    def test_authorization_error(self):
        """Test AuthorizationError exception"""
        error = AuthorizationError("Insufficient permissions")
        assert error.status_code == 403
        assert error.error_code == "AUTHORIZATION_ERROR"
        assert error.message == "Insufficient permissions"
    
    def test_not_found_error(self):
        """Test NotFoundError exception"""
        error = NotFoundError("User", 123)
        assert error.status_code == 404
        assert error.error_code == "NOT_FOUND"
        assert "User" in error.message
        assert "123" in error.message
    
    def test_validation_error(self):
        """Test ValidationError exception"""
        error = ValidationError("Invalid email format", field="email")
        assert error.status_code == 422
        assert error.error_code == "VALIDATION_ERROR"
        assert error.message == "Invalid email format"
        assert error.data == {"field": "email"}
    
    def test_conflict_error(self):
        """Test ConflictError exception"""
        error = ConflictError("Email already exists", field="email")
        assert error.status_code == 409
        assert error.error_code == "CONFLICT"
        assert error.message == "Email already exists"
        assert error.data == {"field": "email"}
    
    def test_business_logic_error(self):
        """Test BusinessLogicError exception"""
        error = BusinessLogicError(
            "Cannot cancel completed order",
            error_code="ORDER_NOT_CANCELLABLE"
        )
        assert error.status_code == 400
        assert error.error_code == "ORDER_NOT_CANCELLABLE"
        assert error.message == "Cannot cancel completed order"
    
    def test_database_error(self):
        """Test DatabaseError exception"""
        error = DatabaseError("Connection failed")
        assert error.status_code == 500
        assert error.error_code == "DATABASE_ERROR"
        assert error.message == "Connection failed"
    
    def test_external_service_error(self):
        """Test ExternalServiceError exception"""
        error = ExternalServiceError("Payment gateway timeout", service="stripe")
        assert error.status_code == 503
        assert error.error_code == "EXTERNAL_SERVICE_ERROR"
        assert error.message == "Payment gateway timeout"
        assert error.data == {"service": "stripe"}
    
    def test_rate_limit_error(self):
        """Test RateLimitError exception"""
        error = RateLimitError(retry_after=60)
        assert error.status_code == 429
        assert error.error_code == "RATE_LIMIT_ERROR"
        assert "Too many requests" in error.message
        assert error.data == {"retry_after": 60}


class TestErrorEndpoints:
    """Test error handling endpoints"""
    
    def test_success_endpoint(self, client: TestClient):
        """Test successful endpoint"""
        response = client.get("/api/v1/test/test-success")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "X-Request-ID" in response.headers
    
    def test_authentication_error_endpoint(self, client: TestClient):
        """Test authentication error endpoint"""
        response = client.get("/api/v1/test/test-authentication-error")
        assert response.status_code == 401
        
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "AUTHENTICATION_ERROR"
        assert data["error"]["status_code"] == 401
        assert "request_id" in data["error"]
    
    def test_authorization_error_endpoint(self, client: TestClient):
        """Test authorization error endpoint"""
        response = client.get("/api/v1/test/test-authorization-error")
        assert response.status_code == 403
        
        data = response.json()
        assert data["error"]["code"] == "AUTHORIZATION_ERROR"
    
    def test_not_found_error_endpoint(self, client: TestClient):
        """Test not found error endpoint"""
        response = client.get("/api/v1/test/test-not-found?resource_id=123")
        assert response.status_code == 404
        
        data = response.json()
        assert data["error"]["code"] == "NOT_FOUND"
        assert "123" in data["error"]["message"]
    
    def test_validation_error_endpoint(self, client: TestClient):
        """Test validation error endpoint"""
        response = client.get("/api/v1/test/test-validation-error")
        assert response.status_code == 422
        
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert data["error"]["data"]["field"] == "email"
    
    def test_conflict_error_endpoint(self, client: TestClient):
        """Test conflict error endpoint"""
        response = client.get("/api/v1/test/test-conflict-error")
        assert response.status_code == 409
        
        data = response.json()
        assert data["error"]["code"] == "CONFLICT"
    
    def test_business_logic_error_endpoint(self, client: TestClient):
        """Test business logic error endpoint"""
        response = client.get("/api/v1/test/test-business-logic-error")
        assert response.status_code == 400
        
        data = response.json()
        assert data["error"]["code"] == "INVALID_OPERATION"
    
    def test_database_error_endpoint(self, client: TestClient):
        """Test database error endpoint"""
        response = client.get("/api/v1/test/test-database-error")
        assert response.status_code == 500
        
        data = response.json()
        assert data["error"]["code"] == "DATABASE_ERROR"
    
    def test_external_service_error_endpoint(self, client: TestClient):
        """Test external service error endpoint"""
        response = client.get("/api/v1/test/test-external-service-error")
        assert response.status_code == 503
        
        data = response.json()
        assert data["error"]["code"] == "EXTERNAL_SERVICE_ERROR"
        assert data["error"]["data"]["service"] == "payment_gateway"
    
    def test_rate_limit_error_endpoint(self, client: TestClient):
        """Test rate limit error endpoint"""
        response = client.get("/api/v1/test/test-rate-limit-error")
        assert response.status_code == 429
        
        data = response.json()
        assert data["error"]["code"] == "RATE_LIMIT_ERROR"
        assert data["error"]["data"]["retry_after"] == 60
    
    def test_unhandled_error_endpoint(self, client: TestClient):
        """Test unhandled error endpoint"""
        response = client.get("/api/v1/test/test-unhandled-error")
        assert response.status_code == 500
        
        data = response.json()
        assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
        assert data["error"]["message"] == "An unexpected error occurred"


class TestLogging:
    """Test logging functionality"""
    
    def test_logging_endpoint(self, client: TestClient):
        """Test logging with parameters"""
        response = client.get("/api/v1/test/test-logging?param1=test&param2=123")
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Logging test completed"
        assert data["params"]["param1"] == "test"
        assert data["params"]["param2"] == "123"
    
    def test_slow_endpoint(self, client: TestClient):
        """Test slow endpoint logging"""
        response = client.get("/api/v1/test/test-slow-endpoint?delay=0.1")
        assert response.status_code == 200
        
        # Response time header should be present and > 100ms
        assert "X-Response-Time" in response.headers
        response_time = float(response.headers["X-Response-Time"].replace("ms", ""))
        assert response_time >= 100


class TestRequestHeaders:
    """Test request/response headers"""
    
    def test_request_id_header(self, client: TestClient):
        """Test that request ID is generated"""
        response = client.get("/api/v1/test/test-success")
        
        assert "X-Request-ID" in response.headers
        request_id = response.headers["X-Request-ID"]
        
        # UUID format check
        assert len(request_id) == 36
        assert request_id.count("-") == 4
    
    def test_response_time_header(self, client: TestClient):
        """Test that response time is measured"""
        response = client.get("/api/v1/test/test-success")
        
        assert "X-Response-Time" in response.headers
        response_time = response.headers["X-Response-Time"]
        
        # Format check (e.g., "123ms")
        assert response_time.endswith("ms")
        assert float(response_time[:-2]) >= 0
    
    def test_cors_headers(self, client: TestClient):
        """Test CORS headers"""
        response = client.options(
            "/api/v1/test/test-success",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )
        
        assert response.status_code == 200
        assert "Access-Control-Allow-Origin" in response.headers


class TestErrorResponseFormat:
    """Test error response format consistency"""
    
    def test_error_response_structure(self, client: TestClient):
        """Test that all errors follow the same structure"""
        error_endpoints = [
            "/api/v1/test/test-authentication-error",
            "/api/v1/test/test-validation-error",
            "/api/v1/test/test-not-found?resource_id=123"
        ]
        
        for endpoint in error_endpoints:
            response = client.get(endpoint)
            data = response.json()
            
            # Check error structure
            assert "error" in data
            error = data["error"]
            
            assert "code" in error
            assert "message" in error
            assert "status_code" in error
            assert "request_id" in error
            
            # Code should be uppercase with underscores
            assert error["code"].isupper()
            assert " " not in error["code"]
            
            # Status code should match response status
            assert error["status_code"] == response.status_code
            
            # Request ID should be valid UUID format
            assert len(error["request_id"]) == 36