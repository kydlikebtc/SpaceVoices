import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from app.services.rate_limiter import RateLimiter

@pytest.fixture
def rate_limiter():
    return RateLimiter(max_requests=2, window_seconds=60)

@pytest.mark.asyncio
async def test_check_rate_limit_within_limits(rate_limiter):
    # First request should be allowed
    assert await rate_limiter.check_rate_limit("test_key") == True
    assert rate_limiter.get_remaining_requests("test_key") == 1
    
    # Second request should be allowed
    assert await rate_limiter.check_rate_limit("test_key") == True
    assert rate_limiter.get_remaining_requests("test_key") == 0
    
    # Third request should be denied
    assert await rate_limiter.check_rate_limit("test_key") == False
    assert rate_limiter.get_remaining_requests("test_key") == 0

@pytest.mark.asyncio
async def test_rate_limit_window_expiry(rate_limiter):
    # Mock datetime.now() to control time
    current_time = datetime.now()
    
    with patch('app.services.rate_limiter.datetime') as mock_datetime:
        # Set initial time
        mock_datetime.now.return_value = current_time
        
        # First request at t=0
        assert await rate_limiter.check_rate_limit("test_key") == True
        
        # Second request at t=0
        assert await rate_limiter.check_rate_limit("test_key") == True
        
        # Third request at t=0 should be denied
        assert await rate_limiter.check_rate_limit("test_key") == False
        
        # Move time forward past window
        mock_datetime.now.return_value = current_time + timedelta(seconds=61)
        
        # Request should be allowed after window expires
        assert await rate_limiter.check_rate_limit("test_key") == True

@pytest.mark.asyncio
async def test_multiple_keys(rate_limiter):
    # Requests for key1
    assert await rate_limiter.check_rate_limit("key1") == True
    assert await rate_limiter.check_rate_limit("key1") == True
    assert await rate_limiter.check_rate_limit("key1") == False
    
    # Requests for key2 should be independent
    assert await rate_limiter.check_rate_limit("key2") == True
    assert await rate_limiter.check_rate_limit("key2") == True
    assert await rate_limiter.check_rate_limit("key2") == False

def test_get_reset_time(rate_limiter):
    current_time = datetime.now()
    
    with patch('app.services.rate_limiter.datetime') as mock_datetime:
        mock_datetime.now.return_value = current_time
        
        # Make a request
        rate_limiter.requests["test_key"] = [current_time]
        
        # Reset time should be window_seconds after the request
        expected_reset = current_time + timedelta(seconds=60)
        assert abs((rate_limiter.get_reset_time("test_key") - expected_reset).total_seconds()) < 1
