
import time
import logging
import os
import sys
from datetime import datetime

# Path Setup
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(root_dir, 'src'))
sys.path.insert(0, root_dir)

# Mock Streamlit for standalone execution
import unittest.mock
st_mock = unittest.mock.MagicMock()
st_mock.session_state = {}
sys.modules['streamlit'] = st_mock
sys.modules['streamlit.components.v1'] = unittest.mock.MagicMock()

from src.email.attachment_manager import AttachmentManager
from src.database.database_manager import get_db_manager
from src.config import Config

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(root_dir, 'data', 'email_worker.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("EmailWorker")

class EmailWorker:
    """Background worker to synchronize emails and process attachments."""
    
    def __init__(self, interval_seconds: int = 900): # Default 15 mins
        self.interval = interval_seconds
        self.manager = AttachmentManager()
        self.db = get_db_manager()
        
    def run(self):
        """Main loop for the worker."""
        logger.info(f"🚀 Email Worker started. Interval: {self.interval}s")
        
        while True:
            try:
                self.process_all_clients()
            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
            
            logger.info(f"💤 Sleeping for {self.interval}s...")
            time.sleep(self.interval)
            
    def process_all_clients(self):
        """Fetching emails for all active clients in the database."""
        logger.info("📅 Starting periodic sync...")
        
        # In a real multi-tenant app, we'd iterate over all clients
        # For now, we use the configured account from secrets
        client_email = Config.get('IMAP_USERNAME') or Config.get('email', {}).get('username')
        
        if not client_email:
            logger.warning("No client email configured for sync.")
            return
            
        logger.info(f"🔄 Syncing emails for {client_email}...")
        result = self.manager.sync_emails(client_email)
        
        if result.get('success'):
            logger.info(f"✅ Sync complete: {result.get('message')}")
        else:
            logger.error(f"❌ Sync failed: {result.get('message')}")

if __name__ == "__main__":
    # Create data dir if missing
    os.makedirs(os.path.join(root_dir, 'data'), exist_ok=True)
    
    # Run worker (15 minutes interval)
    worker = EmailWorker(interval_seconds=900)
    worker.run()
