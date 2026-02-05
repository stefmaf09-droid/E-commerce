"""
Deadline Checker Cron Script

Run this script daily at 8:00 AM to check for claims approaching their response deadline (J-3).
Sends reminder notifications to clients via NotificationManager.

Schedule with Windows Task Scheduler or crontab:
    Windows: Task Scheduler -> New Task -> Run daily at 8:00 AM
    Linux: 0 8 * * * python /path/to/check_deadlines_cron.py
"""

import os
import sys
import logging
from datetime import datetime, timedelta

# Add project root to path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

from src.database.database_manager import get_db_manager
from src.notifications.notification_manager import NotificationManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_approaching_deadlines():
    """
    Check for claims with deadlines in 3 days and send reminder notifications.
    
    This function queries the database for all pending claims whose response_deadline
    is exactly 3 days from now, and sends a warning notification to the client.
    """
    logger.info("=" * 70)
    logger.info("DEADLINE CHECKER - Starting daily check")
    logger.info("=" * 70)
    
    try:
        db = get_db_manager()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Calculate target date (3 days from now)
        three_days_from_now = datetime.now() + timedelta(days=3)
        target_date = three_days_from_now.date()
        
        logger.info(f"Checking for deadlines on: {target_date.strftime('%Y-%m-%d')}")
        
        # Query claims with approaching deadlines
        cursor.execute("""
            SELECT 
                c.id,
                c.claim_reference,
                c.carrier,
                c.response_deadline,
                cl.email as client_email
            FROM claims c
            JOIN clients cl ON c.client_id = cl.id
            WHERE DATE(c.response_deadline) = ?
            AND c.status IN ('pending', 'submitted')
        """, (target_date,))
        
        approaching_claims = cursor.fetchall()
        conn.close()
        
        logger.info(f"Found {len(approaching_claims)} claims with approaching deadlines")
        
        if not approaching_claims:
            logger.info("No claims found approaching their deadline today.")
            return 0
        
        # Send notifications
        notification_mgr = NotificationManager()
        sent_count = 0
        
        for claim in approaching_claims:
            claim_id, claim_ref, carrier, deadline, client_email = claim
            
            try:
                # Format deadline date
                if isinstance(deadline, str):
                    deadline_date = datetime.fromisoformat(deadline).strftime('%d/%m/%Y')
                else:
                    deadline_date = deadline.strftime('%d/%m/%Y')
                
                # Queue notification
                success = notification_mgr.queue_notification(
                    client_email=client_email,
                    event_type='deadline_warning',
                    context={
                        'claim_ref': claim_ref,
                        'carrier': carrier,
                        'days_remaining': 3,
                        'deadline_date': deadline_date
                    }
                )
                
                if success:
                    sent_count += 1
                    logger.info(f"✅ Notification queued: {claim_ref} -> {client_email}")
                else:
                    logger.warning(f"⚠️ Notification blocked by preferences: {claim_ref}")
                    
            except Exception as e:
                logger.error(f"❌ Failed to send notification for {claim_ref}: {e}")
        
        logger.info("=" * 70)
        logger.info(f"COMPLETE: {sent_count}/{len(approaching_claims)} notifications sent")
        logger.info("=" * 70)
        
        return sent_count
        
    except Exception as e:
        logger.error(f"❌ Deadline checker failed: {e}")
        return 0


if __name__ == "__main__":
    print("\n🔔 Deadline Checker - Starting...\n")
    
    sent_count = check_approaching_deadlines()
    
    print(f"\n✅ Done! {sent_count} deadline warnings sent.\n")
    
    sys.exit(0)
