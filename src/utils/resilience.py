
import time
import logging
from functools import wraps
from typing import Callable, Any

logger = logging.getLogger(__name__)

class CircuitBreakerOpenException(Exception):
    """Exception levée quand le circuit est ouvert."""
    pass

class CircuitBreaker:
    """
    Pattern Circuit Breaker pour protéger les appels aux APIs externes.
    États : CLOSED (Normal), OPEN (Erreur détectée, on bloque), HALF_OPEN (Test de rétablissement).
    """
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"

    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            if self.state == "OPEN":
                # Vérifier si on peut passer en HALF_OPEN
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = "HALF_OPEN"
                    logger.info(f"Circuit Breaker for {func.__name__} moving to HALF_OPEN")
                else:
                    logger.warning(f"Circuit Breaker for {func.__name__} is OPEN. Blocking call.")
                    raise CircuitBreakerOpenException(f"Circuit open for {func.__name__}")

            try:
                result = func(*args, **kwargs)
                
                # Succès : Si on était en HALF_OPEN, on referme
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    self.failure_count = 0
                    logger.info(f"Circuit Breaker for {func.__name__} successfully CLOSED")
                
                return result
                
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"
                    logger.error(f"Circuit Breaker for {func.__name__} is now OPEN after {self.failure_count} failures. Error: {e}")
                
                raise e
        return wrapper
