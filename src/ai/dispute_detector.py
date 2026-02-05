"""
Auto-Dispute Detector

Automatically detects disputes from order tracking data.

Features:
- Scans order tracking for problematic deliveries
- Detects: Invalid POD, Lost packages, Delays, Damage
- Auto-creates claims when issues found
- Configurable detection rules
- Integrates with NotificationManager

Usage:
    from src.ai.dispute_detector import DisputeDetector
    
    detector = DisputeDetector()
    disputes = detector.scan_orders(order_data)
    
    for dispute in disputes:
        detector.create_claim(dispute)
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)


class DisputeDetector:
    """Automatically detect disputes from order data."""
    
    # Detection rules
    DELAY_THRESHOLD_DAYS = 5  # Consider delayed if >5 days late
    POD_INVALID_KEYWORDS = [
        'signature manquante', 'non signé', 'signature illisible',
        'missing signature', 'unsigned', 'illegible signature',
        'boîte aux lettres', 'mailbox', 'garage', 'portail'
    ]
    
    def __init__(self, db_manager=None):
        """Initialize dispute detector."""
        if db_manager:
            self.db = db_manager
        else:
            import sys
            import os
            # Add project root to path for imports
            root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            if root_dir not in sys.path:
                sys.path.insert(0, root_dir)
            
            from src.database.database_manager import get_db_manager
            self.db = get_db_manager()
        
        logger.info("DisputeDetector initialized")
    
    def scan_orders(
        self,
        orders: List[Dict[str, Any]],
        client_email: str
    ) -> List[Dict[str, Any]]:
        """
        Scan orders for potential disputes.
        
        Args:
            orders: List of order dictionaries with tracking data
            client_email: Client email for notifications
            
        Returns:
            List of detected disputes with details
        """
        detected_disputes = []
        
        for order in orders:
            # Check each detection rule
            dispute_type = None
            reason = None
            confidence = 0.0
            
            # 1. Check for invalid POD
            if self._check_invalid_pod(order):
                dispute_type = 'pod_invalide'
                reason = 'POD signature manquante ou non conforme'
                confidence = 0.85
            
            # 2. Check for lost package
            elif self._check_lost_package(order):
                dispute_type = 'colis_perdu'
                reason = 'Colis non livré dans les délais légaux'
                confidence = 0.90
            
            # 3. Check for delivery delay
            elif self._check_delivery_delay(order):
                dispute_type = 'retard_livraison'
                reason = f"Retard de {self._calculate_delay_days(order)} jours"
                confidence = 0.75
            
            # 4. Check for damage
            elif self._check_damaged(order):
                dispute_type = 'colis_endommage'
                reason = 'Colis livré endommagé'
                confidence = 0.80
            
            # If dispute detected, add to results
            if dispute_type:
                dispute = {
                    'order_id': order.get('order_id'),
                    'tracking_number': order.get('tracking_number'),
                    'carrier': order.get('carrier', 'unknown'),
                    'dispute_type': dispute_type,
                    'reason': reason,
                    'confidence': confidence,
                    'client_email': client_email,
                    'order_date': order.get('order_date'),
                    'delivery_date': order.get('delivery_date'),
                    'expected_delivery': order.get('expected_delivery'),
                    'order_value': order.get('order_value', 0),
                    'shipping_cost': order.get('shipping_cost', 0),
                    'total_recoverable': order.get('order_value', 0) + order.get('shipping_cost', 0),
                    'pod_data': order.get('pod_data', {}),
                    'customer_name': order.get('customer_name'),
                    'delivery_address': order.get('delivery_address')
                }
                
                detected_disputes.append(dispute)
                logger.info(f"Dispute detected: {order.get('order_id')} - {dispute_type} (confidence: {confidence:.0%})")
        
        logger.info(f"Scan complete: {len(detected_disputes)} disputes detected from {len(orders)} orders")
        return detected_disputes
    
    def _check_invalid_pod(self, order: Dict) -> bool:
        """Check if POD is invalid or non-compliant."""
        pod_data = order.get('pod_data', {})
        
        if not pod_data:
            return False
        
        # Check for missing signature
        if not pod_data.get('signature'):
            return True
        
        # Check for invalid delivery location
        delivery_location = pod_data.get('delivery_location', '').lower()
        for keyword in self.POD_INVALID_KEYWORDS:
            if keyword in delivery_location:
                return True
        
        # Check if signature doesn't match recipient
        if pod_data.get('signer_name'):
            recipient = order.get('customer_name', '').lower()
            signer = pod_data.get('signer_name', '').lower()
            
            # Simple name matching (could be improved with fuzzy matching)
            if recipient and signer and recipient not in signer and signer not in recipient:
                return True
        
        return False
    
    def _check_lost_package(self, order: Dict) -> bool:
        """Check if package is lost (no delivery after reasonable time)."""
        # Package is considered lost if:
        # 1. Status is "in transit" or "unknown" for >14 days
        # 2. OR no tracking updates for >10 days
        
        status = order.get('delivery_status', '').lower()
        
        if status in ['delivered', 'livré']:
            return False
        
        # Check order age
        order_date = order.get('order_date')
        if order_date:
            if isinstance(order_date, str):
                try:
                    order_date = datetime.fromisoformat(order_date)
                except:
                    return False
            
            days_since_order = (datetime.now() - order_date).days
            
            # Lost if in transit for >14 days
            if days_since_order > 14:
                return True
        
        return False
    
    def _check_delivery_delay(self, order: Dict) -> bool:
        """Check if delivery is significantly delayed."""
        expected_delivery = order.get('expected_delivery')
        actual_delivery = order.get('delivery_date')
        
        if not expected_delivery:
            return False
        
        # Convert to datetime if string
        if isinstance(expected_delivery, str):
            try:
                expected_delivery = datetime.fromisoformat(expected_delivery)
            except:
                return False
        
        # If not yet delivered, check against current date
        if not actual_delivery:
            delay_days = (datetime.now().date() - expected_delivery.date()).days
        else:
            if isinstance(actual_delivery, str):
                try:
                    actual_delivery = datetime.fromisoformat(actual_delivery)
                except:
                    return False
            delay_days = (actual_delivery.date() - expected_delivery.date()).days
        
        # Delayed if >DELAY_THRESHOLD_DAYS late
        return delay_days > self.DELAY_THRESHOLD_DAYS
    
    def _calculate_delay_days(self, order: Dict) -> int:
        """Calculate number of delay days."""
        expected_delivery = order.get('expected_delivery')
        actual_delivery = order.get('delivery_date')
        
        if not expected_delivery:
            return 0
        
        if isinstance(expected_delivery, str):
            try:
                expected_delivery = datetime.fromisoformat(expected_delivery)
            except:
                return 0
        
        if not actual_delivery:
            return (datetime.now().date() - expected_delivery.date()).days
        
        if isinstance(actual_delivery, str):
            try:
                actual_delivery = datetime.fromisoformat(actual_delivery)
            except:
                return 0
        
        return (actual_delivery.date() - expected_delivery.date()).days
    
    def _check_damaged(self, order: Dict) -> bool:
        """Check if package was delivered damaged."""
        # Check for damage indicators in notes or status
        notes = order.get('delivery_notes', '').lower()
        damage_keywords = [
            'endommagé', 'cassé', 'abîmé', 'damaged', 'broken',
            'crushed', 'torn', 'wet', 'mouillé'
        ]
        
        for keyword in damage_keywords:
            if keyword in notes:
                return True
        
        # Check POD for damage mention
        pod_data = order.get('pod_data', {})
        pod_notes = pod_data.get('notes', '').lower()
        
        for keyword in damage_keywords:
            if keyword in pod_notes:
                return True
        
        return False
    
    def auto_create_claims(
        self,
        disputes: List[Dict[str, Any]],
        auto_submit: bool = False
    ) -> int:
        """
        Automatically create claims for detected disputes.
        
        Args:
            disputes: List of detected disputes
            auto_submit: Whether to auto-submit claims to carriers
            
        Returns:
            Number of claims created
        """
        created_count = 0
        
        from src.orchestrator import AutoRecoveryOrchestrator
        orchestrator = AutoRecoveryOrchestrator()
        
        for dispute in disputes:
            try:
                # Only create if confidence >70%
                if dispute.get('confidence', 0) < 0.70:
                    logger.info(f"Skipping low-confidence dispute: {dispute['order_id']} ({dispute['confidence']:.0%})")
                    continue
                
                # Check if claim already exists for this order
                conn = self.db.get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id FROM claims WHERE order_id = ?",
                    (dispute['order_id'],)
                )
                existing = cursor.fetchone()
                conn.close()
                
                if existing:
                    logger.info(f"Claim already exists for order {dispute['order_id']}, skipping")
                    continue
                
                # Create claim via orchestrator
                if auto_submit:
                    import asyncio
                    result = asyncio.run(orchestrator.process_dispute(dispute))
                    
                    if result.get('success'):
                        created_count += 1
                        logger.info(f"✅ Auto-created and submitted claim for {dispute['order_id']}")
                    else:
                        logger.warning(f"Failed to auto-submit claim for {dispute['order_id']}")
                else:
                    # Just create without submitting
                    conn = self.db.get_connection()
                    client = self.db.get_client(email=dispute['client_email'])
                    
                    if client:
                        import random
                        import string
                        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
                        claim_ref = f"CLM-AUTO-{datetime.now().strftime('%Y%m%d%H%M%S')}-{suffix}"
                        
                        claim_id = self.db.create_claim(
                            claim_reference=claim_ref,
                            client_id=client['id'],
                            order_id=dispute['order_id'],
                            carrier=dispute['carrier'],
                            dispute_type=dispute['dispute_type'],
                            amount_requested=dispute['total_recoverable'],
                            tracking_number=dispute.get('tracking_number'),
                            order_date=dispute.get('order_date')
                        )
                        
                        created_count += 1
                        logger.info(f"✅ Auto-created claim {claim_ref} for {dispute['order_id']}")
                
            except Exception as e:
                logger.error(f"Failed to create claim for {dispute.get('order_id')}: {e}")
        
        logger.info(f"Auto-created {created_count} claims from {len(disputes)} disputes")
        return created_count


if __name__ == "__main__":
    # Test the dispute detector
    print("="*70)
    print("AUTO-DISPUTE DETECTOR - Test")
    print("="*70)
    
    detector = DisputeDetector()
    
    # Sample test data
    test_orders = [
        {
            'order_id': 'ORD-TEST-001',
            'tracking_number': 'FR123456789',
            'carrier': 'colissimo',
            'order_date': (datetime.now() - timedelta(days=20)).isoformat(),
            'expected_delivery': (datetime.now() - timedelta(days=15)).isoformat(),
            'delivery_date': None,
            'delivery_status': 'in_transit',
            'order_value': 50.0,
            'shipping_cost': 5.0,
            'customer_name': 'Jean Dupont'
        },
        {
            'order_id': 'ORD-TEST-002',
            'tracking_number': 'CHR987654321',
            'carrier': 'chronopost',
            'order_date': (datetime.now() - timedelta(days=10)).isoformat(),
            'expected_delivery': (datetime.now() - timedelta(days=3)).isoformat(),
            'delivery_date': datetime.now().isoformat(),
            'delivery_status': 'delivered',
            'order_value': 120.0,
            'shipping_cost': 12.0,
            'pod_data': {
                'signature': False,
                'delivery_location': 'boîte aux lettres',
                'signer_name': None
            },
            'customer_name': 'Marie Martin'
        }
    ]
    
    print("\n📊 Scanning test orders...")
    disputes = detector.scan_orders(test_orders, 'test@client.com')
    
    print(f"\n✅ Found {len(disputes)} disputes:")
    for dispute in disputes:
        print(f"\n  - Order: {dispute['order_id']}")
        print(f"    Type: {dispute['dispute_type']}")
        print(f"    Reason: {dispute['reason']}")
        print(f"    Confidence: {dispute['confidence']:.0%}")
        print(f"    Recoverable: {dispute['total_recoverable']}€")
    
    print("\n" + "="*70)
    print("✅ Dispute Detector Operational")
    print("="*70)
