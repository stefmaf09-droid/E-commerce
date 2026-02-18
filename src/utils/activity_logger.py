import functools
import logging
from typing import Optional, Dict, Any
from src.database.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

class ActivityLogger:
    """Helper to log user activities to database."""
    
    @staticmethod
    def log(client_id: int, action: str, details: Dict[str, Any] = None, 
            resource_type: str = None, resource_id: int = None):
        """
        Log an action safely (swallows errors).
        """
        if not client_id:
            logger.warning(f"Anonymous activity not logged: {action}")
            return

        try:
            db = DatabaseManager()
            db.log_activity(
                client_id=client_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details
            )
        except Exception as e:
            logger.error(f"Activity logging failed: {e}")

    @staticmethod
    def wrap(action_name: str, resource_type: str = None):
        """
        Decorator to log function execution.
        Assumes the first argument is 'self' or context containing 'client_id' 
        OR functionality handles client_id retrieval from session state if available in context.
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Execute function first
                result = func(*args, **kwargs)
                
                # Try to log after success
                try:
                    import streamlit as st
                    client_id = st.session_state.get('client_id')
                    
                    # If not in session state, try to find in args (fragile, specific to context)
                    # For now, rely on session state which is common in this Streamlit app
                    
                    if client_id:
                        ActivityLogger.log(
                            client_id=int(client_id),
                            action=action_name,
                            details={'func': func.__name__},
                            resource_type=resource_type
                        )
                except Exception:
                    pass # Don't break execution for logging
                    
                return result
            return wrapper
        return decorator
