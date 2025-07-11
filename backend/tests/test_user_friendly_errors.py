"""
Tests for user-friendly error handling
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    BusinessLogicError,
    RateLimitError
)
from app.core.error_messages import get_user_message, get_field_error_message


class TestErrorMessages:
    """Test error message functions"""
    
    def test_get_user_message_with_valid_code(self):
        """Test getting user message with valid error code"""
        result = get_user_message("AUTH001")
        
        assert result["message"] == "로그인이 필요합니다"
        assert result["action"] == "다시 로그인해주세요"
        assert result["category"] == "authentication"
    
    def test_get_user_message_with_context(self):
        """Test getting user message with context"""
        result = get_user_message("RATE001", context={"retry_after": 30})
        
        assert result["message"] == "너무 많은 요청을 보냈습니다"
        assert result["action"] == "30초 후에 다시 시도해주세요"
    
    def test_get_user_message_with_invalid_code(self):
        """Test getting user message with invalid error code"""
        result = get_user_message("INVALID_CODE", "Custom fallback message")
        
        assert result["message"] == "Custom fallback message"
        assert result["action"] == "문제가 지속되면 고객센터에 문의해주세요"
        assert result["category"] == "server"
    
    def test_get_field_error_message(self):
        """Test getting field-specific error messages"""
        assert get_field_error_message("email", "required") == "이메일을(를) 입력해주세요"
        assert get_field_error_message("password", "too_short") == "비밀번호이(가) 너무 짧습니다"
        assert get_field_error_message("phone", "invalid") == "올바른 전화번호 형식이 아닙니다"


class TestCustomExceptions:
    """Test custom exception classes"""
    
    def test_authentication_error(self):
        """Test AuthenticationError with error code"""
        error = AuthenticationError(error_code="AUTH003")
        
        assert error.error_code == "AUTH003"
        assert error.user_message == "잘못된 이메일 또는 비밀번호입니다"
        assert error.action == "입력 정보를 확인하고 다시 시도해주세요"
        assert error.category == "authentication"
    
    def test_authorization_error_with_context(self):
        """Test AuthorizationError with required role"""
        error = AuthorizationError(
            error_code="PERM001",
            required_role="admin"
        )
        
        assert error.error_code == "PERM001"
        assert error.user_message == "접근 권한이 없습니다"
        assert error.data == {"required_role": "admin"}
    
    def test_validation_error_with_field(self):
        """Test ValidationError with field information"""
        error = ValidationError(
            detail="Invalid email format",
            field="email",
            error_code="VAL003"
        )
        
        assert error.error_code == "VAL003"
        assert error.user_message == "올바른 이메일 형식이 아닙니다"
        assert error.data == {"field": "email"}
    
    def test_rate_limit_error_with_retry(self):
        """Test RateLimitError with retry_after"""
        error = RateLimitError(
            retry_after=60,
            error_code="RATE001"
        )
        
        assert error.error_code == "RATE001"
        assert error.user_message == "너무 많은 요청을 보냈습니다"
        assert error.data == {"retry_after": 60}
        assert error.headers["Retry-After"] == "60"


@pytest.mark.integration
class TestErrorHandlingIntegration:
    """Integration tests for error handling"""
    
    def test_authentication_error_response(self, client: TestClient):
        """Test authentication error response format"""
        # Create a test endpoint that raises auth error
        from app.main import app
        
        @app.get("/test-auth-error")
        async def test_auth_error():
            raise AuthenticationError(error_code="AUTH001")
        
        response = client.get("/test-auth-error")
        
        assert response.status_code == 401
        data = response.json()
        
        assert data["error"]["code"] == "AUTH001"
        assert data["error"]["user_message"] == "로그인이 필요합니다"
        assert data["error"]["action"] == "다시 로그인해주세요"
        assert data["error"]["category"] == "authentication"
        assert "request_id" in data["error"]
    
    def test_validation_error_response(self, client: TestClient):
        """Test validation error response with field errors"""
        from app.main import app
        from pydantic import BaseModel, validator
        
        class TestModel(BaseModel):
            email: str
            age: int
            
            @validator('email')
            def validate_email(cls, v):
                if '@' not in v:
                    raise ValueError('Invalid email format')
                return v
        
        @app.post("/test-validation-error")
        async def test_validation_error(data: TestModel):
            return {"success": True}
        
        response = client.post("/test-validation-error", json={
            "email": "invalid-email",
            "age": "not-a-number"
        })
        
        assert response.status_code == 422
        data = response.json()
        
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert data["error"]["user_message"] == "입력 정보를 확인해주세요"
        assert data["error"]["category"] == "validation"
        assert "user_errors" in data["error"]["data"]
        
        # Check user-friendly field errors
        user_errors = data["error"]["data"]["user_errors"]
        assert any(e["field"] == "email" for e in user_errors)
        assert any(e["field"] == "age" for e in user_errors)
    
    def test_business_logic_error_response(self, client: TestClient):
        """Test business logic error response"""
        from app.main import app
        
        @app.post("/test-business-error")
        async def test_business_error():
            raise BusinessLogicError(
                error_code="BIZ003",
                detail="User has insufficient points"
            )
        
        response = client.post("/test-business-error")
        
        assert response.status_code == 400
        data = response.json()
        
        assert data["error"]["code"] == "BIZ003"
        assert data["error"]["user_message"] == "포인트가 부족합니다"
        assert data["error"]["action"] == "퀘스트를 완료하여 포인트를 획득하세요"
        assert data["error"]["category"] == "business"
    
    def test_rate_limit_error_response(self, client: TestClient):
        """Test rate limit error response"""
        from app.main import app
        
        @app.get("/test-rate-limit")
        async def test_rate_limit():
            raise RateLimitError(
                retry_after=30,
                error_code="RATE001"
            )
        
        response = client.get("/test-rate-limit")
        
        assert response.status_code == 429
        assert response.headers["Retry-After"] == "30"
        
        data = response.json()
        assert data["error"]["code"] == "RATE001"
        assert data["error"]["user_message"] == "너무 많은 요청을 보냈습니다"
        assert data["error"]["data"]["retry_after"] == 30
    
    def test_unhandled_error_response(self, client: TestClient):
        """Test unhandled error gets user-friendly message"""
        from app.main import app
        
        @app.get("/test-unhandled-error")
        async def test_unhandled_error():
            raise Exception("Something went wrong")
        
        response = client.get("/test-unhandled-error")
        
        assert response.status_code == 500
        data = response.json()
        
        assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
        assert data["error"]["user_message"] == "일시적인 오류가 발생했습니다"
        assert data["error"]["action"] == "잠시 후 다시 시도해주세요"
        assert data["error"]["category"] == "server"
        assert "request_id" in data["error"]


class TestErrorScenarios:
    """Test specific error scenarios"""
    
    def test_login_failure_scenario(self, client: TestClient, db: Session):
        """Test login failure with user-friendly error"""
        response = client.post("/api/v1/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
        data = response.json()
        
        # Should get user-friendly login error
        assert data["error"]["code"] == "AUTH003"
        assert data["error"]["user_message"] == "잘못된 이메일 또는 비밀번호입니다"
        assert data["error"]["action"] == "입력 정보를 확인하고 다시 시도해주세요"
    
    def test_expired_token_scenario(self, client: TestClient):
        """Test expired token with user-friendly error"""
        # Use an expired token
        expired_token = "expired.jwt.token"
        
        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        
        assert response.status_code == 401
        data = response.json()
        
        assert data["error"]["code"] == "AUTH002"
        assert data["error"]["user_message"] == "로그인 정보가 만료되었습니다"
        assert data["error"]["action"] == "보안을 위해 다시 로그인해주세요"
    
    def test_permission_denied_scenario(self, client: TestClient, normal_user_token: str):
        """Test permission denied with user-friendly error"""
        response = client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {normal_user_token}"}
        )
        
        assert response.status_code == 403
        data = response.json()
        
        assert data["error"]["code"] == "PERM001"
        assert data["error"]["user_message"] == "접근 권한이 없습니다"
        assert data["error"]["action"] == "필요한 권한이 있는지 확인해주세요"