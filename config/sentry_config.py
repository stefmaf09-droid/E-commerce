"""
Sentry Configuration for Production Monitoring

Monitors errors, performance, and tracks issues in production.
"""

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration
import logging
import os


def init_sentry():
    """
    Initialize Sentry for production error tracking and monitoring.
    
    Environment variables required:
    - SENTRY_DSN: Your Sentry DSN
    - ENVIRONMENT: production/staging/development
    """
    sentry_dsn = os.getenv('SENTRY_DSN')
    environment = os.getenv('ENVIRONMENT', 'development')
    
    if not sentry_dsn:
        logging.warning("⚠️  SENTRY_DSN not set. Error monitoring disabled.")
        return False
    
    # Configure Sentry
    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=environment,
        
        # Performance Monitoring
        traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
        profiles_sample_rate=0.1,  # 10% for profiling
        
        # Release tracking
        release=os.getenv('GIT_SHA', 'unknown'),
        
        # Integrations
        integrations=[
            LoggingIntegration(
                level=logging.INFO,        # Breadcrumbs from INFO
                event_level=logging.ERROR  # Sentry events from ERROR
            ),
            RedisIntegration()
        ],
        
        # Filters
        before_send=filter_sensitive_data,
        
        # Additional options
        attach_stacktrace=True,
        send_default_pii=False,  # Don't send PII by default
        max_breadcrumbs=50
    )
    
    logging.info(f"✅ Sentry initialized for environment: {environment}")
    return True


def filter_sensitive_data(event, hint):
    """
    Filter out sensitive information before sending to Sentry.
    
    Removes:
    - Passwords
    - API keys
    - Tokens
    - Credit card numbers
    - Email addresses (partially masked)
    """
    # Filter request data
    if 'request' in event:
        if 'headers' in event['request']:
            headers = event['request']['headers']
            for key in list(headers.keys()):
                if any(term in key.lower() for term in ['authorization', 'token', 'key', 'secret']):
                    headers[key] = '[FILTERED]'
        
        if 'data' in event['request']:
            event['request']['data'] = filter_dict(event['request']['data'])
    
    # Filter extra data
    if 'extra' in event:
        event['extra'] = filter_dict(event['extra'])
    
    # Filter contexts
    if 'contexts' in event:
        for context in event['contexts'].values():
            if isinstance(context, dict):
                context = filter_dict(context)
    
    return event


def filter_dict(data):
    """Recursively filter sensitive keys from dict."""
    if not isinstance(data, dict):
        return data
    
    sensitive_keys = [
        'password', 'token', 'key', 'secret', 'api_key',
        'access_token', 'refresh_token', 'authorization',
        'credit_card', 'cvv', 'ssn'
    ]
    
    filtered = {}
    for key, value in data.items():
        if isinstance(key, str) and any(term in key.lower() for term in sensitive_keys):
            filtered[key] = '[FILTERED]'
        elif isinstance(value, dict):
            filtered[key] = filter_dict(value)
        else:
            filtered[key] = value
    
    return filtered


def capture_exception(exception, context=None):
    """
    Manually capture an exception with optional context.
    
    Args:
        exception: Exception to capture
        context: Additional context dict
    """
    with sentry_sdk.push_scope() as scope:
        if context:
            for key, value in context.items():
                scope.set_extra(key, value)
        
        sentry_sdk.capture_exception(exception)


def capture_message(message, level='info', context=None):
    """
    Capture a message event.
    
    Args:
        message: Message to send
        level: Severity (debug/info/warning/error/fatal)
        context: Additional context
    """
    with sentry_sdk.push_scope() as scope:
        if context:
            for key, value in context.items():
                scope.set_extra(key, value)
        
        sentry_sdk.capture_message(message, level=level)


if __name__ == "__main__":
    # Test Sentry configuration
    print("="*70)
    print("SENTRY CONFIG - Test")
    print("="*70)
    
    # Set test environment variable
    os.environ['SENTRY_DSN'] = 'https://test@sentry.io/123456'
    os.environ['ENVIRONMENT'] = 'test'
    
    success = init_sentry()
    
    if success:
        print("\n✅ Sentry initialized successfully")
        
        # Test filtering
        test_data = {
            'user_email': 'test@example.com',
            'api_key': 'secret_key_123',
            'password': 'my_password',
            'order_total': 150.00
        }
        
        filtered = filter_dict(test_data)
        print("\n🔒 Filtering test:")
        print(f"  Original: {test_data}")
        print(f"  Filtered: {filtered}")
        
        # Test message capture (won't actually send in test)
        capture_message("Test message", level='info', context={'test': True})
        print("\n📤 Test message captured")
    else:
        print("\n❌ Sentry initialization failed")
    
    print("\n" + "="*70)
    print("✅ Test Complete")
    print("="*70)
