from typing import Any, Dict, List, Optional
import json
from cryptography.fernet import Fernet
from sqlalchemy.types import TypeDecorator, String
from sqlalchemy.ext.mutable import MutableDict

from app.core.security import encrypt_data, decrypt_data


class EncryptedType(TypeDecorator):
    """SQLAlchemy type for encrypted fields"""
    impl = String
    cache_ok = True
    
    def process_bind_param(self, value, dialect):
        """Encrypt value before storing in database"""
        if value is None:
            return None
        
        # Convert non-string values to JSON
        if not isinstance(value, str):
            value = json.dumps(value)
        
        return encrypt_data(value)
    
    def process_result_value(self, value, dialect):
        """Decrypt value when retrieving from database"""
        if value is None:
            return None
        
        decrypted = decrypt_data(value)
        
        # Try to parse as JSON
        try:
            return json.loads(decrypted)
        except (json.JSONDecodeError, TypeError):
            return decrypted


class EncryptedJSON(TypeDecorator):
    """SQLAlchemy type for encrypted JSON fields"""
    impl = String
    cache_ok = True
    
    def process_bind_param(self, value, dialect):
        """Serialize and encrypt JSON before storing"""
        if value is None:
            return None
        
        json_str = json.dumps(value)
        return encrypt_data(json_str)
    
    def process_result_value(self, value, dialect):
        """Decrypt and deserialize JSON when retrieving"""
        if value is None:
            return None
        
        decrypted = decrypt_data(value)
        return json.loads(decrypted)


# Make EncryptedJSON mutable for SQLAlchemy tracking
MutableDict.associate_with(EncryptedJSON)


def encrypt_sensitive_fields(data: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
    """
    Encrypt specific fields in a dictionary.
    
    Args:
        data: Dictionary containing data
        fields: List of field names to encrypt
    
    Returns:
        Dictionary with encrypted fields
    """
    result = data.copy()
    
    for field in fields:
        if field in result and result[field] is not None:
            if isinstance(result[field], str):
                result[field] = encrypt_data(result[field])
            else:
                # Convert to JSON string before encrypting
                result[field] = encrypt_data(json.dumps(result[field]))
    
    return result


def decrypt_sensitive_fields(data: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
    """
    Decrypt specific fields in a dictionary.
    
    Args:
        data: Dictionary containing encrypted data
        fields: List of field names to decrypt
    
    Returns:
        Dictionary with decrypted fields
    """
    result = data.copy()
    
    for field in fields:
        if field in result and result[field] is not None:
            decrypted = decrypt_data(result[field])
            
            # Try to parse as JSON
            try:
                result[field] = json.loads(decrypted)
            except (json.JSONDecodeError, TypeError):
                result[field] = decrypted
    
    return result


class EncryptionMixin:
    """Mixin for models with encrypted fields"""
    
    # Override in subclass
    ENCRYPTED_FIELDS: List[str] = []
    
    def encrypt_fields(self) -> None:
        """Encrypt sensitive fields before saving"""
        for field in self.ENCRYPTED_FIELDS:
            if hasattr(self, field):
                value = getattr(self, field)
                if value is not None:
                    if isinstance(value, str):
                        setattr(self, field, encrypt_data(value))
                    else:
                        setattr(self, field, encrypt_data(json.dumps(value)))
    
    def decrypt_fields(self) -> None:
        """Decrypt sensitive fields after loading"""
        for field in self.ENCRYPTED_FIELDS:
            if hasattr(self, field):
                value = getattr(self, field)
                if value is not None:
                    decrypted = decrypt_data(value)
                    try:
                        setattr(self, field, json.loads(decrypted))
                    except (json.JSONDecodeError, TypeError):
                        setattr(self, field, decrypted)
    
    def to_dict(self, include_encrypted: bool = False) -> Dict[str, Any]:
        """
        Convert model to dictionary.
        
        Args:
            include_encrypted: Whether to include encrypted fields in decrypted form
        
        Returns:
            Dictionary representation of the model
        """
        result = {}
        
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            
            if column.name in self.ENCRYPTED_FIELDS and not include_encrypted:
                # Skip encrypted fields unless explicitly requested
                continue
            
            if column.name in self.ENCRYPTED_FIELDS and include_encrypted and value is not None:
                # Decrypt the field for output
                decrypted = decrypt_data(value)
                try:
                    value = json.loads(decrypted)
                except (json.JSONDecodeError, TypeError):
                    value = decrypted
            
            result[column.name] = value
        
        return result


def mask_sensitive_data(data: str, mask_char: str = "*", visible_chars: int = 4) -> str:
    """
    Mask sensitive data for display.
    
    Args:
        data: Data to mask
        mask_char: Character to use for masking
        visible_chars: Number of characters to leave visible at the end
    
    Returns:
        Masked string
    """
    if not data or len(data) <= visible_chars:
        return data
    
    masked_length = len(data) - visible_chars
    return mask_char * masked_length + data[-visible_chars:]


def hash_sensitive_data(data: str) -> str:
    """
    Create a one-way hash of sensitive data for comparison.
    
    Args:
        data: Data to hash
    
    Returns:
        Hashed string
    """
    import hashlib
    return hashlib.sha256(data.encode()).hexdigest()