"""
Centralized Configuration Manager for Refundly Platform.

Provides unified access to configuration values with intelligent fallbacks:
1. Environment variables (production/cloud)
2. Streamlit secrets.toml (local development)
3. Default values

Usage:
    from src.config import Config
    
    api_key = Config.get('GEMINI_API_KEY')
    db_url = Config.get('DATABASE_URL', default='sqlite:///local.db')
"""

import os
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)


class Config:
    """Centralized configuration manager with smart fallbacks."""
    
    _secrets_cache = None
    
    @classmethod
    def get(cls, key: str, default: Optional[Any] = None) -> Optional[Any]:
        """
        Retrieve a configuration value with intelligent fallback.
        
        Priority:
        1. Environment variables (os.getenv)
        2. Streamlit secrets.toml
        3. Default value
        
        Args:
            key: Configuration key name
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        # 1. Check environment variables first (production priority)
        value = os.getenv(key)
        if value is not None:
            logger.debug(f"Config '{key}' loaded from environment")
            return value
        
        # 2. Check Streamlit secrets (local dev)
        value = cls._load_from_secrets(key)
        if value is not None:
            logger.debug(f"Config '{key}' loaded from secrets.toml")
            return value
        
        # 3. Return default
        if default is not None:
            logger.debug(f"Config '{key}' using default value")
            return default
        
        logger.warning(f"Config '{key}' not found and no default provided")
        return None
    
    @classmethod
    def _load_from_secrets(cls, key: str) -> Optional[Any]:
        """Load value from Streamlit secrets.toml file."""
        # Cache secrets to avoid repeated file reads
        if cls._secrets_cache is None:
            try:
                import toml
                secrets_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    '.streamlit',
                    'secrets.toml'
                )
                
                if os.path.exists(secrets_path):
                    with open(secrets_path, 'r', encoding='utf-8') as f:
                        cls._secrets_cache = toml.load(f)
                        logger.debug("Secrets.toml loaded successfully")
                else:
                    cls._secrets_cache = {}
                    logger.debug("No secrets.toml found, using empty cache")
                    
            except Exception as e:
                logger.warning(f"Failed to load secrets.toml: {e}")
                cls._secrets_cache = {}
        
        return cls._secrets_cache.get(key)
    
    @classmethod
    def get_database_url(cls) -> str:
        """Get database URL with smart defaults."""
        db_url = cls.get('DATABASE_URL')
        if db_url:
            return db_url
        
        # Check for legacy DB_TYPE
        db_type = cls.get('DATABASE_TYPE', 'sqlite')
        if db_type == 'postgres':
            # Try to construct from individual components
            return cls.get('POSTGRES_URL', 'sqlite:///database/main.db')
        
        return 'sqlite:///database/main.db'
    
    @classmethod
    def get_supabase_config(cls) -> dict:
        """Get Supabase configuration bundle."""
        return {
            'url': cls.get('SUPABASE_URL'),
            'service_key': cls.get('SUPABASE_SERVICE_ROLE_KEY'),
            'storage_bucket': cls.get('SUPABASE_STORAGE_BUCKET', 'evidence')
        }
    
    @classmethod
    def get_gemini_api_key(cls) -> Optional[str]:
        """Get Gemini API key with multiple name variants."""
        # Try both common variants
        return (
            cls.get('GEMINI_API_KEY') or 
            cls.get('GOOGLE_API_KEY') or
            cls.get('GOOGLE_GEMINI_API_KEY')
        )
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production environment."""
        return cls.get('STREAMLIT_RUNTIME', '').lower() == 'true' or \
               cls.get('ENVIRONMENT', 'development').lower() == 'production'
    
    @classmethod
    def clear_cache(cls):
        """Clear the secrets cache (useful for testing)."""
        cls._secrets_cache = None
        logger.debug("Config cache cleared")


# Convenience functions for backward compatibility
def get_config(key: str, default: Optional[Any] = None) -> Optional[Any]:
    """Shorthand for Config.get()"""
    return Config.get(key, default)


if __name__ == "__main__":
    # Test the config manager
    print("="*70)
    print("CONFIG MANAGER - Test")
    print("="*70)
    
    print("\n1. Testing environment variable (should use env):")
    os.environ['TEST_VAR'] = 'from_environment'
    print(f"   TEST_VAR = {Config.get('TEST_VAR')}")
    
    print("\n2. Testing missing variable with default:")
    print(f"   MISSING_VAR = {Config.get('MISSING_VAR', 'default_value')}")
    
    print("\n3. Testing convenience methods:")
    print(f"   Is Production? {Config.is_production()}")
    print(f"   Gemini API Key exists? {Config.get_gemini_api_key() is not None}")
    
    print("\n" + "="*70)
    print("✅ Config Manager Operational")
    print("="*70)
