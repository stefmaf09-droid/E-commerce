
import os
import sys
import logging
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.workers.task_queue import TaskQueue
from src.workers.email_workers import execute_formal_notice
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EmailTester")

def run_test():
    # Explicitly load .env from root
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    loaded = load_dotenv(env_path)
    logger.info(f"Loading .env from {env_path}: {loaded}")
    
    # Debug config
    logger.info(f"SMTP_HOST: {os.getenv('SMTP_HOST')}")
    logger.info(f"SMTP_USER: {os.getenv('SMTP_USER')}")

    
    # 1. Configuration Check
    sender = os.getenv('SMTP_USER') or os.getenv('GMAIL_SENDER')
    pwd = os.getenv('SMTP_PASSWORD') or os.getenv('GMAIL_APP_PASSWORD')
    
    if not sender or not pwd:
        logger.error("❌ SMTP credentials missing in .env")
        return

    # Enable Test Mode
    os.environ['TEST_MODE'] = 'True'
    # Default to sender if no recipient specified
    recipient = os.getenv('TEST_EMAIL_RECIPIENT', sender)
    os.environ['TEST_EMAIL_RECIPIENT'] = recipient
    
    logger.info(f"🧪 TEST MODE ENABLED. All emails will be sent to: {recipient}")
    
    # 2. Create Dummy Claim Data
    dummy_claim = {
        'id': 99999,
        'claim_reference': 'TEST-FORMAL-001',
        'carrier': 'DHL', # Will be redirected
        'tracking_number': '1234567890',
        'amount_requested': 150.00,
        'currency': 'EUR',
        'customer_name': 'Jean Test',
        'country': 'FR',
        'location': 'Lyon',
        'client_id': 1,
        'dispute_type': 'Non-livraison', # Requis par le template
        'company_name': 'My Super Shop' # Requis par le template Refundly
    }
    
    # 3. Queue the Task
    queue = TaskQueue()
    logger.info("Queuing a test Formal Notice email...")
    queue.add_task(execute_formal_notice, dummy_claim)
    
    # 4. Process the Queue
    logger.info("Processing queue...")
    queue.process_pending_tasks()
    
    logger.info("✅ Test Complete. Check your inbox.")

if __name__ == "__main__":
    run_test()
