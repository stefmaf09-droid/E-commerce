"""
Backend worker for automatic order synchronization and dispute detection.

This worker runs periodically to:
1. Fetch new orders from connected e-commerce platforms
2. Analyze orders for potential disputes
3. Update client dashboards
4. Send notifications
"""

import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict
import sys

sys.path.insert(0, 'src')

from auth.credentials_manager import CredentialsManager
from integrations import (
    ShopifyConnector,
    WooCommerceConnector,
    PrestaShopConnector,
    MagentoConnector,
    BigCommerceConnector,
    WixConnector
)
from dispute_detector import DisputeDetectionEngine

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OrderSyncWorker:
    """Worker for synchronizing orders and detecting disputes."""
    
    CONNECTOR_MAP = {
        'shopify': ShopifyConnector,
        'woocommerce': WooCommerceConnector,
        'prestashop': PrestaShopConnector,
        'magento': MagentoConnector,
        'bigcommerce': BigCommerceConnector,
        'wix': WixConnector
    }
    
    def __init__(self, sync_interval_hours: int = 24):
        """
        Initialize the order sync worker.
        
        Args:
            sync_interval_hours: Hours between synchronizations
        """
        self.sync_interval = sync_interval_hours
        self.credentials_manager = CredentialsManager()
        self.dispute_detector = DisputeDetectionEngine()
        
        logger.info(f"OrderSyncWorker initialized (sync every {sync_interval_hours}h)")
    
    def run_forever(self):
        """
        Run worker in continuous loop.
        
        This is for production deployment. Syncs all clients periodically.
        """
        logger.info("🚀 Starting OrderSyncWorker in continuous mode")
        
        while True:
            try:
                self.sync_all_clients()
                
                # Wait for next sync
                logger.info(f"⏳ Sleeping for {self.sync_interval}h until next sync...")
                time.sleep(self.sync_interval * 3600)
                
            except KeyboardInterrupt:
                logger.info("⚠️ Worker stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Error in worker loop: {e}")
                try:
                    import sentry_sdk
                    sentry_sdk.capture_exception(e)
                except ImportError:
                    logger.critical("Sentry SDK not installed. Error not reported.")
                # Optionally: raise to avoid silent failure in production
                # raise
                time.sleep(300)  # 5 minutes
    
    def sync_all_clients(self):
        """Sync orders for all connected clients."""
        clients = self.credentials_manager.list_clients()
        
        if not clients:
            logger.info("No clients to sync")
            return
        
        logger.info(f"📊 Starting sync for {len(clients)} clients")
        
        for client_id, platform, created_at in clients:
            try:
                self.sync_client(client_id, platform)
            except Exception as e:
                logger.error(f"Error syncing {client_id} ({platform}): {e}")
                try:
                    import sentry_sdk
                    sentry_sdk.capture_exception(e)
                except ImportError:
                    logger.critical("Sentry SDK not installed. Error not reported.")
                # Optionally: raise to avoid silent failure in production
                # raise
        
        logger.info(f"✅ Sync completed for {len(clients)} clients")
    
    def sync_client(self, client_id: str, platform: str = None):
        """
        Sync orders for a specific client.
        
        Args:
            client_id: Client identifier (email)
            platform: Platform name (optional, will be fetched if not provided)
        """
        logger.info(f"🔄 Syncing client: {client_id}")
        
        # Get credentials
        credentials = self.credentials_manager.get_credentials(client_id)
        
        if not credentials:
            logger.error(f"No credentials found for {client_id}")
            return
        
        platform = credentials.get('platform')
        
        if platform not in self.CONNECTOR_MAP:
            logger.error(f"Unsupported platform: {platform}")
            return
        
        # Initialize connector
        connector_class = self.CONNECTOR_MAP[platform]
        connector = connector_class(credentials)
        
        # Test authentication
        if not connector.authenticate():
            logger.error(f"Authentication failed for {client_id} ({platform})")
            return
        
        # Fetch orders from last 90 days
        since = datetime.now() - timedelta(days=90)
        
        logger.info(f"Fetching orders since {since.date()} for {client_id}...")
        orders = connector.fetch_orders(since=since)
        
        if not orders:
            logger.warning(f"No orders found for {client_id}")
            return
        
        logger.info(f"✅ Fetched {len(orders)} orders for {client_id}")
        
        # Detect disputes
        logger.info(f"🔍 Analyzing orders for disputes...")
        disputes = self.dispute_detector.analyze_orders(orders)
        
        disputed_orders = [d for d in disputes if d['has_dispute']]
        total_recoverable = sum(d['total_recoverable'] for d in disputed_orders)
        
        logger.info(f"💰 Found {len(disputed_orders)} disputes worth {total_recoverable:,.2f}€")
        
        # Update sync status
        last_order_id = orders[0]['order_id'] if orders else None
        self.credentials_manager.update_sync_status(
            client_id=client_id,
            last_order_id=last_order_id,
            status='active'
        )
        
        # Save disputes to database
        try:
            from src.database import get_db_manager
            db = get_db_manager()
            
            # Get or create client
            client = db.get_client(email=client_id)
            if not client:
                client_db_id = db.create_client(email=client_id)
            else:
                client_db_id = client['id']
            
            # Save each dispute
            new_disputes_count = 0
            for dispute_data in disputed_orders:
                # Check if dispute already exists
                existing = db.get_client_disputes(client_db_id)
                order_exists = any(d['order_id'] == dispute_data['order_id'] for d in existing)
                
                if not order_exists:
                    db.create_dispute(
                        client_id=client_db_id,
                        order_id=dispute_data['order_id'],
                        carrier=dispute_data.get('carrier', ''),
                        dispute_type=dispute_data.get('dispute_type', ''),
                        amount_recoverable=dispute_data.get('total_recoverable', 0.0),
                        order_date=dispute_data.get('order_date'),
                        tracking_number=dispute_data.get('tracking_number'),
                        customer_name=dispute_data.get('recipient', {}).get('name')
                    )
                    new_disputes_count += 1
            
            logger.info(f"📝 Saved {new_disputes_count} new disputes to database")
            
            # Send notification email if new disputes found
            if new_disputes_count > 0:
                try:
                    from src.email_service import send_disputes_detected_email
                    send_disputes_detected_email(
                        client_email=client_id,
                        disputes_count=new_disputes_count,
                        total_amount=total_recoverable,
                        disputes_summary=disputed_orders
                    )
                    logger.info(f"📧 Notification email sent to {client_id}")
                    
                    # Log notification
                    db.log_notification(
                        client_id=client_db_id,
                        notification_type='disputes_detected',
                        subject=f'{new_disputes_count} nouveaux litiges détectés',
                        sent_to=client_id,
                        status='sent'
                    )
                except Exception as e:
                    logger.warning(f"Failed to send email notification: {e}")
            
            # Update client dashboard
            # The dashboard reads directly from database, so it will be automatically updated
            logger.info(f"✅ Dashboard updated (via database persistence)")
            
        except Exception as e:
            logger.error(f"Error saving disputes or sending notifications: {e}")
        
        return {
            'client_id': client_id,
            'platform': platform,
            'orders_fetched': len(orders),
            'disputes_found': len(disputed_orders),
            'total_recoverable': total_recoverable,
            'new_disputes_saved': new_disputes_count if 'new_disputes_count' in locals() else 0
        }
    
    def sync_client_once(self, client_email: str) -> Dict:
        """
        One-time sync for a specific client (useful for testing).
        
        Args:
            client_email: Client email address
            
        Returns:
            Dictionary with sync results
        """
        return self.sync_client(client_email)


def main():
    """Main entry point for worker."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Order Sync Worker')
    parser.add_argument(
        '--mode',
        choices=['once', 'continuous'],
        default='once',
        help='Run mode: once (single sync) or continuous (loop)'
    )
    parser.add_argument(
        '--client',
        type=str,
        help='Specific client email to sync (for testing)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=24,
        help='Sync interval in hours (for continuous mode)'
    )
    
    args = parser.parse_args()
    
    worker = OrderSyncWorker(sync_interval_hours=args.interval)
    
    if args.mode == 'once':
        if args.client:
            logger.info(f"Running one-time sync for {args.client}")
            result = worker.sync_client_once(args.client)
            if result:
                print("\n" + "="*60)
                print("SYNC RESULTS")
                print("="*60)
                print(f"Client: {result['client_id']}")
                print(f"Platform: {result['platform']}")
                print(f"Orders Fetched: {result['orders_fetched']}")
                print(f"Disputes Found: {result['disputes_found']}")
                print(f"Total Recoverable: {result['total_recoverable']:,.2f}€")
                print("="*60)
        else:
            logger.info("Running one-time sync for all clients")
            worker.sync_all_clients()
    else:
        logger.info("Running in continuous mode")
        worker.run_forever()


if __name__ == "__main__":  # pragma: no cover
    main()
