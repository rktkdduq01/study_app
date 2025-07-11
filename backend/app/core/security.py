from datetime import datetime, timedelta
from typing import Optional, Union, Dict, Any
from jose import JWTError, jwt, ExpiredSignatureError
from passlib.context import CryptContext
from cryptography.fernet import Fernet
import secrets
import redis
import json
import logging
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.exceptions import (
    TokenError, TokenExpiredError, TokenBlacklistedError, 
    InvalidTokenTypeError, EncryptionError, DecryptionError
)

# Configure logger
logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Data encryption
ENCRYPTION_KEY = settings.ENCRYPTION_KEY if hasattr(settings, 'ENCRYPTION_KEY') else Fernet.generate_key()
fernet = Fernet(ENCRYPTION_KEY)

# Redis client for token blacklist and refresh token storage
try:
    redis_client = redis.StrictRedis(
        host=settings.REDIS_HOST if hasattr(settings, 'REDIS_HOST') else "localhost",
        port=settings.REDIS_PORT if hasattr(settings, 'REDIS_PORT') else 6379,
        db=settings.REDIS_DB if hasattr(settings, 'REDIS_DB') else 0,
        decode_responses=True
    )
    redis_client.ping()
except:
    redis_client = None  # Fallback if Redis is not available


def create_access_token(
    subject: Union[str, int], 
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[Dict[str, Any]] = None
) -> str:
    """
    Create a JWT access token with enhanced security features.
    
    Args:
        subject: The subject of the token (usually user ID)
        expires_delta: Optional custom expiration time
        additional_claims: Additional claims to include in the token
    
    Returns:
        Encoded JWT token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "iat": datetime.utcnow(),
        "type": "access",
        "jti": secrets.token_urlsafe(16)  # JWT ID for revocation
    }
    
    if additional_claims:
        to_encode.update(additional_claims)
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(
    subject: Union[str, int],
    additional_claims: Optional[Dict[str, Any]] = None
) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        subject: The subject of the token (usually user ID)
        additional_claims: Additional claims to include in the token
    
    Returns:
        Encoded refresh token
    """
    expire = datetime.utcnow() + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS if hasattr(settings, 'REFRESH_TOKEN_EXPIRE_DAYS') else 7
    )
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "iat": datetime.utcnow(),
        "type": "refresh",
        "jti": secrets.token_urlsafe(16)
    }
    
    if additional_claims:
        to_encode.update(additional_claims)
    
    refresh_secret = settings.REFRESH_SECRET_KEY if hasattr(settings, 'REFRESH_SECRET_KEY') else settings.SECRET_KEY
    encoded_jwt = jwt.encode(
        to_encode,
        refresh_secret,
        algorithm=settings.ALGORITHM
    )
    
    # Store refresh token in Redis if available
    if redis_client:
        try:
            redis_client.setex(
                f"refresh:{subject}:{encoded_jwt[-20:]}",
                timedelta(days=7).total_seconds(),
                json.dumps({
                    "user_id": str(subject),
                    "created_at": datetime.utcnow().isoformat()
                })
            )
        except:
            pass
    
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    Args:
        plain_password: The plain text password
        hashed_password: The hashed password to check against
    
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password.
    
    Args:
        password: The plain text password to hash
    
    Returns:
        The hashed password
    """
    return pwd_context.hash(password)


def decode_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT token.
    
    Args:
        token: The JWT token to decode
        token_type: Type of token ("access" or "refresh")
    
    Returns:
        The payload if valid
        
    Raises:
        TokenExpiredError: If token has expired
        TokenBlacklistedError: If token is blacklisted
        InvalidTokenTypeError: If token type doesn't match
        TokenError: For other JWT validation errors
    """
    try:
        secret = settings.SECRET_KEY
        if token_type == "refresh" and hasattr(settings, 'REFRESH_SECRET_KEY'):
            secret = settings.REFRESH_SECRET_KEY
            
        payload = jwt.decode(
            token, 
            secret, 
            algorithms=[settings.ALGORITHM]
        )
        
        # Verify token type
        actual_type = payload.get("type")
        if actual_type != token_type:
            logger.warning(f"Token type mismatch. Expected: {token_type}, Got: {actual_type}")
            raise InvalidTokenTypeError(expected=token_type, actual=actual_type or "unknown")
        
        # Check if token is blacklisted (if Redis is available)
        if redis_client:
            try:
                jti = payload.get("jti")
                if jti and redis_client.get(f"blacklist:{jti}"):
                    logger.warning(f"Blacklisted token attempted: JTI={jti}")
                    raise TokenBlacklistedError(token_type=token_type)
            except redis.RedisError as e:
                logger.error(f"Redis error checking token blacklist: {e}")
                # Continue without blacklist check if Redis fails
            except (TokenBlacklistedError, InvalidTokenTypeError):
                # Re-raise our custom exceptions
                raise
        
        return payload
    except ExpiredSignatureError:
        logger.info(f"Expired {token_type} token attempted")
        raise TokenExpiredError(token_type=token_type)
    except (TokenExpiredError, TokenBlacklistedError, InvalidTokenTypeError):
        # Re-raise our custom exceptions
        raise
    except JWTError as e:
        logger.warning(f"JWT validation error: {e}")
        raise TokenError(detail=f"Invalid {token_type} token")


def decode_access_token(token: str) -> str:
    """
    Decode a JWT access token.
    
    Args:
        token: The JWT token to decode
    
    Returns:
        The subject (user ID) if valid
        
    Raises:
        TokenError: If token is invalid or user ID not found
    """
    payload = decode_token(token, "access")
    user_id = payload.get("sub") if payload else None
    if not user_id:
        logger.error("Access token missing 'sub' claim or invalid token")
        raise TokenError(detail="Invalid access token: missing user identifier")
    return user_id


def revoke_token(token: str, token_type: str = "access") -> bool:
    """
    Revoke a token by adding it to blacklist.
    
    Args:
        token: The token to revoke
        token_type: Type of token ("access" or "refresh")
    
    Returns:
        True if successfully revoked, False otherwise
    """
    if not redis_client:
        return False
    
    try:
        payload = decode_token(token, token_type)
        if not payload:
            return False
        
        jti = payload.get("jti")
        exp = payload.get("exp")
        
        if jti and exp:
            # Calculate TTL for Redis
            ttl = exp - datetime.utcnow().timestamp()
            if ttl > 0:
                redis_client.setex(f"blacklist:{jti}", int(ttl), "1")
                return True
    except:
        pass
    
    return False


def create_token_pair(
    subject: Union[str, int],
    additional_claims: Optional[Dict[str, Any]] = None
) -> Dict[str, str]:
    """
    Create both access and refresh tokens.
    
    Args:
        subject: The subject of the tokens (usually user ID)
        additional_claims: Additional claims to include
    
    Returns:
        Dictionary containing access_token, refresh_token, and token_type
    """
    access_token = create_access_token(subject, additional_claims=additional_claims)
    refresh_token = create_refresh_token(subject, additional_claims=additional_claims)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


def refresh_access_token(refresh_token: str) -> Dict[str, str]:
    """
    Create new access token from refresh token.
    
    Args:
        refresh_token: The refresh token
    
    Returns:
        Dictionary with new access token
        
    Raises:
        TokenError: If refresh token is invalid
    """
    try:
        payload = decode_token(refresh_token, "refresh")
        if not payload:
            raise TokenError(detail="Invalid refresh token")
        
        # Create new access token with same claims
        subject = payload.get("sub")
        if not subject:
            logger.error("Refresh token missing 'sub' claim during refresh")
            raise TokenError(detail="Invalid refresh token: missing user identifier")
        
        # Extract additional claims
        additional_claims = {
            k: v for k, v in payload.items() 
            if k not in ["exp", "iat", "sub", "type", "jti"]
        }
        
        access_token = create_access_token(subject, additional_claims=additional_claims)
        
        logger.info(f"Access token refreshed for user: {subject}")
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
    except Exception as e:
        logger.error(f"Failed to refresh access token: {e}")
        raise


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password meets security requirements.
    
    Args:
        password: The password to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    if not has_upper:
        return False, "Password must contain at least one uppercase letter"
    if not has_lower:
        return False, "Password must contain at least one lowercase letter"
    if not has_digit:
        return False, "Password must contain at least one digit"
    if not has_special:
        return False, "Password must contain at least one special character"
    
    return True, ""


def encrypt_data(data: str) -> str:
    """
    Encrypt sensitive data.
    
    Args:
        data: The data to encrypt
    
    Returns:
        Encrypted data as string
        
    Raises:
        EncryptionError: If encryption fails
    """
    try:
        if not data:
            raise ValueError("Cannot encrypt empty data")
        
        encrypted = fernet.encrypt(data.encode()).decode()
        logger.debug("Data encrypted successfully")
        return encrypted
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        raise EncryptionError(detail=f"Failed to encrypt data: {str(e)}")


def decrypt_data(encrypted_data: str) -> str:
    """
    Decrypt sensitive data.
    
    Args:
        encrypted_data: The encrypted data
    
    Returns:
        Decrypted data as string
        
    Raises:
        DecryptionError: If decryption fails
    """
    try:
        if not encrypted_data:
            raise ValueError("Cannot decrypt empty data")
        
        decrypted = fernet.decrypt(encrypted_data.encode()).decode()
        logger.debug("Data decrypted successfully")
        return decrypted
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        raise DecryptionError(detail=f"Failed to decrypt data: {str(e)}")


def generate_secure_token(length: int = 32) -> str:
    """
    Generate secure random token.
    
    Args:
        length: Length of the token
    
    Returns:
        Secure random token
    """
    return secrets.token_urlsafe(length)