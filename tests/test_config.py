import pytest
from unittest.mock import patch
import os
from base64 import b64encode
from app.services.config import ConfigService, ConfigError

@pytest.fixture
def config_service():
    return ConfigService()

def test_init_without_key(config_service):
    """Test initialization without encryption key."""
    assert config_service.fernet is None

def test_init_with_key():
    """Test initialization with encryption key."""
    test_key = b64encode(b"test-key-12345678901234567890123456789012")
    with patch.dict('os.environ', {'ENCRYPTION_KEY': test_key.decode()}):
        service = ConfigService()
        assert service.fernet is not None

def test_pad_key():
    """Test key padding functionality."""
    short_key = "short-key"
    padded = ConfigService._pad_key(short_key)
    assert len(padded) >= 32  # Base64 encoding will make it longer
    assert isinstance(padded, bytes)

def test_get_encrypted_without_encryption(config_service):
    """Test getting value without encryption."""
    with patch.dict('os.environ', {'TEST_KEY': 'test-value'}):
        value = config_service.get_encrypted('TEST_KEY')
        assert value == 'test-value'

def test_get_encrypted_with_encryption():
    """Test getting encrypted value."""
    test_key = b64encode(b"test-key-12345678901234567890123456789012")
    with patch.dict('os.environ', {
        'ENCRYPTION_KEY': test_key.decode(),
        'TEST_KEY': 'test-value'
    }):
        service = ConfigService()
        value = service.get_encrypted('TEST_KEY')
        assert value == 'test-value'

def test_get_all(config_service):
    """Test getting all configuration values."""
    test_env = {
        'APP_KEY1': 'value1',
        'APP_KEY2': 'value2',
        'OTHER_KEY': 'value3'
    }
    with patch.dict('os.environ', test_env):
        # Get all values
        all_values = config_service.get_all()
        assert len(all_values) >= 3
        assert all_values['APP_KEY1'] == 'value1'
        assert all_values['APP_KEY2'] == 'value2'
        
        # Get values with prefix
        app_values = config_service.get_all('APP_')
        assert len(app_values) == 2
        assert 'OTHER_KEY' not in app_values

def test_missing_value(config_service):
    """Test behavior with missing environment variable."""
    assert config_service.get_encrypted('NONEXISTENT_KEY') is None

def test_error_handling():
    """Test error handling with invalid encryption key."""
    with patch.dict('os.environ', {'ENCRYPTION_KEY': 'invalid-key'}):
        service = ConfigService()
        assert service.fernet is None  # Should fail gracefully
