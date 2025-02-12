from typing import Dict, Any, Optional
import os
import logging
from cryptography.fernet import Fernet, InvalidToken
from base64 import b64encode

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

class ConfigService:
    """Service for secure configuration management."""
    
    def __init__(self):
        """Initialize configuration service."""
        self._init_encryption()
    
    def _init_encryption(self):
        """Initialize encryption with key from environment."""
        try:
            key = os.getenv("ENCRYPTION_KEY")
            if key:
                # Ensure key is properly padded for Fernet
                padded_key = self._pad_key(key)
                self.fernet = Fernet(padded_key)
            else:
                logger.warning("No encryption key found, running without encryption")
                self.fernet = None
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {str(e)}")
            self.fernet = None
    
    @staticmethod
    def _pad_key(key: str) -> Optional[bytes]:
        """Ensure key is properly base64-encoded and padded."""
        try:
            # Convert to bytes if string
            if isinstance(key, str):
                key = key.encode()
            
            # Key must be at least 32 bytes for security
            if len(key) < 32:
                logger.warning("Encryption key too short")
                return None
            
            # Ensure proper base64 encoding
            return b64encode(key[:32])
        except Exception as e:
            logger.error(f"Invalid encryption key format: {str(e)}")
            return None
    
    def get_encrypted(self, key: str) -> Optional[str]:
        """
        Get and decrypt a configuration value.
        
        Args:
            key: Environment variable key
            
        Returns:
            Decrypted value if encryption is enabled, raw value otherwise
        """
        try:
            value = os.getenv(key)
            if not value:
                return None
                
            if self.fernet:
                try:
                    # Try to decrypt if value is encrypted
                    decrypted = self.fernet.decrypt(value.encode())
                    return decrypted.decode()
                except Exception:
                    # If decryption fails, assume value is not encrypted
                    return value
            return value
            
        except Exception as e:
            logger.error(f"Error getting config value for {key}: {str(e)}")
            raise ConfigError(f"Failed to get config value: {str(e)}")
    
    def get_all(self, prefix: str = "") -> Dict[str, str]:
        """
        Get all configuration values with optional prefix filtering.
        
        Args:
            prefix: Optional prefix to filter environment variables
            
        Returns:
            Dictionary of configuration values
        """
        try:
            result = {}
            for key, value in os.environ.items():
                if prefix and not key.startswith(prefix):
                    continue
                if value:
                    result[key] = self.get_encrypted(key)
            return result
        except Exception as e:
            logger.error(f"Error getting config values: {str(e)}")
            raise ConfigError(f"Failed to get config values: {str(e)}")
