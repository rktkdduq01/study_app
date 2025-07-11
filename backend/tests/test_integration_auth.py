"""
Integration tests for authentication flow
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.character import Character


class TestAuthenticationFlow:
    """Test complete authentication flow"""
    
    def test_complete_registration_and_login_flow(
        self,
        client: TestClient,
        db: Session
    ):
        """Test full registration and login flow"""
        # 1. Register new user
        register_data = {
            "username": "integrationuser",
            "email": "integration@example.com",
            "password": "Integration123!",
            "full_name": "Integration Test User"
        }
        
        register_response = client.post(
            "/api/v1/auth/register",
            json=register_data
        )
        assert register_response.status_code == 201
        
        user_data = register_response.json()
        user_id = user_data["id"]
        
        # 2. Verify user in database
        user = db.query(User).filter(User.id == user_id).first()
        assert user is not None
        assert user.username == register_data["username"]
        assert user.email == register_data["email"]
        
        # 3. Verify character was created
        character = db.query(Character).filter(
            Character.user_id == user_id
        ).first()
        assert character is not None
        assert character.name == f"{register_data['username']}'s Character"
        
        # 4. Login with username
        login_data = {
            "username": register_data["username"],
            "password": register_data["password"]
        }
        
        login_response = client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        tokens = login_response.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["user"]["id"] == user_id
        
        # 5. Access protected endpoint
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        me_response = client.get("/api/v1/auth/me", headers=headers)
        assert me_response.status_code == 200
        assert me_response.json()["id"] == user_id
        
        # 6. Update profile
        update_data = {
            "full_name": "Updated Integration User",
            "bio": "This is my bio"
        }
        
        update_response = client.put(
            "/api/v1/auth/me",
            json=update_data,
            headers=headers
        )
        assert update_response.status_code == 200
        assert update_response.json()["full_name"] == update_data["full_name"]
        
        # 7. Change password
        password_data = {
            "current_password": register_data["password"],
            "new_password": "NewIntegration123!"
        }
        
        password_response = client.post(
            "/api/v1/auth/change-password",
            json=password_data,
            headers=headers
        )
        assert password_response.status_code == 200
        
        # 8. Login with new password
        new_login_data = {
            "username": register_data["username"],
            "password": password_data["new_password"]
        }
        
        new_login_response = client.post(
            "/api/v1/auth/login",
            json=new_login_data
        )
        assert new_login_response.status_code == 200
        
        # 9. Refresh token
        refresh_data = {
            "refresh_token": tokens["refresh_token"]
        }
        
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            json=refresh_data
        )
        assert refresh_response.status_code == 200
        
        new_access_token = refresh_response.json()["access_token"]
        assert new_access_token != tokens["access_token"]
        
        # 10. Logout
        logout_response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {new_access_token}"}
        )
        assert logout_response.status_code == 200
    
    def test_parent_child_account_flow(
        self,
        client: TestClient,
        db: Session
    ):
        """Test parent and child account creation flow"""
        # 1. Register parent account
        parent_data = {
            "username": "parentuser",
            "email": "parent@example.com",
            "password": "Parent123!",
            "full_name": "Parent User",
            "role": "parent"
        }
        
        parent_response = client.post(
            "/api/v1/auth/register",
            json=parent_data
        )
        assert parent_response.status_code == 201
        
        parent_id = parent_response.json()["id"]
        
        # 2. Login as parent
        parent_login = client.post(
            "/api/v1/auth/login",
            json={
                "username": parent_data["username"],
                "password": parent_data["password"]
            }
        )
        assert parent_login.status_code == 200
        
        parent_token = parent_login.json()["access_token"]
        parent_headers = {"Authorization": f"Bearer {parent_token}"}
        
        # 3. Create child account (would need parent-child endpoint)
        # This is a placeholder for when parent-child functionality is implemented
        
        # 4. Register child account independently for now
        child_data = {
            "username": "childuser",
            "email": "child@example.com",
            "password": "Child123!",
            "full_name": "Child User",
            "role": "student"
        }
        
        child_response = client.post(
            "/api/v1/auth/register",
            json=child_data
        )
        assert child_response.status_code == 201
        
        child_id = child_response.json()["id"]
        
        # Verify both accounts exist
        parent = db.query(User).filter(User.id == parent_id).first()
        child = db.query(User).filter(User.id == child_id).first()
        
        assert parent is not None
        assert child is not None
        assert parent.role.value == "parent"
        assert child.role.value == "student"


class TestTokenManagement:
    """Test token lifecycle and security"""
    
    def test_token_expiration_and_refresh(
        self,
        client: TestClient,
        test_user: User
    ):
        """Test token expiration and refresh flow"""
        # Login to get tokens
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user.username,
                "password": "testpassword"
            }
        )
        assert login_response.status_code == 200
        
        tokens = login_response.json()
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
        
        # Access protected endpoint with valid token
        headers = {"Authorization": f"Bearer {access_token}"}
        me_response = client.get("/api/v1/auth/me", headers=headers)
        assert me_response.status_code == 200
        
        # Refresh the token
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert refresh_response.status_code == 200
        
        new_access_token = refresh_response.json()["access_token"]
        
        # Use new access token
        new_headers = {"Authorization": f"Bearer {new_access_token}"}
        me_response2 = client.get("/api/v1/auth/me", headers=new_headers)
        assert me_response2.status_code == 200
        
        # Old access token should still work (not expired yet)
        me_response3 = client.get("/api/v1/auth/me", headers=headers)
        assert me_response3.status_code == 200
    
    def test_concurrent_sessions(
        self,
        client: TestClient,
        test_user: User
    ):
        """Test multiple concurrent sessions"""
        # Login from first session
        session1_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user.username,
                "password": "testpassword"
            }
        )
        assert session1_response.status_code == 200
        session1_token = session1_response.json()["access_token"]
        
        # Login from second session
        session2_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user.username,
                "password": "testpassword"
            }
        )
        assert session2_response.status_code == 200
        session2_token = session2_response.json()["access_token"]
        
        # Both tokens should be different
        assert session1_token != session2_token
        
        # Both sessions should work
        headers1 = {"Authorization": f"Bearer {session1_token}"}
        headers2 = {"Authorization": f"Bearer {session2_token}"}
        
        me_response1 = client.get("/api/v1/auth/me", headers=headers1)
        me_response2 = client.get("/api/v1/auth/me", headers=headers2)
        
        assert me_response1.status_code == 200
        assert me_response2.status_code == 200
        assert me_response1.json()["id"] == me_response2.json()["id"]


class TestSecurityFeatures:
    """Test security features like rate limiting and validation"""
    
    def test_password_validation(self, client: TestClient):
        """Test password strength validation"""
        weak_passwords = [
            "short",           # Too short
            "nouppercase123!", # No uppercase
            "NOLOWERCASE123!", # No lowercase
            "NoNumbers!",      # No numbers
            "NoSpecialChar1",  # No special characters
        ]
        
        for weak_password in weak_passwords:
            register_data = {
                "username": "testuser",
                "email": "test@example.com",
                "password": weak_password,
                "full_name": "Test User"
            }
            
            response = client.post("/api/v1/auth/register", json=register_data)
            assert response.status_code == 422
    
    def test_input_validation(self, client: TestClient):
        """Test input validation for various fields"""
        # Invalid email format
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "email": "invalid-email",
                "password": "Valid123!",
                "full_name": "Test User"
            }
        )
        assert response.status_code == 422
        
        # Empty username
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "",
                "email": "test@example.com",
                "password": "Valid123!",
                "full_name": "Test User"
            }
        )
        assert response.status_code == 422
        
        # Username too long
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "a" * 51,  # Assuming 50 char limit
                "email": "test@example.com",
                "password": "Valid123!",
                "full_name": "Test User"
            }
        )
        assert response.status_code == 422
    
    def test_sql_injection_protection(
        self,
        client: TestClient,
        test_user: User
    ):
        """Test protection against SQL injection"""
        # Try SQL injection in login
        malicious_inputs = [
            "admin' OR '1'='1",
            "admin'; DROP TABLE users; --",
            "admin' UNION SELECT * FROM users --",
        ]
        
        for malicious_input in malicious_inputs:
            response = client.post(
                "/api/v1/auth/login",
                json={
                    "username": malicious_input,
                    "password": "password"
                }
            )
            # Should return 401, not 500 (SQL error)
            assert response.status_code == 401
            
            # Ensure error message doesn't leak SQL info
            error = response.json()["error"]
            assert "SQL" not in error["message"]
            assert "SELECT" not in error["message"]