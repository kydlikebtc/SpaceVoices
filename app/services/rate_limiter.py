from typing import Dict, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class RateLimitError(Exception):
    """Custom exception for rate limit errors."""
    pass

class RateLimiter:
    """Service for rate limiting API requests."""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 900):
        """
        Initialize rate limiter with configurable limits.
        
        Args:
            max_requests: Maximum number of requests allowed in the window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[datetime]] = {}
    
    async def check_rate_limit(self, key: str) -> bool:
        """
        Check if a request is allowed under current rate limits.
        
        Args:
            key: Identifier for the rate limit bucket
            
        Returns:
            bool: True if request is allowed, False if rate limit exceeded
        """
        now = datetime.now()
        window_start = now - timedelta(seconds=self.window_seconds)
        
        # Initialize request list for new keys
        if key not in self.requests:
            self.requests[key] = []
        
        # Clean up expired timestamps
        self.requests[key] = [t for t in self.requests[key] if t > window_start]
        
        # Check if rate limit is exceeded
        if len(self.requests[key]) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for {key}: {len(self.requests[key])} requests in {self.window_seconds}s")
            return False
        
        # Record the request
        self.requests[key].append(now)
        return True
    
    def get_remaining_requests(self, key: str) -> int:
        """Get number of remaining requests allowed for a key."""
        if key not in self.requests:
            return self.max_requests
        
        now = datetime.now()
        window_start = now - timedelta(seconds=self.window_seconds)
        valid_requests = [t for t in self.requests[key] if t > window_start]
        
        return max(0, self.max_requests - len(valid_requests))
    
    def get_reset_time(self, key: str) -> datetime:
        """Get time when the rate limit will reset for a key."""
        if key not in self.requests or not self.requests[key]:
            return datetime.now()
        
        oldest_request = min(self.requests[key])
        return oldest_request + timedelta(seconds=self.window_seconds)
