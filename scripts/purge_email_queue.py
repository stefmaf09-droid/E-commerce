#!/usr/bin/env python3
"""
Script to purge pending emails (status requests, warnings, formal notices).
This script uses the FollowUpManager to identify and process claims requiring follow-up.
"""

import os
import sys
import logging
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.automation.follow_up_manager import FollowUpManager
from src.workers.task_queue import TaskQueue
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_env():
    """Verify essential environment variables."""
    load_dotenv()
    
    sender = os.getenv('GMAIL_SENDER')
    password = os.getenv('GMAIL_APP_PASSWORD')
    
    if not sender or not password:
        logger.error("❌ GMAIL credentials missing in .env file.")
        logger.error("Please add GMAIL_SENDER and GMAIL_APP_PASSWORD to your .env file.")
        return False
        
    logger.info(f"✅ GMAIL credentials found for: {sender}")
    return True

def purge_queue():
    """Process all pending follow-ups and execute queued tasks."""
    logger.info("Starting email queue refill & purge...")
    
    manager = FollowUpManager()
    queue = TaskQueue()
    
    try:
        # 1. Identify follow-ups and populate queue
        logger.info("1. Identifying needed follow-ups...")
        stats = manager.process_follow_ups()
        
        queued_count = sum(stats.values())
        if queued_count > 0:
            logger.info(f"📥 Queued {queued_count} tasks: {stats}")
        else:
            logger.info("No new follow-ups found to queue.")
            
        # 2. Process the queue
        logger.info("2. Processing Task Queue...")
        queue.process_pending_tasks(limit=50) # Process up to 50 tasks
        
        logger.info("-" * 40)
        logger.info("✅ PURGE COMPLETE")
        logger.info("-" * 40)
            
    except Exception as e:
        logger.error(f"❌ Error during purge: {e}", exc_info=True)
            
    except Exception as e:
        logger.error(f"❌ Error during purge: {e}", exc_info=True)

if __name__ == "__main__":
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Launching Email Queue Purge")
    
    if check_env():
        purge_queue()
    else:
        sys.exit(1)
