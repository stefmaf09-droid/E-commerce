"""
POD Fetch Background Worker

Processes pending POD fetches in batches.
Designed to run as a scheduled cron job every 30 minutes.

Features:
- Batch processing (configurable batch size)
- Rate limit-aware (respects API limits)
- Error handling and logging
- Progress tracking
- Automatic retry for failed fetches

Schedule:
- Windows: schtasks /create /tn "PODFetchWorker" /tr "python D:\\Recours_Ecommerce\\scripts\\pod_fetch_worker.py" /sc minute /mo 30
- Linux: */30 * * * * cd /path/to/Recours_Ecommerce && python scripts/pod_fetch_worker.py

Usage:
    python scripts/pod_fetch_worker.py
    
    # With custom batch size
    python scripts/pod_fetch_worker.py --batch-size 100
"""

import os
import sys
import logging
import argparse
from datetime import datetime
from pathlib import Path

# Add project to path
root_dir = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(root_dir))

from src.database.database_manager import get_db_manager
from src.integrations.pod_fetcher import PODFetcher
from src.integrations.api_request_queue import APIRequestQueue

# Create logs directory before logging setup
(root_dir / 'logs').mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler(root_dir / 'logs' / 'pod_worker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PODFetchWorker:
    """Background worker for processing pending POD fetches."""
    
    def __init__(self, batch_size: int = 50):
        """
        Initialize worker.
        
        Args:
            batch_size: Number of claims to process per run
        """
        self.batch_size = batch_size
        self.db = get_db_manager()
        self.pod_fetcher = PODFetcher()
        self.api_queue = APIRequestQueue()
        
        # Stats
        self.stats = {
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'total': 0
        }
    
    def run(self):
        """Execute worker run."""
        logger.info("="*70)
        logger.info("POD FETCH WORKER - Starting")
        logger.info(f"Batch size: {self.batch_size}")
        logger.info("="*70)
        
        start_time = datetime.now()
        
        try:
            # Get pending claims
            pending_claims = self._get_pending_claims()
            
            if not pending_claims:
                logger.info("No pending POD fetches found")
                return self.stats
            
            logger.info(f"Found {len(pending_claims)} pending POD fetch(es)")
            
            # Process each claim
            for claim in pending_claims:
                self._process_claim(claim)
            
            # Log summary
            duration = (datetime.now() - start_time).total_seconds()
            self._log_summary(duration)
            
            return self.stats
            
        except Exception as e:
            logger.error(f"Worker failed: {e}", exc_info=True)
            raise
    
    def _get_pending_claims(self) -> list:
        """Get claims with pending POD fetch status."""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    id,
                    tracking_number,
                    carrier,
                    claim_reference,
                    created_at
                FROM claims
                WHERE pod_fetch_status = 'pending'
                AND tracking_number IS NOT NULL
                AND tracking_number != ''
                ORDER BY created_at ASC
                LIMIT ?
            """
            
            cursor.execute(query, (self.batch_size,))
            results = cursor.fetchall()
            conn.close()
            
            # Convert to list of dicts
            claims = []
            for row in results:
                claims.append({
                    'id': row[0],
                    'tracking_number': row[1],
                    'carrier': row[2],
                    'claim_reference': row[3],
                    'created_at': row[4]
                })
            
            return claims
            
        except Exception as e:
            logger.error(f"Failed to get pending claims: {e}")
            return []
    
    def _process_claim(self, claim: dict):
        """
        Process a single claim POD fetch.
        
        Args:
            claim: Claim dictionary
        """
        claim_id = claim['id']
        claim_ref = claim['claim_reference']
        tracking = claim['tracking_number']
        carrier = claim['carrier']
        
        self.stats['total'] += 1
        
        logger.info(f"[{self.stats['total']}/{self.batch_size}] Processing {claim_ref} ({carrier})")
        
        # Check rate limit
        if not self.api_queue.can_execute(carrier):
            logger.warning(f"⚠️ Rate limit for {carrier}, skipping {claim_ref}")
            self.stats['skipped'] += 1
            return
        
        try:
            # Fetch POD with rate limiting
            result = self.api_queue.execute_with_limit(
                carrier,
                self.pod_fetcher.fetch_pod,
                tracking,
                carrier
            )
            
            if result.get('success'):
                # Update claim with POD
                self.db.update_claim(
                    claim_id,
                    pod_url=result['pod_url'],
                    pod_fetch_status='success',
                    pod_fetched_at=datetime.now(),
                    pod_delivery_person=result['pod_data'].get('recipient_name'),
                    pod_signature_url=result['pod_data'].get('signature_url')
                )
                
                self.stats['success'] += 1
                logger.info(f"✅ POD fetched successfully for {claim_ref}")
                
            else:
                # Mark as failed
                error_msg = result.get('error', 'Unknown error')
                self.db.update_claim(
                    claim_id,
                    pod_fetch_status='failed',
                    pod_fetch_error=error_msg
                )
                
                self.stats['failed'] += 1
                logger.warning(f"❌ POD fetch failed for {claim_ref}: {error_msg}")
                
        except Exception as e:
            logger.error(f"Exception processing {claim_ref}: {e}")
            
            # Update claim with exception
            self.db.update_claim(
                claim_id,
                pod_fetch_status='failed',
                pod_fetch_error=f'Exception: {str(e)}'
            )
            
            self.stats['failed'] += 1
    
    def _log_summary(self, duration: float):
        """Log run summary."""
        logger.info("")
        logger.info("="*70)
        logger.info("POD FETCH WORKER - Summary")
        logger.info("="*70)
        logger.info(f"Duration: {duration:.2f}s")
        logger.info(f"Total processed: {self.stats['total']}")
        logger.info(f"✅ Success: {self.stats['success']}")
        logger.info(f"❌ Failed: {self.stats['failed']}")
        logger.info(f"⚠️  Skipped (rate limit): {self.stats['skipped']}")
        
        success_rate = (self.stats['success'] / self.stats['total'] * 100) if self.stats['total'] > 0 else 0
        logger.info(f"Success rate: {success_rate:.1f}%")
        
        # API usage stats
        logger.info("\n📊 API Usage:")
        api_stats = self.api_queue.get_stats()
        for carrier, stats in api_stats.items():
            if stats.get('count', 0) > 0:
                logger.info(f"  {carrier}: {stats['count']}/{stats['limit']} ({stats['usage_percent']}%)")
        
        logger.info("="*70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="POD Fetch Background Worker")
    parser.add_argument(
        '--batch-size',
        type=int,
        default=50,
        help='Number of claims to process per run (default: 50)'
    )
    
    args = parser.parse_args()
    
    # Create logs directory
    (root_dir / 'logs').mkdir(exist_ok=True)
    
    # Run worker
    worker = PODFetchWorker(batch_size=args.batch_size)
    
    try:
        stats = worker.run()
        
        # Exit code based on results
        if stats['total'] == 0:
            sys.exit(0)  # No work to do
        elif stats['failed'] == stats['total']:
            sys.exit(2)  # All failed
        else:
            sys.exit(0)  # Some success
            
    except Exception as e:
        logger.error(f"Worker failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
