"""
POD Auto-Retry Scheduler

Automatically retries failed POD fetches with intelligent strategies:
- Exponential backoff (1h, 6h, 24h, 72h)
- Smart error classification (skip persistent errors)
- Rate limit awareness
- Email notifications for persistent failures only
- Comprehensive logging and monitoring

Schedule:
- Windows: schtasks /create /tn "PODRetryScheduler" /tr "python D:\\Recours_Ecommerce\\scripts\\pod_retry_scheduler.py" /sc hourly /mo 1
- Linux: 0 */1 * * * cd /path/to/Recours_Ecommerce && python scripts/pod_retry_scheduler.py

Usage:
    python scripts/pod_retry_scheduler.py
    
    # With custom settings
    python scripts/pod_retry_scheduler.py --batch-size 30 --max-retries 4
"""

import os
import sys
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict

# Add project to path
root_dir = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(root_dir))

from src.database.database_manager import get_db_manager
from src.integrations.pod_fetcher import PODFetcher
from src.integrations.api_request_queue import APIRequestQueue
from src.integrations.pod_error_classifier import is_persistent_pod_error
from src.notifications.notification_manager import NotificationManager
from src.utils.i18n import get_browser_language, get_i18n_text

# Create logs directory
(root_dir / 'logs').mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler(root_dir / 'logs' / 'pod_retry_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PODRetryScheduler:
    """
    Intelligent POD retry scheduler with exponential backoff.
    
    Retry Strategy:
    - Attempt 1: 1 hour after failure
    - Attempt 2: 6 hours after last attempt
    - Attempt 3: 24 hours after last attempt
    - Attempt 4: 72 hours after last attempt
    - After 4 attempts: Give up and notify user (persistent errors only)
    """
    
    # Backoff intervals (in hours)
    BACKOFF_SCHEDULE = [1, 6, 24, 72]
    
    def __init__(self, batch_size: int = 30, max_retries: int = 4):
        """
        Initialize retry scheduler.
        
        Args:
            batch_size: Max claims to process per run
            max_retries: Maximum retry attempts before giving up
        """
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.db = get_db_manager()
        self.pod_fetcher = PODFetcher()
        self.api_queue = APIRequestQueue()
        self.notif_manager = NotificationManager()
        
        # Stats
        self.stats = {
            'success': 0,
            'failed': 0,
            'skipped_persistent': 0,
            'skipped_rate_limit': 0,
            'skipped_backoff': 0,
            'max_retries_reached': 0,
            'total': 0
        }
    
    def run(self):
        """Execute scheduler run."""
        logger.info("=" * 70)
        logger.info("POD AUTO-RETRY SCHEDULER - Starting")
        logger.info(f"Batch size: {self.batch_size} | Max retries: {self.max_retries}")
        logger.info("=" * 70)
        
        start_time = datetime.now()
        
        try:
            # Get failed PODs eligible for retry
            failed_claims = self._get_retry_eligible_claims()
            
            if not failed_claims:
                logger.info("✅ No failed PODs eligible for retry")
                return self.stats
            
            logger.info(f"Found {len(failed_claims)} claim(s) to retry")
            
            # Process each claim
            for claim in failed_claims:
                self._process_retry(claim)
            
            # Log summary
            duration = (datetime.now() - start_time).total_seconds()
            self._log_summary(duration)
            
            return self.stats
            
        except Exception as e:
            logger.error(f"Scheduler failed: {e}", exc_info=True)
            raise
    
    def _get_retry_eligible_claims(self) -> List[Dict]:
        """
        Get failed POD claims that are eligible for retry.
        
        Filters:
        - Status: failed
        - Not max retries reached
        - Past backoff interval
        - Not persistent errors (unless first retry)
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Add retry_count and last_retry_at columns if they don't exist
            try:
                cursor.execute("""
                    SELECT pod_retry_count FROM claims LIMIT 1
                """)
            except:
                logger.info("Adding retry tracking columns...")
                cursor.execute("""
                    ALTER TABLE claims 
                    ADD COLUMN pod_retry_count INTEGER DEFAULT 0
                """)
                cursor.execute("""
                    ALTER TABLE claims 
                    ADD COLUMN pod_last_retry_at TIMESTAMP
                """)
                conn.commit()
            
            query = """
                SELECT 
                    id,
                    tracking_number,
                    carrier,
                    claim_reference,
                    client_id,
                    pod_fetch_error,
                    pod_retry_count,
                    pod_last_retry_at,
                    created_at
                FROM claims
                WHERE pod_fetch_status = 'failed'
                AND tracking_number IS NOT NULL
                AND tracking_number != ''
                AND (pod_retry_count IS NULL OR pod_retry_count < ?)
                ORDER BY pod_last_retry_at ASC, created_at ASC
                LIMIT ?
            """
            
            cursor.execute(query, (self.max_retries, self.batch_size * 2))  # Get extra for filtering
            results = cursor.fetchall()
            conn.close()
            
            # Convert to list of dicts and filter by backoff
            claims = []
            for row in results:
                claim = {
                    'id': row[0],
                    'tracking_number': row[1],
                    'carrier': row[2],
                    'claim_reference': row[3],
                    'client_id': row[4],
                    'pod_fetch_error': row[5] or '',
                    'pod_retry_count': row[6] or 0,
                    'pod_last_retry_at': row[7],
                    'created_at': row[8]
                }
                
                # Check if ready for retry (past backoff interval)
                if self._is_ready_for_retry(claim):
                    claims.append(claim)
                    if len(claims) >= self.batch_size:
                        break
            
            return claims
            
        except Exception as e:
            logger.error(f"Failed to get retry eligible claims: {e}")
            return []
    
    def _is_ready_for_retry(self, claim: Dict) -> bool:
        """Check if claim is past its backoff interval."""
        retry_count = claim['pod_retry_count']
        last_retry = claim['pod_last_retry_at']
        
        # First retry - no backoff
        if retry_count == 0:
            return True
        
        # Get backoff hours for this retry attempt
        if retry_count >= len(self.BACKOFF_SCHEDULE):
            # Max retries reached
            return False
        
        backoff_hours = self.BACKOFF_SCHEDULE[retry_count - 1]
        
        # Check if enough time has passed
        if last_retry:
            last_retry_time = datetime.fromisoformat(last_retry) if isinstance(last_retry, str) else last_retry
            next_retry_time = last_retry_time + timedelta(hours=backoff_hours)
            return datetime.now() >= next_retry_time
        
        return True
    
    def _process_retry(self, claim: Dict):
        """
        Process retry for a single claim.
        
        Args:
            claim: Claim dictionary
        """
        claim_id = claim['id']
        claim_ref = claim['claim_reference']
        tracking = claim['tracking_number']
        carrier = claim['carrier']
        retry_count = claim['pod_retry_count']
        error_msg = claim['pod_fetch_error']
        
        self.stats['total'] += 1
        
        logger.info(f"[{self.stats['total']}] Retry #{retry_count + 1} for {claim_ref} ({carrier})")
        
        # Skip persistent errors (after first retry)
        if retry_count > 0 and is_persistent_pod_error(error_msg):
            logger.info(f"⏭️  Skipping {claim_ref} - persistent error: {error_msg[:50]}")
            self.stats['skipped_persistent'] += 1
            
            # Send notification if max retries reached
            if retry_count +1 >= self.max_retries:
                self._send_failure_notification(claim)
                self.stats['max_retries_reached'] += 1
            
            return
        
        # Check rate limit
        if not self.api_queue.can_execute(carrier):
            logger.warning(f"⚠️  Rate limit for {carrier}, skipping {claim_ref}")
            self.stats['skipped_rate_limit'] += 1
            return
        
        try:
            # Attempt POD fetch
            result = self.api_queue.execute_with_limit(
                carrier,
                self.pod_fetcher.fetch_pod,
                tracking,
                carrier
            )
            
            # Update retry tracking
            self._update_retry_tracking(claim_id, retry_count + 1)
            
            if result.get('success'):
                # Success! Update claim
                conn = self.db.get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE claims 
                    SET pod_url = ?,
                        pod_fetch_status = 'success',
                        pod_fetched_at = ?,
                        pod_delivery_person = ?,
                        pod_retry_count = ?
                    WHERE id = ?
                """, (
                    result['pod_url'],
                    datetime.now(),
                    result['pod_data'].get('recipient_name'),
                    retry_count + 1,
                    claim_id
                ))
                conn.commit()
                conn.close()
                
                self.stats['success'] += 1
                logger.info(f"✅ SUCCESS: POD fetched for {claim_ref} after {retry_count + 1} attempts")
                
                # Send success notification
                self._send_success_notification(claim, result['pod_url'])
                
            else:
                # Still failed
                new_error = result.get('error', 'Unknown error')
                
                conn = self.db.get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE claims 
                    SET pod_fetch_error = ?
                    WHERE id = ?
                """, (new_error, claim_id))
                conn.commit()
                conn.close()
                
                self.stats['failed'] += 1
                logger.warning(f"❌ FAILED: {claim_ref} - {new_error[:60]}")
                
                # Send notification if max retries reached AND persistent error
                if retry_count + 1 >= self.max_retries and is_persistent_pod_error(new_error):
                    self._send_failure_notification(claim)
                    self.stats['max_retries_reached'] += 1
                    logger.info(f"📧 Notification sent for {claim_ref} (max retries reached)")
                
        except Exception as e:
            logger.error(f"Exception processing {claim_ref}: {e}")
            self._update_retry_tracking(claim_id, retry_count + 1)
            self.stats['failed'] += 1
    
    def _update_retry_tracking(self, claim_id: int, retry_count: int):
        """Update retry count and timestamp."""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE claims 
                SET pod_retry_count = ?,
                    pod_last_retry_at = ?
                WHERE id = ?
            """, (retry_count, datetime.now(), claim_id))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to update retry tracking: {e}")
    
    def _send_success_notification(self, claim: Dict, pod_url: str):
        """Send success notification after retry."""
        try:
            # Get client email
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT email FROM clients WHERE id = ?
            """, (claim['client_id'],))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                client_email = result[0]
                lang = get_browser_language()
                
                self.notif_manager.queue_notification(
                    client_email=client_email,
                    event_type='pod_retrieved',
                    context={
                        'claim_ref': claim['claim_reference'],
                        'carrier': claim['carrier'],
                        'pod_url': pod_url,
                        'lang': lang
                    }
                )
        except Exception as e:
            logger.warning(f"Failed to send success notification: {e}")
    
    def _send_failure_notification(self, claim: Dict):
        """Send failure notification after max retries."""
        try:
            # Get client email
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT email FROM clients WHERE id = ?
            """, (claim['client_id'],))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                client_email = result[0]
                lang = get_browser_language()
                
                self.notif_manager.queue_notification(
                    client_email=client_email,
                    event_type='pod_failed',
                    context={
                        'claim_ref': claim['claim_reference'],
                        'carrier': claim['carrier'],
                        'error': claim['pod_fetch_error'],
                        'lang': lang
                    }
                )
        except Exception as e:
            logger.warning(f"Failed to send failure notification: {e}")
    
    def _log_summary(self, duration: float):
        """Log run summary with detailed stats."""
        logger.info("")
        logger.info("=" * 70)
        logger.info("POD AUTO-RETRY SCHEDULER - Summary")
        logger.info("=" * 70)
        logger.info(f"Duration: {duration:.2f}s")
        logger.info(f"Total processed: {self.stats['total']}")
        logger.info(f"✅ Success: {self.stats['success']}")
        logger.info(f"❌ Failed: {self.stats['failed']}")
        logger.info(f"⏭️  Skipped (persistent error): {self.stats['skipped_persistent']}")
        logger.info(f"⚠️  Skipped (rate limit): {self.stats['skipped_rate_limit']}")
        logger.info(f"🛑 Max retries reached: {self.stats['max_retries_reached']}")
        
        success_rate = (self.stats['success'] / self.stats['total'] * 100) if self.stats['total'] > 0 else 0
        logger.info(f"Success rate: {success_rate:.1f}%")
        
        # API usage stats
        logger.info("\n📊 API Usage:")
        api_stats = self.api_queue.get_stats()
        for carrier, stats in api_stats.items():
            if stats.get('count', 0) > 0:
                logger.info(f"  {carrier}: {stats['count']}/{stats['limit']} ({stats['usage_percent']}%)")
        
        logger.info("=" * 70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="POD Auto-Retry Scheduler with Exponential Backoff")
    parser.add_argument(
        '--batch-size',
        type=int,
        default=30,
        help='Number of claims to process per run (default: 30)'
    )
    parser.add_argument(
        '--max-retries',
        type=int,
        default=4,
        help='Maximum retry attempts before giving up (default: 4)'
    )
    
    args = parser.parse_args()
    
    # Run scheduler
    scheduler = PODRetryScheduler(
        batch_size=args.batch_size,
        max_retries=args.max_retries
    )
    
    try:
        stats = scheduler.run()
        
        # Exit code based on results
        if stats['total'] == 0:
            sys.exit(0)  # No work to do
        elif stats['failed'] == stats['total']:
            sys.exit(2)  # All failed
        else:
            sys.exit(0)  # Some success
            
    except Exception as e:
        logger.error(f"Scheduler failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
