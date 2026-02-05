"""
Notification Manager - Smart email notification system with user preferences.

Handles:
- User preference checking before sending
- Frequency-based queuing (immediate, daily, weekly)
- Anti-spam protection (max 10 emails/day per client)
- Digest generation for batched notifications

Usage:
    from src.notifications.notification_manager import NotificationManager
    
    manager = NotificationManager()
    manager.queue_notification(
        client_email='client@example.com',
        event_type='claim_created',
        context={'claim_ref': 'CLM-001', 'carrier': 'Colissimo', 'amount': 45.0}
    )
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

# Add project root to path
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, root_dir)

from src.database.database_manager import get_db_manager

logger = logging.getLogger(__name__)


class NotificationManager:
    """Smart notification system respecting user preferences."""
    
    # Anti-spam limits
    MAX_EMAILS_PER_DAY = 10
    
    # Default preferences if user hasn't set any
    DEFAULT_PREFERENCES = {
        'claim_created': True,
        'claim_updated': True,
        'claim_accepted': True,
        'payment_received': True,
        'deadline_warning': True,
        'frequency': 'immediate'
    }
    
    def __init__(self):
        self.db = get_db_manager()
    
    def queue_notification(
        self, 
        client_email: str, 
        event_type: str, 
        context: Dict[str, Any]
    ) -> bool:
        """
        Queue a notification based on user preferences.
        
        Args:
            client_email: Recipient email
            event_type: Type of notification (claim_created, claim_updated, etc.)
            context: Data to populate email template (claim_ref, amount, etc.)
            
        Returns:
            True if notification was queued/sent, False if user has disabled it
        """
        # Check if user wants this notification
        if not self.should_notify(client_email, event_type):
            logger.info(f"Notification {event_type} disabled for {client_email}")
            return False
        
        # Check anti-spam limit
        if not self._check_daily_limit(client_email):
            logger.warning(f"Daily email limit reached for {client_email}")
            return False
        
        # Get user frequency preference
        prefs = self._get_user_preferences(client_email)
        frequency = prefs.get('frequency', 'immediate')
        
        if frequency == 'immediate':
            return self._send_now(client_email, event_type, context)
        elif frequency == 'daily':
            return self._queue_for_daily_digest(client_email, event_type, context)
        elif frequency == 'weekly':
            return self._queue_for_weekly_digest(client_email, event_type, context)
        
        return False
    
    def should_notify(self, client_email: str, event_type: str) -> bool:
        """
        Check if user wants to receive this notification type.
        
        Args:
            client_email: User email
            event_type: Notification type to check
            
        Returns:
            True if user has enabled this notification, False otherwise
        """
        prefs = self._get_user_preferences(client_email)
        return prefs.get(event_type, True)
    
    def _get_user_preferences(self, client_email: str) -> Dict[str, Any]:
        """
        Load user notification preferences from database.
        
        Args:
            client_email: User email
            
        Returns:
            Dict with user preferences or default preferences
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT notification_preferences FROM clients WHERE email = ?",
                (client_email,)
            )
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0]:
                return json.loads(result[0])
            else:
                return self.DEFAULT_PREFERENCES.copy()
                
        except Exception as e:
            logger.error(f"Failed to load preferences for {client_email}: {e}")
            return self.DEFAULT_PREFERENCES.copy()
    
    def _check_daily_limit(self, client_email: str) -> bool:
        """
        Check if user hasn't exceeded daily email quota.
        
        Args:
            client_email: User email
            
        Returns:
            True if under limit, False if limit reached
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Count emails sent today
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            cursor.execute("""
                SELECT COUNT(*) FROM notifications
                WHERE sent_to = ? AND sent_at >= ?
            """, (client_email, today_start))
            
            count = cursor.fetchone()[0]
            conn.close()
            
            return count < self.MAX_EMAILS_PER_DAY
            
        except Exception as e:
            logger.error(f"Failed to check daily limit: {e}")
            return True  # Allow on error to not block critical notifications
    
    def _send_now(self, client_email: str, event_type: str, context: Dict[str, Any]) -> bool:
        """
        Send email immediately.
        
        Args:
            client_email: Recipient
            event_type: Type of email
            context: Template data
            
        Returns:
            True if sent successfully
        """
        try:
            from src.notifications.send_notification import send_notification_email
            
            # Send email
            success = send_notification_email(
                to_email=client_email,
                event_type=event_type,
                context=context
            )
            
            if success:
                # Log to notifications table
                self._log_notification(client_email, event_type, context)
                logger.info(f"Sent {event_type} notification to {client_email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to send immediate notification: {e}")
            return False
    
    def _queue_for_daily_digest(
        self, 
        client_email: str, 
        event_type: str, 
        context: Dict[str, Any]
    ) -> bool:
        """
        Add notification to daily digest queue.
        
        Daily digest sent at 9:00 AM.
        
        Args:
            client_email: Recipient
            event_type: Type of notification
            context: Template data
            
        Returns:
            True if queued successfully
        """
        try:
            # Store in pending_notifications table (to be created)
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Create table if doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pending_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_email TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    context TEXT NOT NULL,
                    digest_type TEXT DEFAULT 'daily',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                INSERT INTO pending_notifications (client_email, event_type, context, digest_type)
                VALUES (?, ?, ?, 'daily')
            """, (client_email, event_type, json.dumps(context)))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Queued {event_type} for daily digest: {client_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to queue for daily digest: {e}")
            return False
    
    def _queue_for_weekly_digest(
        self, 
        client_email: str, 
        event_type: str, 
        context: Dict[str, Any]
    ) -> bool:
        """
        Add notification to weekly digest queue.
        
        Weekly digest sent Monday at 9:00 AM.
        
        Args:
            client_email: Recipient
            event_type: Type of notification
            context: Template data
            
        Returns:
            True if queued successfully
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO pending_notifications (client_email, event_type, context, digest_type)
                VALUES (?, ?, ?, 'weekly')
            """, (client_email, event_type, json.dumps(context)))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Queued {event_type} for weekly digest: {client_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to queue for weekly digest: {e}")
            return False
    
    def _log_notification(self, client_email: str, event_type: str, context: Dict[str, Any]):
        """Log sent notification to database for tracking."""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Get client_id
            cursor.execute("SELECT id FROM clients WHERE email = ?", (client_email,))
            result = cursor.fetchone()
            client_id = result[0] if result else None
            
            if client_id:
                subject = self._get_email_subject(event_type, context)
                cursor.execute("""
                    INSERT INTO notifications (client_id, notification_type, subject, sent_to, status)
                    VALUES (?, ?, ?, ?, 'sent')
                """, (client_id, event_type, subject, client_email))
                conn.commit()
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to log notification: {e}")
    
    def _get_email_subject(self, event_type: str, context: Dict[str, Any]) -> str:
        """Generate email subject based on event type."""
        subjects = {
            'claim_created': f"✅ Nouveau litige {context.get('claim_ref', 'créé')}",
            'claim_updated': f"🔄 Mise à jour - {context.get('claim_ref', 'Litige')}",
            'claim_accepted': f"🎉 Litige accepté - {context.get('claim_ref', '')}",
            'payment_received': f"💰 Remboursement reçu - {context.get('amount', '')}€",
            'deadline_warning': f"⚠️ Action requise - {context.get('claim_ref', 'Litige')}"
        }
        return subjects.get(event_type, "Notification Refundly")
    
    def send_daily_digests(self) -> int:
        """
        Send all pending daily digest emails.
        
        Called by cron job at 9:00 AM daily.
        
        Returns:
            Number of digests sent
        """
        # TODO: Implement digest sender
        logger.info("Daily digest sending not yet implemented")
        return 0
    
    def send_weekly_digests(self) -> int:
        """
        Send all pending weekly digest emails.
        
        Called by cron job Monday at 9:00 AM.
        
        Returns:
            Number of digests sent
        """
        # TODO: Implement digest sender
        logger.info("Weekly digest sending not yet implemented")
        return 0


if __name__ == "__main__":
    # Test the notification manager
    print("="*70)
    print("NOTIFICATION MANAGER - Test")
    print("="*70)
    
    manager = NotificationManager()
    
    print("\n1. Testing preference check:")
    should_notify = manager.should_notify('test@client.com', 'claim_created')
    print(f"   Should notify test@client.com for claim_created? {should_notify}")
    
    print("\n2. Testing notification queue:")
    success = manager.queue_notification(
        'test@client.com',
        'claim_created',
        {'claim_ref': 'CLM-TEST-001', 'carrier': 'Colissimo', 'amount': 45.0}
    )
    print(f"   Notification queued? {success}")
    
    print("\n" + "="*70)
    print("✅ Notification Manager Operational")
    print("="*70)
