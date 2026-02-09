"""
POD Error Classifier

Distinguishes between temporary errors (will retry automatically) 
and persistent errors (require user notification).
"""

def is_persistent_pod_error(error_message: str) -> bool:
    """
    Determine if a POD fetch error is persistent and requires notification.
    
    Persistent errors (NOTIFY user):
    - Tracking number not found / invalid
    - POD document not available at carrier
    - Carrier account authentication failed (permanent)
    - Unsupported carrier
    
    Temporary errors (DON'T notify, auto-retry will handle):
    - API timeout / connection errors
    - Rate limit exceeded
    - Package not yet delivered
    - Temporary authentication issues
    
    Args:
        error_message: The error message from POD fetch attempt
        
    Returns:
        True if persistent (notify user), False if temporary (silent retry)
    """
    if not error_message:
        return False
    
    error_lower = error_message.lower()
    
    # Persistent errors - these won't resolve automatically
    persistent_keywords = [
        'not found',
        'tracking number invalid',
        'tracking not found',
        'numéro invalide',
        'numéro introuvable',
        'pod not available',
        'pod document not available',
        'pod non disponible',
        'carrier not supported',
        'transporteur non supporté',
        'authentication failed',  # Only if it's a permanent cred issue
        'invalid credentials',
        'account suspended',
        'compte suspendu'
    ]
    
    for keyword in persistent_keywords:
        if keyword in error_lower:
            return True
    
    # Temporary errors - auto-retry will fix these
    temporary_keywords = [
        'timeout',
        'connection',
        'rate limit',
        'too many requests',
        'not yet delivered',
        'pas encore livré',
        'en cours de livraison',
        'in transit',
        'temporary',
        'temporaire',
        'try again',
        'retry'
    ]
    
    for keyword in temporary_keywords:
        if keyword in error_lower:
            return False
    
    # Default: treat unknown errors as temporary (safer, avoids spam)
    return False


def get_error_severity(error_message: str) -> str:
    """
    Get error severity level for logging/analytics.
    
    Returns:
        'critical', 'warning', or 'info'
    """
    if is_persistent_pod_error(error_message):
        return 'critical'
    elif 'rate limit' in error_message.lower():
        return 'warning'
    else:
        return 'info'
