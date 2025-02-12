import pytest
from unittest.mock import patch
from app.services.feature_flags import FeatureFlags

@pytest.fixture
def feature_flags():
    return FeatureFlags()

def test_default_flags(feature_flags):
    """Test that default flags are set correctly."""
    assert feature_flags.is_enabled("enable_nlp_optimization") == True
    assert feature_flags.is_enabled("enable_real_time_monitoring") == True
    assert feature_flags.is_enabled("enable_rate_limiting") == True
    assert feature_flags.is_enabled("enable_heartbeat") == True
    assert feature_flags.is_enabled("enable_resource_monitoring") == True

def test_unknown_flag(feature_flags):
    """Test behavior with unknown flag."""
    assert feature_flags.is_enabled("nonexistent_flag") == False

def test_parse_bool_env():
    """Test boolean parsing from environment variables."""
    assert FeatureFlags._parse_bool_env("TEST_KEY", True) == True  # Default
    assert FeatureFlags._parse_bool_env("TEST_KEY", False) == False  # Default
    
    with patch.dict('os.environ', {'TEST_KEY': 'true'}):
        assert FeatureFlags._parse_bool_env("TEST_KEY", False) == True
    
    with patch.dict('os.environ', {'TEST_KEY': '1'}):
        assert FeatureFlags._parse_bool_env("TEST_KEY", False) == True
    
    with patch.dict('os.environ', {'TEST_KEY': 'false'}):
        assert FeatureFlags._parse_bool_env("TEST_KEY", True) == False
    
    with patch.dict('os.environ', {'TEST_KEY': '0'}):
        assert FeatureFlags._parse_bool_env("TEST_KEY", True) == False

def test_get_all_flags(feature_flags):
    """Test getting all feature flags."""
    flags = feature_flags.get_all_flags()
    assert isinstance(flags, dict)
    assert "enable_nlp_optimization" in flags
    assert "enable_real_time_monitoring" in flags
    assert "enable_rate_limiting" in flags
    assert "enable_heartbeat" in flags
    assert "enable_resource_monitoring" in flags

def test_environment_override():
    """Test environment variable override of defaults."""
    with patch.dict('os.environ', {
        'ENABLE_NLP_OPTIMIZATION': 'false',
        'ENABLE_REAL_TIME_MONITORING': '0',
        'ENABLE_RATE_LIMITING': 'off'
    }):
        flags = FeatureFlags()
        assert flags.is_enabled("enable_nlp_optimization") == False
        assert flags.is_enabled("enable_real_time_monitoring") == False
        assert flags.is_enabled("enable_rate_limiting") == False
