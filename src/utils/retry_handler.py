
import time
import logging
import random
from functools import wraps
from typing import Type, Tuple, Optional, Callable

logger = logging.getLogger(__name__)

class RetryHandler:
    """
    Handles retry logic with exponential backoff for operational robustness.
    """
    
    @staticmethod
    def with_retry(
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exceptions: Tuple[Type[Exception], ...] = (Exception,),
        backoff_factor: float = 2.0,
        jitter: bool = True
    ) -> Callable:
        """
        Decorator to retry a function call upon handling specific exceptions.
        
        Args:
            max_retries (int): Maximum number of retries before giving up.
            base_delay (float): Initial delay between retries in seconds.
            max_delay (float): Maximum delay in seconds.
            exceptions (tuple): Tuple of exception types to catch and retry.
            backoff_factor (float): Multiplier for the delay after each failure.
            jitter (bool): Whether to add random jitter to the delay.
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                attempt = 0
                delay = base_delay
                
                while attempt <= max_retries:
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        attempt += 1
                        if attempt > max_retries:
                            logger.error(f"Function {func.__name__} failed after {max_retries} retries. Last error: {e}")
                            raise e
                        
                        # Calculate delay
                        current_delay = min(delay * (backoff_factor ** (attempt - 1)), max_delay)
                        
                        if jitter:
                            current_delay = current_delay * random.uniform(0.5, 1.5)
                        
                        logger.warning(
                            f"Attempt {attempt}/{max_retries} for {func.__name__} failed with {type(e).__name__}. "
                            f"Retrying in {current_delay:.2f}s..."
                        )
                        
                        time.sleep(current_delay)
                return None # Should not be reached
            return wrapper
        return decorator
