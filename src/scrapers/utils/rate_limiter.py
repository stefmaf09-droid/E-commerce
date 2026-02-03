"""
Rate limiter for respectful web scraping.

Ensures requests are spaced out to avoid overwhelming servers.
"""

import time
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple rate limiter for web scraping."""
    
    def __init__(self, requests_per_second: float = 1.0, burst: int = 1):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_second: Maximum requests per second
            burst: Number of requests allowed in burst
        """
        self.min_interval = 1.0 / requests_per_second
        self.burst = burst
        self.last_request_time = 0
        self.tokens = burst
        self.last_token_update = time.time()
    
    def wait(self):
        """Wait if necessary before making next request."""
        current_time = time.time()
        
        # Refill tokens based on time elapsed
        time_since_update = current_time - self.last_token_update
        tokens_to_add = time_since_update / self.min_interval
        self.tokens = min(self.burst, self.tokens + tokens_to_add)
        self.last_token_update = current_time
        
        # If no tokens available, wait
        if self.tokens < 1:
            wait_time = (1 - self.tokens) * self.min_interval
            logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
            time.sleep(wait_time)
            self.tokens = 1
        
        # Consume a token
        self.tokens -= 1
        self.last_request_time = current_time
    
    def __enter__(self):
        """Context manager entry."""
        self.wait()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        pass
