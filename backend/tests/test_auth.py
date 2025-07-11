"""
Tests for authentication endpoints
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.models.user import User, UserRole
from app.core.security import create_token_pair, get_password_hash
from app.schemas.user import UserRole as UserRoleEnum


class TestRegister:
    """Test user registration endpoint"""
    
    def test_register_success(self, client: TestClient, db: Session):
        """Test successful user registration"""
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "NewUser123!",
            "full_name": "New User"
        }
        
        response = client.post("/api/v1/auth/register", json=data)
        assert response.status_code == 201
        
        result = response.json()
        assert result["username"] == data["username"]
        assert result["email"] == data["email"]
        assert result["full_name"] == data["full_name"]
        assert result["role"] == UserRole.STUDENT.value
        assert "id" in result
        assert "created_at" in result
        
        # Verify user in database
        user = db.query(User).filter(User.username == data["username"]).first()
        assert user is not None
        assert user.email == data["email"]
        assert user.is_active is True
    
    def test_register_duplicate_username(self, client: TestClient, test_user: User):
        """Test registration with existing username"""
        data = {
            "username": test_user.username,
            "email": "different@example.com",
            "password": "Password123!",
            "full_name": "Different User"
        }
        
        response = client.post("/api/v1/auth/register", json=data)
        assert response.status_code == 409
        
        error = response.json()["error"]
        assert error["code"] == "CONFLICT"
        assert "username" in error["message"].lower()
    
    def test_register_duplicate_email(self, client: TestClient, test_user: User):
        """Test registration with existing email"""
        data = {
            "username": "differentuser",
            "email": test_user.email,
            "password": "Password123!",
            "full_name": "Different User"
        }
        
        response = client.post("/api/v1/auth/register", json=data)
        assert response.status_code == 409
        
        error = response.json()["error"]
        assert error["code"] == "CONFLICT"
        assert "email" in error["message"].lower()
    
    def test_register_invalid_email(self, client: TestClient):
        """Test registration with invalid email format"""
        data = {
            "username": "testuser",
            "email": "invalid-email",
            "password": "Password123!",
            "full_name": "Test User"
        }
        
        response = client.post("/api/v1/auth/register", json=data)
        assert response.status_code == 422
    
    def test_register_weak_password(self, client: TestClient):
        """Test registration with weak password"""
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "weak",
            "full_name": "Test User"
        }
        
        response = client.post("/api/v1/auth/register", json=data)
        assert response.status_code == 422
    
    def test_register_missing_required_fields(self, client: TestClient):
        """Test registration with missing required fields"""
        data = {
            "username": "testuser"
            # Missing email and password
        }
        
        response = client.post("/api/v1/auth/register", json=data)
        assert response.status_code == 422


class TestLogin:
    """Test user login endpoint"""
    
    def test_login_success_with_username(self, client: TestClient, test_user: User):
        """Test successful login with username"""
        data = {
            "username": test_user.username,
            "password": "testpassword"
        }
        
        response = client.post("/api/v1/auth/login", json=data)
        assert response.status_code == 200
        
        result = response.json()
        assert "access_token" in result
        assert "refresh_token" in result
        assert result["token_type"] == "bearer"
        assert "user" in result
        assert result["user"]["username"] == test_user.username
    
    def test_login_success_with_email(self, client: TestClient, test_user: User):
        """Test successful login with email"""
        data = {
            "username": test_user.email,
            "password": "testpassword"
        }
        
        response = client.post("/api/v1/auth/login", json=data)
        assert response.status_code == 200
        
        result = response.json()
        assert "access_token" in result
        assert "refresh_token" in result
    
    def test_login_invalid_credentials(self, client: TestClient, test_user: User):
        """Test login with invalid credentials"""
        data = {
            "username": test_user.username,
            "password": "wrongpassword"
        }
        
        response = client.post("/api/v1/auth/login", json=data)
        assert response.status_code == 401
        
        error = response.json()["error"]
        assert error["code"] == "AUTHENTICATION_ERROR"
    
    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with non-existent user"""
        data = {
            "username": "nonexistent",
            "password": "password123"
        }
        
        response = client.post("/api/v1/auth/login", json=data)
        assert response.status_code == 401
        
        error = response.json()["error"]
        assert error["code"] == "AUTHENTICATION_ERROR"
    
    def test_login_inactive_user(self, client: TestClient, db: Session):
        """Test login with inactive user"""
        # Create inactive user
        user = User(
            username="inactive",
            email="inactive@example.com",
            hashed_password=get_password_hash("password123"),
            is_active=False
        )
        db.add(user)
        db.commit()
        
        data = {
            "username": "inactive",
            "password": "password123"
        }
        
        response = client.post("/api/v1/auth/login", json=data)
        assert response.status_code == 401
        
        error = response.json()["error"]
        assert error["code"] == "AUTHENTICATION_ERROR"


class TestRefreshToken:
    """Test token refresh endpoint"""
    
    def test_refresh_token_success(self, client: TestClient, test_user: User):
        """Test successful token refresh"""
        # First login to get tokens
        login_data = {
            "username": test_user.username,
            "password": "testpassword"
        }
        login_response = client.post("/api/v1/auth/login", json=login_data)
        tokens = login_response.json()
        
        # Refresh token
        refresh_data = {
            "refresh_token": tokens["refresh_token"]
        }
        
        response = client.post("/api/v1/auth/refresh", json=refresh_data)
        assert response.status_code == 200
        
        result = response.json()
        assert "access_token" in result
        assert "token_type" in result
        assert result["token_type"] == "bearer"
        
        # New access token should be different
        assert result["access_token"] != tokens["access_token"]
    
    def test_refresh_token_invalid(self, client: TestClient):
        """Test refresh with invalid token"""
        refresh_data = {
            "refresh_token": "invalid.refresh.token"
        }
        
        response = client.post("/api/v1/auth/refresh", json=refresh_data)
        assert response.status_code == 401
        
        error = response.json()["error"]
        assert error["code"] == "AUTHENTICATION_ERROR"
    
    def test_refresh_token_expired(self, client: TestClient, test_user: User):
        """Test refresh with expired token"""
        # Create an expired refresh token
        access_token, refresh_token = create_token_pair(
            data={"sub": test_user.username},
            access_token_expires_delta=timedelta(minutes=-1),
            refresh_token_expires_delta=timedelta(minutes=-1)
        )
        
        refresh_data = {
            "refresh_token": refresh_token
        }
        
        response = client.post("/api/v1/auth/refresh", json=refresh_data)
        assert response.status_code == 401
        
        error = response.json()["error"]
        assert error["code"] == "AUTHENTICATION_ERROR"


class TestGetCurrentUser:
    """Test get current user endpoint"""
    
    def test_get_current_user_success(
        self, 
        client: TestClient, 
        test_user: User,
        test_user_token_headers: dict
    ):
        """Test getting current user info"""
        response = client.get("/api/v1/auth/me", headers=test_user_token_headers)
        assert response.status_code == 200
        
        result = response.json()
        assert result["id"] == test_user.id
        assert result["username"] == test_user.username
        assert result["email"] == test_user.email
        assert result["full_name"] == test_user.full_name
        assert result["role"] == test_user.role
    
    def test_get_current_user_no_auth(self, client: TestClient):
        """Test getting current user without authentication"""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401
        
        error = response.json()["error"]
        assert error["code"] == "AUTHENTICATION_ERROR"
    
    def test_get_current_user_invalid_token(self, client: TestClient):
        """Test getting current user with invalid token"""
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401
        
        error = response.json()["error"]
        assert error["code"] == "AUTHENTICATION_ERROR"


class TestUpdateProfile:
    """Test update profile endpoint"""
    
    def test_update_profile_success(
        self,
        client: TestClient,
        test_user: User,
        test_user_token_headers: dict,
        db: Session
    ):
        """Test successful profile update"""
        update_data = {
            "full_name": "Updated Name",
            "bio": "This is my bio"
        }
        
        response = client.put(
            "/api/v1/auth/me", 
            json=update_data,
            headers=test_user_token_headers
        )
        assert response.status_code == 200
        
        result = response.json()
        assert result["full_name"] == update_data["full_name"]
        assert result["bio"] == update_data["bio"]
        
        # Verify in database
        db.refresh(test_user)
        assert test_user.full_name == update_data["full_name"]
        assert test_user.bio == update_data["bio"]
    
    def test_update_profile_email_conflict(
        self,
        client: TestClient,
        test_user: User,
        test_admin_user: User,
        test_user_token_headers: dict
    ):
        """Test profile update with existing email"""
        update_data = {
            "email": test_admin_user.email
        }
        
        response = client.put(
            "/api/v1/auth/me",
            json=update_data,
            headers=test_user_token_headers
        )
        assert response.status_code == 409
        
        error = response.json()["error"]
        assert error["code"] == "CONFLICT"
        assert "email" in error["message"].lower()
    
    def test_update_profile_no_auth(self, client: TestClient):
        """Test profile update without authentication"""
        update_data = {
            "full_name": "Updated Name"
        }
        
        response = client.put("/api/v1/auth/me", json=update_data)
        assert response.status_code == 401


class TestChangePassword:
    """Test change password endpoint"""
    
    def test_change_password_success(
        self,
        client: TestClient,
        test_user: User,
        test_user_token_headers: dict
    ):
        """Test successful password change"""
        data = {
            "current_password": "testpassword",
            "new_password": "NewPassword123!"
        }
        
        response = client.post(
            "/api/v1/auth/change-password",
            json=data,
            headers=test_user_token_headers
        )
        assert response.status_code == 200
        
        result = response.json()
        assert result["message"] == "Password changed successfully"
        
        # Verify can login with new password
        login_data = {
            "username": test_user.username,
            "password": data["new_password"]
        }
        login_response = client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
    
    def test_change_password_wrong_current(
        self,
        client: TestClient,
        test_user: User,
        test_user_token_headers: dict
    ):
        """Test password change with wrong current password"""
        data = {
            "current_password": "wrongpassword",
            "new_password": "NewPassword123!"
        }
        
        response = client.post(
            "/api/v1/auth/change-password",
            json=data,
            headers=test_user_token_headers
        )
        assert response.status_code == 400
        
        error = response.json()["error"]
        assert error["code"] == "BUSINESS_LOGIC_ERROR"
    
    def test_change_password_weak_new(
        self,
        client: TestClient,
        test_user: User,
        test_user_token_headers: dict
    ):
        """Test password change with weak new password"""
        data = {
            "current_password": "testpassword",
            "new_password": "weak"
        }
        
        response = client.post(
            "/api/v1/auth/change-password",
            json=data,
            headers=test_user_token_headers
        )
        assert response.status_code == 422
    
    def test_change_password_no_auth(self, client: TestClient):
        """Test password change without authentication"""
        data = {
            "current_password": "oldpassword",
            "new_password": "NewPassword123!"
        }
        
        response = client.post("/api/v1/auth/change-password", json=data)
        assert response.status_code == 401


class TestLogout:
    """Test logout endpoint"""
    
    def test_logout_success(
        self,
        client: TestClient,
        test_user: User,
        test_user_token_headers: dict
    ):
        """Test successful logout"""
        response = client.post(
            "/api/v1/auth/logout",
            headers=test_user_token_headers
        )
        assert response.status_code == 200
        
        result = response.json()
        assert result["message"] == "Successfully logged out"
        
        # Verify token is invalidated (would need Redis to fully test)
        # For now, just verify the endpoint returns success
    
    def test_logout_no_auth(self, client: TestClient):
        """Test logout without authentication"""
        response = client.post("/api/v1/auth/logout")
        assert response.status_code == 401