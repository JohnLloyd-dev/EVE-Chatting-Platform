"""
Advanced Encryption Manager
Provides comprehensive encryption and data protection capabilities
"""

import os
import base64
import hashlib
import secrets
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Union, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hmac
import logging

# Configure logging
encryption_logger = logging.getLogger("encryption_manager")
encryption_logger.setLevel(logging.INFO)

class AdvancedEncryptionManager:
    """Advanced encryption manager with multiple encryption methods"""
    
    def __init__(self, master_key: Optional[str] = None):
        self.master_key = master_key or self.generate_master_key()
        self.key_derivation_salt = os.urandom(16)
        self.encryption_keys: Dict[str, bytes] = {}
        self.key_rotation_schedule: Dict[str, datetime] = {}
        
        # Initialize encryption components
        self.symmetric_cipher = self._create_symmetric_cipher()
        self.asymmetric_keys = self._create_asymmetric_keys()
        self.hmac_key = self._create_hmac_key()
    
    def generate_master_key(self) -> str:
        """Generate a cryptographically secure master key"""
        return base64.urlsafe_b64encode(os.urandom(32)).decode()
    
    def _create_symmetric_cipher(self) -> Fernet:
        """Create symmetric encryption cipher"""
        key = self._derive_key("symmetric", 32)
        return Fernet(base64.urlsafe_b64encode(key))
    
    def _create_asymmetric_keys(self) -> Dict[str, Any]:
        """Create asymmetric encryption key pair"""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        public_key = private_key.public_key()
        
        return {
            "private_key": private_key,
            "public_key": public_key
        }
    
    def _create_hmac_key(self) -> bytes:
        """Create HMAC key for integrity verification"""
        return self._derive_key("hmac", 32)
    
    def _derive_key(self, purpose: str, key_length: int) -> bytes:
        """Derive encryption key from master key"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=key_length,
            salt=self.key_derivation_salt,
            iterations=100000,
        )
        return kdf.derive(f"{self.master_key}:{purpose}".encode())
    
    def encrypt_symmetric(self, data: Union[str, bytes], purpose: str = "general") -> str:
        """Encrypt data using symmetric encryption"""
        try:
            if isinstance(data, str):
                data = data.encode()
            
            # Add purpose and timestamp for additional security
            metadata = {
                "purpose": purpose,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "version": "1.0"
            }
            
            # Combine data with metadata
            combined_data = json.dumps({
                "data": base64.b64encode(data).decode(),
                "metadata": metadata
            }).encode()
            
            # Encrypt
            encrypted_data = self.symmetric_cipher.encrypt(combined_data)
            
            # Add HMAC for integrity
            h = hmac.HMAC(self.hmac_key, hashes.SHA256())
            h.update(encrypted_data)
            hmac_value = h.finalize()
            
            # Combine encrypted data with HMAC
            result = base64.urlsafe_b64encode(encrypted_data + hmac_value).decode()
            
            encryption_logger.info(f"Data encrypted successfully with purpose: {purpose}")
            return result
            
        except Exception as e:
            encryption_logger.error(f"Symmetric encryption failed: {str(e)}")
            raise
    
    def decrypt_symmetric(self, encrypted_data: str) -> str:
        """Decrypt data using symmetric encryption"""
        try:
            # Decode from base64
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            
            # Separate HMAC from encrypted data
            hmac_length = 32  # SHA256 HMAC length
            encrypted_part = encrypted_bytes[:-hmac_length]
            received_hmac = encrypted_bytes[-hmac_length:]
            
            # Verify HMAC
            h = hmac.HMAC(self.hmac_key, hashes.SHA256())
            h.update(encrypted_part)
            expected_hmac = h.finalize()
            
            if not hmac.compare_digest(received_hmac, expected_hmac):
                raise ValueError("HMAC verification failed - data integrity compromised")
            
            # Decrypt
            decrypted_data = self.symmetric_cipher.decrypt(encrypted_part)
            
            # Parse metadata and data
            parsed = json.loads(decrypted_data.decode())
            original_data = base64.b64decode(parsed["data"])
            
            encryption_logger.info(f"Data decrypted successfully with purpose: {parsed['metadata']['purpose']}")
            return original_data.decode()
            
        except Exception as e:
            encryption_logger.error(f"Symmetric decryption failed: {str(e)}")
            raise
    
    def encrypt_asymmetric(self, data: Union[str, bytes]) -> str:
        """Encrypt data using asymmetric encryption"""
        try:
            if isinstance(data, str):
                data = data.encode()
            
            # Encrypt with public key
            encrypted = self.asymmetric_keys["public_key"].encrypt(
                data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            result = base64.urlsafe_b64encode(encrypted).decode()
            encryption_logger.info("Data encrypted successfully with asymmetric encryption")
            return result
            
        except Exception as e:
            encryption_logger.error(f"Asymmetric encryption failed: {str(e)}")
            raise
    
    def decrypt_asymmetric(self, encrypted_data: str) -> str:
        """Decrypt data using asymmetric encryption"""
        try:
            # Decode from base64
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            
            # Decrypt with private key
            decrypted = self.asymmetric_keys["private_key"].decrypt(
                encrypted_bytes,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            encryption_logger.info("Data decrypted successfully with asymmetric encryption")
            return decrypted.decode()
            
        except Exception as e:
            encryption_logger.error(f"Asymmetric decryption failed: {str(e)}")
            raise
    
    def encrypt_field(self, field_value: str, field_name: str) -> str:
        """Encrypt a specific field with field-specific encryption"""
        try:
            # Create field-specific key
            field_key = self._derive_key(f"field:{field_name}", 32)
            field_cipher = Fernet(base64.urlsafe_b64encode(field_key))
            
            # Add field metadata
            metadata = {
                "field_name": field_name,
                "encrypted_at": datetime.now(timezone.utc).isoformat(),
                "encryption_type": "field_specific"
            }
            
            # Combine data with metadata
            combined_data = json.dumps({
                "value": field_value,
                "metadata": metadata
            }).encode()
            
            # Encrypt
            encrypted_data = field_cipher.encrypt(combined_data)
            result = base64.urlsafe_b64encode(encrypted_data).decode()
            
            encryption_logger.info(f"Field '{field_name}' encrypted successfully")
            return result
            
        except Exception as e:
            encryption_logger.error(f"Field encryption failed for '{field_name}': {str(e)}")
            raise
    
    def decrypt_field(self, encrypted_field: str, field_name: str) -> str:
        """Decrypt a specific field"""
        try:
            # Create field-specific key
            field_key = self._derive_key(f"field:{field_name}", 32)
            field_cipher = Fernet(base64.urlsafe_b64encode(field_key))
            
            # Decode and decrypt
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_field.encode())
            decrypted_data = field_cipher.decrypt(encrypted_bytes)
            
            # Parse data
            parsed = json.loads(decrypted_data.decode())
            
            encryption_logger.info(f"Field '{field_name}' decrypted successfully")
            return parsed["value"]
            
        except Exception as e:
            encryption_logger.error(f"Field decryption failed for '{field_name}': {str(e)}")
            raise
    
    def hash_password(self, password: str, salt: Optional[str] = None) -> Dict[str, str]:
        """Hash password with salt using PBKDF2"""
        try:
            if salt is None:
                salt = base64.b64encode(os.urandom(16)).decode()
            
            # Use PBKDF2 for password hashing
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=base64.b64decode(salt),
                iterations=100000,
            )
            
            hash_value = kdf.derive(password.encode())
            hash_b64 = base64.b64encode(hash_value).decode()
            
            return {
                "hash": hash_b64,
                "salt": salt,
                "algorithm": "PBKDF2-SHA256",
                "iterations": 100000
            }
            
        except Exception as e:
            encryption_logger.error(f"Password hashing failed: {str(e)}")
            raise
    
    def verify_password(self, password: str, stored_hash: str, salt: str) -> bool:
        """Verify password against stored hash"""
        try:
            # Recreate hash with same parameters
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=base64.b64decode(salt),
                iterations=100000,
            )
            
            hash_value = kdf.derive(password.encode())
            hash_b64 = base64.b64encode(hash_value).decode()
            
            return hash_b64 == stored_hash
            
        except Exception as e:
            encryption_logger.error(f"Password verification failed: {str(e)}")
            return False
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate a cryptographically secure token"""
        return secrets.token_urlsafe(length)
    
    def generate_secure_id(self) -> str:
        """Generate a secure UUID-like identifier"""
        return secrets.token_urlsafe(16)
    
    def encrypt_sensitive_data(self, data: Dict[str, Any], sensitive_fields: List[str]) -> Dict[str, Any]:
        """Encrypt sensitive fields in a data dictionary"""
        try:
            encrypted_data = data.copy()
            
            for field in sensitive_fields:
                if field in encrypted_data and encrypted_data[field]:
                    encrypted_data[field] = self.encrypt_field(
                        str(encrypted_data[field]), 
                        field
                    )
            
            encryption_logger.info(f"Encrypted {len(sensitive_fields)} sensitive fields")
            return encrypted_data
            
        except Exception as e:
            encryption_logger.error(f"Sensitive data encryption failed: {str(e)}")
            raise
    
    def decrypt_sensitive_data(self, data: Dict[str, Any], sensitive_fields: List[str]) -> Dict[str, Any]:
        """Decrypt sensitive fields in a data dictionary"""
        try:
            decrypted_data = data.copy()
            
            for field in sensitive_fields:
                if field in decrypted_data and decrypted_data[field]:
                    decrypted_data[field] = self.decrypt_field(
                        decrypted_data[field], 
                        field
                    )
            
            encryption_logger.info(f"Decrypted {len(sensitive_fields)} sensitive fields")
            return decrypted_data
            
        except Exception as e:
            encryption_logger.error(f"Sensitive data decryption failed: {str(e)}")
            raise
    
    def rotate_keys(self) -> Dict[str, str]:
        """Rotate encryption keys"""
        try:
            old_master_key = self.master_key
            self.master_key = self.generate_master_key()
            
            # Recreate encryption components with new key
            self.symmetric_cipher = self._create_symmetric_cipher()
            self.hmac_key = self._create_hmac_key()
            
            # Update rotation schedule
            self.key_rotation_schedule["last_rotation"] = datetime.now(timezone.utc).isoformat()
            
            encryption_logger.info("Encryption keys rotated successfully")
            
            return {
                "old_master_key": old_master_key,
                "new_master_key": self.master_key,
                "rotation_time": self.key_rotation_schedule["last_rotation"]
            }
            
        except Exception as e:
            encryption_logger.error(f"Key rotation failed: {str(e)}")
            raise
    
    def get_encryption_status(self) -> Dict[str, Any]:
        """Get encryption system status"""
        return {
            "master_key_exists": bool(self.master_key),
            "symmetric_cipher_ready": bool(self.symmetric_cipher),
            "asymmetric_keys_ready": bool(self.asymmetric_keys),
            "hmac_key_ready": bool(self.hmac_key),
            "last_key_rotation": self.key_rotation_schedule.get("last_rotation"),
            "encryption_version": "2.0"
        }

# Initialize global encryption manager
encryption_manager = AdvancedEncryptionManager()

# Utility functions
def encrypt_data(data: Union[str, bytes], purpose: str = "general") -> str:
    """Encrypt data using the global encryption manager"""
    return encryption_manager.encrypt_symmetric(data, purpose)

def decrypt_data(encrypted_data: str) -> str:
    """Decrypt data using the global encryption manager"""
    return encryption_manager.decrypt_symmetric(encrypted_data)

def encrypt_field(field_value: str, field_name: str) -> str:
    """Encrypt a field using the global encryption manager"""
    return encryption_manager.encrypt_field(field_value, field_name)

def decrypt_field(encrypted_field: str, field_name: str) -> str:
    """Decrypt a field using the global encryption manager"""
    return encryption_manager.decrypt_field(encrypted_field, field_name)

def hash_password(password: str, salt: Optional[str] = None) -> Dict[str, str]:
    """Hash password using the global encryption manager"""
    return encryption_manager.hash_password(password, salt)

def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Verify password using the global encryption manager"""
    return encryption_manager.verify_password(password, stored_hash, salt)

def generate_secure_token(length: int = 32) -> str:
    """Generate secure token using the global encryption manager"""
    return encryption_manager.generate_secure_token(length)

def encrypt_sensitive_data(data: Dict[str, Any], sensitive_fields: List[str]) -> Dict[str, Any]:
    """Encrypt sensitive data using the global encryption manager"""
    return encryption_manager.encrypt_sensitive_data(data, sensitive_fields)

def decrypt_sensitive_data(data: Dict[str, Any], sensitive_fields: List[str]) -> Dict[str, Any]:
    """Decrypt sensitive data using the global encryption manager"""
    return encryption_manager.decrypt_sensitive_data(data, sensitive_fields) 