"""
Tests for security module
"""
import pytest
from datetime import datetime, timedelta
from jose import jwt, JWTError

from app.core.security import (
    verify_password,
    get_password_hash,
    create_token_pair,
    refresh_access_token,
    verify_token,
    encrypt_data,
    decrypt_data
)
from app.core.config import settings


class TestPasswordHashing:
    """Test password hashing functions"""
    
    def test_password_hash_and_verify(self):
        """Test password hashing and verification"""
        password = "TestPassword123!"
        
        # Hash password
        hashed = get_password_hash(password)
        
        # Verify correct password
        assert verify_password(password, hashed) is True
        
        # Verify incorrect password
        assert verify_password("WrongPassword", hashed) is False
        
        # Verify hash is different each time
        hashed2 = get_password_hash(password)
        assert hashed != hashed2
        assert verify_password(password, hashed2) is True
    
    def test_empty_password(self):
        """Test hashing empty password"""
        password = ""
        hashed = get_password_hash(password)
        
        assert verify_password("", hashed) is True
        assert verify_password("NotEmpty", hashed) is False


class TestTokenCreation:
    """Test JWT token creation and verification"""
    
    def test_create_token_pair(self):
        """Test creating access and refresh token pair"""
        data = {"sub": "testuser", "role": "student"}
        
        access_token, refresh_token = create_token_pair(data)
        
        assert access_token is not None
        assert refresh_token is not None
        assert access_token != refresh_token
        
        # Decode and verify access token
        access_payload = jwt.decode(
            access_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        assert access_payload["sub"] == data["sub"]
        assert access_payload["role"] == data["role"]
        assert access_payload["type"] == "access"
        assert "exp" in access_payload
        
        # Decode and verify refresh token
        refresh_payload = jwt.decode(
            refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        assert refresh_payload["sub"] == data["sub"]
        assert refresh_payload["role"] == data["role"]
        assert refresh_payload["type"] == "refresh"
        assert "exp" in refresh_payload
    
    def test_create_token_with_custom_expiry(self):
        """Test creating tokens with custom expiry times"""
        data = {"sub": "testuser"}
        access_delta = timedelta(minutes=5)
        refresh_delta = timedelta(days=1)
        
        access_token, refresh_token = create_token_pair(
            data,
            access_token_expires_delta=access_delta,
            refresh_token_expires_delta=refresh_delta
        )
        
        # Verify access token expiry
        access_payload = jwt.decode(
            access_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        access_exp = datetime.fromtimestamp(access_payload["exp"])
        expected_exp = datetime.utcnow() + access_delta
        assert abs((access_exp - expected_exp).total_seconds()) < 2
        
        # Verify refresh token expiry
        refresh_payload = jwt.decode(
            refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        refresh_exp = datetime.fromtimestamp(refresh_payload["exp"])
        expected_exp = datetime.utcnow() + refresh_delta
        assert abs((refresh_exp - expected_exp).total_seconds()) < 2
    
    def test_create_expired_token(self):
        """Test creating already expired tokens"""
        data = {"sub": "testuser"}
        
        access_token, refresh_token = create_token_pair(
            data,
            access_token_expires_delta=timedelta(minutes=-1),
            refresh_token_expires_delta=timedelta(minutes=-1)
        )
        
        # Verify tokens are expired
        with pytest.raises(JWTError):
            jwt.decode(
                access_token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
        
        with pytest.raises(JWTError):
            jwt.decode(
                refresh_token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )


class TestTokenRefresh:
    """Test token refresh functionality"""
    
    def test_refresh_access_token_success(self):
        """Test successful access token refresh"""
        data = {"sub": "testuser", "role": "student"}
        
        # Create initial tokens
        _, refresh_token = create_token_pair(data)
        
        # Refresh access token
        new_access_token = refresh_access_token(refresh_token)
        
        assert new_access_token is not None
        
        # Verify new access token
        payload = jwt.decode(
            new_access_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        assert payload["sub"] == data["sub"]
        assert payload["role"] == data["role"]
        assert payload["type"] == "access"
    
    def test_refresh_with_invalid_token(self):
        """Test refresh with invalid token"""
        invalid_token = "invalid.refresh.token"
        
        new_access_token = refresh_access_token(invalid_token)
        assert new_access_token is None
    
    def test_refresh_with_access_token(self):
        """Test refresh with access token instead of refresh token"""
        data = {"sub": "testuser"}
        
        # Create access token
        access_token, _ = create_token_pair(data)
        
        # Try to refresh with access token (should fail)
        new_access_token = refresh_access_token(access_token)
        assert new_access_token is None
    
    def test_refresh_with_expired_token(self):
        """Test refresh with expired refresh token"""
        data = {"sub": "testuser"}
        
        # Create expired refresh token
        _, refresh_token = create_token_pair(
            data,
            refresh_token_expires_delta=timedelta(minutes=-1)
        )
        
        # Try to refresh (should fail)
        new_access_token = refresh_access_token(refresh_token)
        assert new_access_token is None


class TestTokenVerification:
    """Test token verification"""
    
    def test_verify_valid_access_token(self):
        """Test verifying valid access token"""
        data = {"sub": "testuser"}
        
        access_token, _ = create_token_pair(data)
        
        payload = verify_token(access_token, "access")
        assert payload is not None
        assert payload["sub"] == data["sub"]
        assert payload["type"] == "access"
    
    def test_verify_valid_refresh_token(self):
        """Test verifying valid refresh token"""
        data = {"sub": "testuser"}
        
        _, refresh_token = create_token_pair(data)
        
        payload = verify_token(refresh_token, "refresh")
        assert payload is not None
        assert payload["sub"] == data["sub"]
        assert payload["type"] == "refresh"
    
    def test_verify_wrong_token_type(self):
        """Test verifying token with wrong type"""
        data = {"sub": "testuser"}
        
        access_token, refresh_token = create_token_pair(data)
        
        # Try to verify access token as refresh token
        payload = verify_token(access_token, "refresh")
        assert payload is None
        
        # Try to verify refresh token as access token
        payload = verify_token(refresh_token, "access")
        assert payload is None
    
    def test_verify_invalid_token(self):
        """Test verifying invalid token"""
        invalid_token = "invalid.token.here"
        
        payload = verify_token(invalid_token, "access")
        assert payload is None
    
    def test_verify_expired_token(self):
        """Test verifying expired token"""
        data = {"sub": "testuser"}
        
        # Create expired token
        access_token, _ = create_token_pair(
            data,
            access_token_expires_delta=timedelta(minutes=-1)
        )
        
        payload = verify_token(access_token, "access")
        assert payload is None


class TestDataEncryption:
    """Test data encryption and decryption"""
    
    def test_encrypt_and_decrypt_string(self):
        """Test encrypting and decrypting string data"""
        original_data = "This is sensitive data"
        
        # Encrypt data
        encrypted = encrypt_data(original_data)
        assert encrypted is not None
        assert encrypted != original_data
        assert isinstance(encrypted, str)
        
        # Decrypt data
        decrypted = decrypt_data(encrypted)
        assert decrypted == original_data
    
    def test_encrypt_and_decrypt_dict(self):
        """Test encrypting and decrypting dictionary data"""
        original_data = {
            "username": "testuser",
            "email": "test@example.com",
            "sensitive_info": "secret123"
        }
        
        # Encrypt data
        encrypted = encrypt_data(original_data)
        assert encrypted is not None
        assert isinstance(encrypted, str)
        
        # Decrypt data
        decrypted = decrypt_data(encrypted)
        assert decrypted == original_data
        assert isinstance(decrypted, dict)
    
    def test_encrypt_and_decrypt_list(self):
        """Test encrypting and decrypting list data"""
        original_data = ["item1", "item2", "item3", 123, True]
        
        # Encrypt data
        encrypted = encrypt_data(original_data)
        assert encrypted is not None
        assert isinstance(encrypted, str)
        
        # Decrypt data
        decrypted = decrypt_data(encrypted)
        assert decrypted == original_data
        assert isinstance(decrypted, list)
    
    def test_decrypt_invalid_data(self):
        """Test decrypting invalid encrypted data"""
        invalid_encrypted = "not_valid_encrypted_data"
        
        decrypted = decrypt_data(invalid_encrypted)
        assert decrypted is None
    
    def test_encrypt_empty_data(self):
        """Test encrypting empty data"""
        # Empty string
        encrypted = encrypt_data("")
        decrypted = decrypt_data(encrypted)
        assert decrypted == ""
        
        # Empty dict
        encrypted = encrypt_data({})
        decrypted = decrypt_data(encrypted)
        assert decrypted == {}
        
        # Empty list
        encrypted = encrypt_data([])
        decrypted = decrypt_data(encrypted)
        assert decrypted == []
    
    def test_encrypt_none(self):
        """Test encrypting None value"""
        encrypted = encrypt_data(None)
        assert encrypted is None
    
    def test_decrypt_none(self):
        """Test decrypting None value"""
        decrypted = decrypt_data(None)
        assert decrypted is None