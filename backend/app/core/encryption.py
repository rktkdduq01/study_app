"""
Advanced encryption and data protection system
"""
from typing import Optional, Dict, Any, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import secrets
import hashlib
import json
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class EncryptionService:
    """Advanced encryption service for sensitive data"""
    
    def __init__(self):
        self.fernet = Fernet(settings.ENCRYPTION_KEY.encode())
        self._key_rotation_schedule = timedelta(days=90)
        self._last_rotation = datetime.utcnow()
        
    def encrypt_field(self, data: Union[str, dict, list]) -> str:
        """Encrypt a field value"""
        try:
            # Convert to JSON if not string
            if not isinstance(data, str):
                data = json.dumps(data)
            
            # Encrypt data
            encrypted = self.fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            raise
    
    def decrypt_field(self, encrypted_data: str) -> Union[str, dict, list]:
        """Decrypt a field value"""
        try:
            # Decode base64
            encrypted = base64.urlsafe_b64decode(encrypted_data.encode())
            
            # Decrypt data
            decrypted = self.fernet.decrypt(encrypted).decode()
            
            # Try to parse as JSON
            try:
                return json.loads(decrypted)
            except:
                return decrypted
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            raise
    
    def generate_key_pair(self) -> Dict[str, str]:
        """Generate RSA key pair for asymmetric encryption"""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        public_key = private_key.public_key()
        
        # Serialize keys
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return {
            "private_key": private_pem.decode(),
            "public_key": public_pem.decode()
        }
    
    def encrypt_with_public_key(self, data: str, public_key_pem: str) -> str:
        """Encrypt data with RSA public key"""
        public_key = serialization.load_pem_public_key(
            public_key_pem.encode(),
            backend=default_backend()
        )
        
        # Encrypt data
        encrypted = public_key.encrypt(
            data.encode(),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return base64.b64encode(encrypted).decode()
    
    def decrypt_with_private_key(self, encrypted_data: str, private_key_pem: str) -> str:
        """Decrypt data with RSA private key"""
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode(),
            password=None,
            backend=default_backend()
        )
        
        # Decode and decrypt
        encrypted = base64.b64decode(encrypted_data.encode())
        decrypted = private_key.decrypt(
            encrypted,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return decrypted.decode()
    
    def derive_key_from_password(self, password: str, salt: Optional[bytes] = None) -> Dict[str, str]:
        """Derive encryption key from password using PBKDF2"""
        if salt is None:
            salt = secrets.token_bytes(32)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        
        return {
            "key": key.decode(),
            "salt": base64.b64encode(salt).decode()
        }
    
    def hash_sensitive_data(self, data: str) -> str:
        """Create secure hash of sensitive data for comparison"""
        # Add salt to prevent rainbow table attacks
        salt = settings.SECRET_KEY
        return hashlib.sha256(f"{salt}{data}".encode()).hexdigest()
    
    def mask_sensitive_field(self, value: str, visible_chars: int = 4) -> str:
        """Mask sensitive field showing only few characters"""
        if not value or len(value) <= visible_chars:
            return "*" * len(value) if value else ""
        
        if visible_chars == 0:
            return "*" * len(value)
        
        # Show first and last characters
        mask_length = len(value) - visible_chars
        if visible_chars >= 2:
            start = visible_chars // 2
            end = visible_chars - start
            return value[:start] + "*" * mask_length + value[-end:]
        else:
            return value[:visible_chars] + "*" * mask_length
    
    def encrypt_pii(self, pii_data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt personally identifiable information"""
        encrypted_data = {}
        
        # Fields that should be encrypted
        pii_fields = [
            'ssn', 'social_security_number',
            'driver_license', 'passport_number',
            'bank_account', 'credit_card',
            'medical_record', 'health_insurance',
            'email', 'phone_number',
            'date_of_birth', 'address'
        ]
        
        for key, value in pii_data.items():
            if key.lower() in pii_fields and value:
                encrypted_data[key] = self.encrypt_field(str(value))
                encrypted_data[f"{key}_masked"] = self.mask_sensitive_field(str(value))
            else:
                encrypted_data[key] = value
        
        return encrypted_data
    
    def tokenize_sensitive_data(self, data: str) -> str:
        """Create a token for sensitive data that can be used as reference"""
        # Generate unique token
        token = secrets.token_urlsafe(32)
        
        # Store mapping in secure storage (Redis with encryption)
        # In production, this should be stored in a secure vault
        # For now, we'll return a hash-based token
        data_hash = self.hash_sensitive_data(data)
        return f"tok_{data_hash[:16]}_{token[:16]}"
    
    def check_encryption_health(self) -> Dict[str, Any]:
        """Check encryption service health"""
        health = {
            "status": "healthy",
            "key_age_days": (datetime.utcnow() - self._last_rotation).days,
            "rotation_due": False,
            "algorithm": "Fernet (AES-128)",
            "tests_passed": True
        }
        
        # Check if key rotation is due
        if health["key_age_days"] >= self._key_rotation_schedule.days:
            health["rotation_due"] = True
            health["status"] = "warning"
        
        # Test encryption/decryption
        try:
            test_data = "encryption_health_check"
            encrypted = self.encrypt_field(test_data)
            decrypted = self.decrypt_field(encrypted)
            if decrypted != test_data:
                health["tests_passed"] = False
                health["status"] = "unhealthy"
        except:
            health["tests_passed"] = False
            health["status"] = "unhealthy"
        
        return health


# Global encryption service instance
encryption_service = EncryptionService()


class DataMasking:
    """Data masking utilities for logs and responses"""
    
    @staticmethod
    def mask_email(email: str) -> str:
        """Mask email address"""
        if '@' not in email:
            return "***"
        
        local, domain = email.split('@', 1)
        if len(local) <= 3:
            masked_local = "*" * len(local)
        else:
            masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
        
        return f"{masked_local}@{domain}"
    
    @staticmethod
    def mask_phone(phone: str) -> str:
        """Mask phone number"""
        # Remove non-digits
        digits = ''.join(filter(str.isdigit, phone))
        
        if len(digits) <= 4:
            return "*" * len(digits)
        
        # Show last 4 digits
        return "*" * (len(digits) - 4) + digits[-4:]
    
    @staticmethod
    def mask_credit_card(card_number: str) -> str:
        """Mask credit card number"""
        # Remove spaces and non-digits
        digits = ''.join(filter(str.isdigit, card_number))
        
        if len(digits) < 12:
            return "*" * len(digits)
        
        # Show first 6 and last 4 digits (BIN and last 4)
        return digits[:6] + "*" * (len(digits) - 10) + digits[-4:]
    
    @staticmethod
    def mask_dict(data: Dict[str, Any], fields_to_mask: list) -> Dict[str, Any]:
        """Mask specific fields in dictionary"""
        masked_data = data.copy()
        
        for field in fields_to_mask:
            if field in masked_data and masked_data[field]:
                value = str(masked_data[field])
                
                # Determine masking based on field name
                if 'email' in field.lower():
                    masked_data[field] = DataMasking.mask_email(value)
                elif 'phone' in field.lower():
                    masked_data[field] = DataMasking.mask_phone(value)
                elif 'card' in field.lower() or 'credit' in field.lower():
                    masked_data[field] = DataMasking.mask_credit_card(value)
                else:
                    # Generic masking
                    masked_data[field] = encryption_service.mask_sensitive_field(value)
        
        return masked_data