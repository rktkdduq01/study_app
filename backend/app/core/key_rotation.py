"""
Encryption Key Rotation System
Automated key rotation for enhanced security
"""

import os
import json
import hmac
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from cryptography.fernet import Fernet, MultiFernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.exceptions import InvalidSignature
import base64
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class KeyMetadata:
    """Metadata for encryption keys"""
    key_id: str
    algorithm: str
    created_at: datetime
    expires_at: datetime
    is_active: bool
    key_version: int
    key_type: str  # 'symmetric', 'asymmetric', 'jwt'
    usage: str  # 'encryption', 'signing', 'auth'

class EncryptionKeyManager:
    """Manages encryption keys with automatic rotation"""
    
    def __init__(self, key_storage_path: str = "keys", rotation_interval_days: int = 30):
        self.key_storage_path = key_storage_path
        self.rotation_interval = timedelta(days=rotation_interval_days)
        self.keys: Dict[str, KeyMetadata] = {}
        self.active_keys: Dict[str, Any] = {}
        
        # Ensure key storage directory exists
        os.makedirs(self.key_storage_path, exist_ok=True)
        
        # Load existing keys
        self._load_keys()
        
        # Initialize default keys if none exist
        if not self.keys:
            self._initialize_default_keys()
    
    def _generate_key_id(self) -> str:
        """Generate a unique key ID"""
        return f"key_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(8)}"
    
    def _derive_key_from_password(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password using PBKDF2"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return kdf.derive(password.encode())
    
    def _encrypt_key_data(self, key_data: bytes, master_password: str) -> Tuple[bytes, bytes]:
        """Encrypt key data with master password"""
        salt = os.urandom(16)
        derived_key = self._derive_key_from_password(master_password, salt)
        fernet = Fernet(base64.urlsafe_b64encode(derived_key))
        encrypted_data = fernet.encrypt(key_data)
        return encrypted_data, salt
    
    def _decrypt_key_data(self, encrypted_data: bytes, salt: bytes, master_password: str) -> bytes:
        """Decrypt key data with master password"""
        derived_key = self._derive_key_from_password(master_password, salt)
        fernet = Fernet(base64.urlsafe_b64encode(derived_key))
        return fernet.decrypt(encrypted_data)
    
    def generate_symmetric_key(self, usage: str = "encryption") -> str:
        """Generate a new symmetric encryption key"""
        key_id = self._generate_key_id()
        key_data = Fernet.generate_key()
        
        # Create metadata
        metadata = KeyMetadata(
            key_id=key_id,
            algorithm="Fernet",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + self.rotation_interval,
            is_active=True,
            key_version=1,
            key_type="symmetric",
            usage=usage
        )
        
        # Store key
        self._store_key(key_id, key_data, metadata)
        
        logger.info(f"Generated new symmetric key: {key_id}")
        return key_id
    
    def generate_asymmetric_key_pair(self, usage: str = "signing") -> str:
        """Generate a new asymmetric key pair"""
        key_id = self._generate_key_id()
        
        # Generate RSA key pair
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
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
        
        # Store both keys
        key_data = {
            'private_key': private_pem.decode(),
            'public_key': public_pem.decode()
        }
        
        # Create metadata
        metadata = KeyMetadata(
            key_id=key_id,
            algorithm="RSA-2048",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + self.rotation_interval,
            is_active=True,
            key_version=1,
            key_type="asymmetric",
            usage=usage
        )
        
        # Store key pair
        self._store_key(key_id, json.dumps(key_data).encode(), metadata)
        
        logger.info(f"Generated new asymmetric key pair: {key_id}")
        return key_id
    
    def generate_jwt_secret(self) -> str:
        """Generate a new JWT signing secret"""
        key_id = self._generate_key_id()
        key_data = base64.urlsafe_b64encode(secrets.token_bytes(64))
        
        # Create metadata
        metadata = KeyMetadata(
            key_id=key_id,
            algorithm="HS256",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + self.rotation_interval,
            is_active=True,
            key_version=1,
            key_type="jwt",
            usage="auth"
        )
        
        # Store key
        self._store_key(key_id, key_data, metadata)
        
        logger.info(f"Generated new JWT secret: {key_id}")
        return key_id
    
    def _store_key(self, key_id: str, key_data: bytes, metadata: KeyMetadata):
        """Store key data and metadata securely"""
        # Get master password from environment or generate one
        master_password = getattr(settings, 'KEY_ENCRYPTION_PASSWORD', None)
        if not master_password:
            master_password = os.getenv('KEY_ENCRYPTION_PASSWORD', 'default-master-key-change-in-production')
            logger.warning("Using default master password - change in production!")
        
        # Encrypt key data
        encrypted_data, salt = self._encrypt_key_data(key_data, master_password)
        
        # Store encrypted key
        key_file_path = os.path.join(self.key_storage_path, f"{key_id}.key")
        with open(key_file_path, 'wb') as f:
            f.write(salt + encrypted_data)
        
        # Store metadata
        metadata_file_path = os.path.join(self.key_storage_path, f"{key_id}.metadata")
        with open(metadata_file_path, 'w') as f:
            # Convert datetime objects to ISO format for JSON serialization
            metadata_dict = asdict(metadata)
            metadata_dict['created_at'] = metadata.created_at.isoformat()
            metadata_dict['expires_at'] = metadata.expires_at.isoformat()
            json.dump(metadata_dict, f, indent=2)
        
        # Update in-memory storage
        self.keys[key_id] = metadata
        self.active_keys[key_id] = key_data
    
    def _load_keys(self):
        """Load all keys from storage"""
        if not os.path.exists(self.key_storage_path):
            return
        
        master_password = getattr(settings, 'KEY_ENCRYPTION_PASSWORD', None)
        if not master_password:
            master_password = os.getenv('KEY_ENCRYPTION_PASSWORD', 'default-master-key-change-in-production')
        
        for filename in os.listdir(self.key_storage_path):
            if filename.endswith('.metadata'):
                key_id = filename[:-9]  # Remove .metadata extension
                
                try:
                    # Load metadata
                    metadata_path = os.path.join(self.key_storage_path, filename)
                    with open(metadata_path, 'r') as f:
                        metadata_dict = json.load(f)
                    
                    # Convert ISO format back to datetime
                    metadata_dict['created_at'] = datetime.fromisoformat(metadata_dict['created_at'])
                    metadata_dict['expires_at'] = datetime.fromisoformat(metadata_dict['expires_at'])
                    metadata = KeyMetadata(**metadata_dict)
                    
                    # Load encrypted key data
                    key_path = os.path.join(self.key_storage_path, f"{key_id}.key")
                    if os.path.exists(key_path):
                        with open(key_path, 'rb') as f:
                            encrypted_key_data = f.read()
                        
                        # Extract salt and encrypted data
                        salt = encrypted_key_data[:16]
                        encrypted_data = encrypted_key_data[16:]
                        
                        # Decrypt key data
                        key_data = self._decrypt_key_data(encrypted_data, salt, master_password)
                        
                        # Store in memory
                        self.keys[key_id] = metadata
                        self.active_keys[key_id] = key_data
                        
                        logger.info(f"Loaded key: {key_id}")
                    
                except Exception as e:
                    logger.error(f"Failed to load key {key_id}: {e}")
    
    def _initialize_default_keys(self):
        """Initialize default keys for the system"""
        logger.info("Initializing default encryption keys")
        
        # Generate default symmetric key for general encryption
        self.generate_symmetric_key("general_encryption")
        
        # Generate default JWT secret
        self.generate_jwt_secret()
        
        # Generate default asymmetric key pair for signing
        self.generate_asymmetric_key_pair("document_signing")
    
    def get_active_key(self, usage: str, key_type: str = "symmetric") -> Optional[Tuple[str, Any]]:
        """Get the most recent active key for a specific usage"""
        matching_keys = [
            (key_id, metadata) for key_id, metadata in self.keys.items()
            if metadata.is_active and metadata.usage == usage and metadata.key_type == key_type
        ]
        
        if not matching_keys:
            logger.warning(f"No active {key_type} key found for usage: {usage}")
            return None
        
        # Sort by creation date (most recent first)
        matching_keys.sort(key=lambda x: x[1].created_at, reverse=True)
        key_id, metadata = matching_keys[0]
        
        return key_id, self.active_keys.get(key_id)
    
    def get_key_by_id(self, key_id: str) -> Optional[Any]:
        """Get a specific key by its ID"""
        return self.active_keys.get(key_id)
    
    def rotate_keys(self, force: bool = False) -> List[str]:
        """Rotate expired keys or force rotation of all keys"""
        rotated_keys = []
        current_time = datetime.utcnow()
        
        for key_id, metadata in list(self.keys.items()):
            should_rotate = force or (metadata.is_active and current_time >= metadata.expires_at)
            
            if should_rotate:
                logger.info(f"Rotating key: {key_id} (usage: {metadata.usage}, type: {metadata.key_type})")
                
                # Deactivate old key
                metadata.is_active = False
                
                # Generate new key of the same type and usage
                if metadata.key_type == "symmetric":
                    new_key_id = self.generate_symmetric_key(metadata.usage)
                elif metadata.key_type == "asymmetric":
                    new_key_id = self.generate_asymmetric_key_pair(metadata.usage)
                elif metadata.key_type == "jwt":
                    new_key_id = self.generate_jwt_secret()
                else:
                    logger.error(f"Unknown key type for rotation: {metadata.key_type}")
                    continue
                
                rotated_keys.append(new_key_id)
                
                # Update metadata file for old key
                self._update_key_metadata(key_id, metadata)
        
        if rotated_keys:
            logger.info(f"Rotated {len(rotated_keys)} keys: {rotated_keys}")
        
        return rotated_keys
    
    def _update_key_metadata(self, key_id: str, metadata: KeyMetadata):
        """Update metadata file for a key"""
        metadata_file_path = os.path.join(self.key_storage_path, f"{key_id}.metadata")
        with open(metadata_file_path, 'w') as f:
            metadata_dict = asdict(metadata)
            metadata_dict['created_at'] = metadata.created_at.isoformat()
            metadata_dict['expires_at'] = metadata.expires_at.isoformat()
            json.dump(metadata_dict, f, indent=2)
    
    def cleanup_expired_keys(self, grace_period_days: int = 7) -> List[str]:
        """Clean up expired keys after grace period"""
        cleaned_keys = []
        grace_period = timedelta(days=grace_period_days)
        cutoff_time = datetime.utcnow() - grace_period
        
        for key_id, metadata in list(self.keys.items()):
            if not metadata.is_active and metadata.expires_at < cutoff_time:
                logger.info(f"Cleaning up expired key: {key_id}")
                
                # Remove files
                key_file = os.path.join(self.key_storage_path, f"{key_id}.key")
                metadata_file = os.path.join(self.key_storage_path, f"{key_id}.metadata")
                
                try:
                    if os.path.exists(key_file):
                        os.remove(key_file)
                    if os.path.exists(metadata_file):
                        os.remove(metadata_file)
                    
                    # Remove from memory
                    del self.keys[key_id]
                    if key_id in self.active_keys:
                        del self.active_keys[key_id]
                    
                    cleaned_keys.append(key_id)
                    
                except Exception as e:
                    logger.error(f"Failed to clean up key {key_id}: {e}")
        
        if cleaned_keys:
            logger.info(f"Cleaned up {len(cleaned_keys)} expired keys")
        
        return cleaned_keys
    
    def get_key_status(self) -> Dict[str, Any]:
        """Get status of all keys"""
        status = {
            "total_keys": len(self.keys),
            "active_keys": len([k for k in self.keys.values() if k.is_active]),
            "expired_keys": len([k for k in self.keys.values() if not k.is_active]),
            "keys_by_type": {},
            "keys_by_usage": {},
            "next_rotation": None
        }
        
        # Count by type and usage
        for metadata in self.keys.values():
            # By type
            if metadata.key_type not in status["keys_by_type"]:
                status["keys_by_type"][metadata.key_type] = {"active": 0, "expired": 0}
            if metadata.is_active:
                status["keys_by_type"][metadata.key_type]["active"] += 1
            else:
                status["keys_by_type"][metadata.key_type]["expired"] += 1
            
            # By usage
            if metadata.usage not in status["keys_by_usage"]:
                status["keys_by_usage"][metadata.usage] = {"active": 0, "expired": 0}
            if metadata.is_active:
                status["keys_by_usage"][metadata.usage]["active"] += 1
            else:
                status["keys_by_usage"][metadata.usage]["expired"] += 1
        
        # Find next rotation time
        active_expiry_times = [
            metadata.expires_at for metadata in self.keys.values() 
            if metadata.is_active
        ]
        if active_expiry_times:
            status["next_rotation"] = min(active_expiry_times).isoformat()
        
        return status

class EncryptionService:
    """High-level encryption service using key rotation manager"""
    
    def __init__(self, key_manager: EncryptionKeyManager):
        self.key_manager = key_manager
    
    def encrypt_data(self, data: str, usage: str = "general_encryption") -> str:
        """Encrypt data using the current active key"""
        key_info = self.key_manager.get_active_key(usage, "symmetric")
        if not key_info:
            raise ValueError(f"No active encryption key found for usage: {usage}")
        
        key_id, key_data = key_info
        fernet = Fernet(key_data)
        encrypted_data = fernet.encrypt(data.encode())
        
        # Prepend key ID for later decryption
        return f"{key_id}:{base64.urlsafe_b64encode(encrypted_data).decode()}"
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt data using the appropriate key"""
        if ':' not in encrypted_data:
            raise ValueError("Invalid encrypted data format")
        
        key_id, data_part = encrypted_data.split(':', 1)
        key_data = self.key_manager.get_key_by_id(key_id)
        
        if not key_data:
            raise ValueError(f"Key not found: {key_id}")
        
        fernet = Fernet(key_data)
        decrypted_data = fernet.decrypt(base64.urlsafe_b64decode(data_part))
        return decrypted_data.decode()
    
    def sign_data(self, data: str, usage: str = "document_signing") -> str:
        """Sign data using asymmetric key"""
        key_info = self.key_manager.get_active_key(usage, "asymmetric")
        if not key_info:
            raise ValueError(f"No active signing key found for usage: {usage}")
        
        key_id, key_data = key_info
        key_dict = json.loads(key_data.decode())
        
        private_key = serialization.load_pem_private_key(
            key_dict['private_key'].encode(),
            password=None
        )
        
        signature = private_key.sign(
            data.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        return f"{key_id}:{base64.urlsafe_b64encode(signature).decode()}"
    
    def verify_signature(self, data: str, signature: str) -> bool:
        """Verify data signature"""
        if ':' not in signature:
            return False
        
        key_id, sig_part = signature.split(':', 1)
        key_data = self.key_manager.get_key_by_id(key_id)
        
        if not key_data:
            return False
        
        try:
            key_dict = json.loads(key_data.decode())
            public_key = serialization.load_pem_public_key(
                key_dict['public_key'].encode()
            )
            
            signature_bytes = base64.urlsafe_b64decode(sig_part)
            
            public_key.verify(
                signature_bytes,
                data.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
            
        except (InvalidSignature, Exception):
            return False

# Global key manager instance
key_manager = EncryptionKeyManager()
encryption_service = EncryptionService(key_manager)