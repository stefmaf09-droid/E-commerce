"""
Simple Notifications System for Client Dashboard

Uses Streamlit session state and auto-refresh for real-time updates.
Simpler alternative to WebSocket for MVP.
"""

import streamlit as st
from datetime import datetime
from typing import List, Dict
import json
import os


class SimpleNotificationSystem:
    """Simple notification system using file-based storage."""
    
    def __init__(self, notifications_file: str = "data/notifications.json"):
        """Initialize notification system."""
        self.notifications_file = notifications_file
        os.makedirs(os.path.dirname(notifications_file), exist_ok=True)
        
        if not os.path.exists(notifications_file):
            with open(notifications_file, 'w') as f:
                json.dump({}, f)
    
    def add_notification(
        self,
        client_email: str,
        notification_type: str,
        message: str,
        data: Dict = None
    ):
        """
        Add a notification for a client.
        
        Args:
            client_email: Client email
            notification_type: Type (claim_submitted, status_update, money_recovered)
            message: Notification message
            data: Additional data
        """
        notifications = self._load_notifications()
        
        if client_email not in notifications:
            notifications[client_email] = []
        
        notification = {
            'id': len(notifications[client_email]) + 1,
            'type': notification_type,
            'message': message,
            'data': data or {},
            'timestamp': datetime.now().isoformat(),
            'read': False
        }
        
        notifications[client_email].append(notification)
        self._save_notifications(notifications)
    
    def get_notifications(self, client_email: str, unread_only: bool = False) -> List[Dict]:
        """Get notifications for a client."""
        notifications = self._load_notifications()
        client_notifications = notifications.get(client_email, [])
        
        if unread_only:
            return [n for n in client_notifications if not n.get('read', False)]
        
        return client_notifications
    
    def mark_as_read(self, client_email: str, notification_id: int):
        """Mark notification as read."""
        notifications = self._load_notifications()
        
        if client_email in notifications:
            for n in notifications[client_email]:
                if n['id'] == notification_id:
                    n['read'] = True
            
            self._save_notifications(notifications)
    
    def mark_all_read(self, client_email: str):
        """Mark all notifications as read."""
        notifications = self._load_notifications()
        
        if client_email in notifications:
            for n in notifications[client_email]:
                n['read'] = True
            
            self._save_notifications(notifications)
    
    def _load_notifications(self) -> Dict:
        """Load notifications from file."""
        try:
            with open(self.notifications_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def _save_notifications(self, notifications: Dict):
        """Save notifications to file."""
        with open(self.notifications_file, 'w') as f:
            json.dump(notifications, f, indent=2)


def render_notifications_panel(client_email: str):
    """
    Render notifications panel in Streamlit dashboard.
    
    Call this at the top of the dashboard to show notifications.
    """
    notif_system = SimpleNotificationSystem()
    
    unread = notif_system.get_notifications(client_email, unread_only=True)
    
    if unread:
        # Show notification badge
        with st.sidebar:
            st.markdown(f"### 🔔 Notifications ({len(unread)})")
            
            for notif in unread[:5]:  # Show max 5
                icon = {
                    'claim_submitted': '📤',
                    'status_update': '🔄',
                    'money_recovered': '💰'
                }.get(notif['type'], '📌')
                
                st.info(f"{icon} {notif['message']}")
            
            if st.button("✅ Marquer tout comme lu"):
                notif_system.mark_all_read(client_email)
                st.rerun()


# Test
if __name__ == "__main__":
    print("="*70)
    print("SIMPLE NOTIFICATIONS - Test")
    print("="*70)
    
    system = SimpleNotificationSystem("data/test_notifications.json")
    
    # Add test notifications
    system.add_notification(
        "test@example.com",
        "claim_submitted",
        "Réclamation envoyée à Colissimo",
        {"tracking": "FR123456789", "amount": "150.00"}
    )
    
    system.add_notification(
        "test@example.com",
        "money_recovered",
        "💰 120€ récupérés pour commande ORD-001",
        {"amount": 120.00}
    )
    
    # Get notifications
    notifs = system.get_notifications("test@example.com")
    
    print(f"\n✅ {len(notifs)} notifications créées")
    
    for n in notifs:
        print(f"  - {n['type']}: {n['message']}")
    
    # Test unread
    unread = system.get_notifications("test@example.com", unread_only=True)
    print(f"\n📬 {len(unread)} non lues")
    
    # Mark as read
    system.mark_all_read("test@example.com")
    unread_after = system.get_notifications("test@example.com", unread_only=True)
    print(f"✅ Après marquage : {len(unread_after)} non lues")
    
    print("\n" + "="*70)
    print("✅ Test Complete")
    print("="*70)
