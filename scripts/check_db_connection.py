
import os
import sys
import psycopg2
from urllib.parse import urlparse
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_connection(url, description):
    logger.info(f"Testing {description}...")
    try:
        # Parse URL to mask password in logs
        parsed = urlparse(url)
        clean_url = f"postgres://{parsed.username}:****@{parsed.hostname}:{parsed.port}{parsed.path}"
        logger.info(f"Connecting to: {clean_url}")
        
        conn = psycopg2.connect(url, connect_timeout=5)
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        logger.info(f"✅ Success! Version: {version}")
        conn.close()
        return True
    except Exception as e:
        logger.error(f"❌ Failed: {str(e)}")
        return False


def load_secrets():
    """Load secrets from .streamlit/secrets.toml"""
    try:
        import toml
        secrets_path = os.path.join(os.path.dirname(__file__), '..', '.streamlit', 'secrets.toml')
        if os.path.exists(secrets_path):
            return toml.load(secrets_path)
    except Exception as e:
        logger.warning(f"Could not load secrets.toml: {e}")
    return {}

def main():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        secrets = load_secrets()
        # Try to find DATABASE_URL in secrets
        # Structure might be [postgres] url = ... or just plain key
        if 'postgres' in secrets and 'url' in secrets['postgres']:
             db_url = secrets['postgres']['url']
        elif 'DATABASE_URL' in secrets:
             db_url = secrets['DATABASE_URL']
        elif 'supaband' in secrets and 'url' in secrets['supaband']:
             db_url = secrets['supaband']['url']

    if not db_url:
        logger.error("DATABASE_URL not found in env or secrets.toml")
        return

    logger.info("--- Starting Database Connection Diagnostics ---")

    
    # Test 1: Standard Connection (as configured)
    logger.info("\n[Test 1] Configured Connection")
    test_connection(db_url, "Standard DATABASE_URL")

    # Test 2: Force Port 5432 (Direct)
    logger.info("\n[Test 2] Direct Connection (Port 5432)")
    try:
        parsed = urlparse(db_url)
        # Reconstruct URL with port 5432
        new_netloc = f"{parsed.username}:{parsed.password}@{parsed.hostname}:5432"
        direct_url = parsed._replace(netloc=new_netloc).geturl()
        test_connection(direct_url, "Direct Port 5432")
    except Exception as e:
        logger.error(f"Could not construct direct URL: {e}")

    logger.info("\n--- Diagnostics Complete ---")

if __name__ == "__main__":
    main()
