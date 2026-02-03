"""
Manual Payment Manager - Track and manage manual payments to clients.

For use before Stripe Connect is activated.
"""

import sqlite3
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class ManualPaymentManager:
    """Manage manual payments to clients."""
    
    def __init__(self, db_path: str = "database/manual_payments.db"):
        """Initialize manual payment manager."""
        self.db_path = db_path
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """Create database and tables if they don't exist."""
        Path(self.db_path).parent.mkdir(exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table pour les IBAN clients
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS client_bank_info (
                client_email TEXT PRIMARY KEY,
                iban TEXT NOT NULL,
                bic TEXT,
                account_holder_name TEXT,
                bank_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table pour les paiements manuels
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS manual_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                claim_reference TEXT NOT NULL,
                client_email TEXT NOT NULL,
                total_amount REAL NOT NULL,
                client_share REAL NOT NULL,
                platform_fee REAL NOT NULL,
                payment_status TEXT DEFAULT 'pending',
                payment_date TIMESTAMP,
                payment_method TEXT,
                transaction_reference TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"Manual payment database initialized at {self.db_path}")
    
    def add_client_bank_info(
        self,
        client_email: str,
        iban: str,
        bic: Optional[str] = None,
        account_holder_name: Optional[str] = None,
        bank_name: Optional[str] = None
    ) -> bool:
        """
        Add or update client bank information.
        
        Args:
            client_email: Client email
            iban: IBAN number
            bic: BIC/SWIFT code (optional)
            account_holder_name: Name on the account
            bank_name: Bank name
            
        Returns:
            True if successful
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO client_bank_info
                (client_email, iban, bic, account_holder_name, bank_name, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (client_email, iban, bic, account_holder_name, bank_name))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Bank info saved for {client_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save bank info: {e}")
            return False
    
    def get_client_bank_info(self, client_email: str) -> Optional[Dict[str, Any]]:
        """Get client bank information."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT client_email, iban, bic, account_holder_name, bank_name
                FROM client_bank_info
                WHERE client_email = ?
            """, (client_email,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'client_email': row[0],
                    'iban': row[1],
                    'bic': row[2],
                    'account_holder_name': row[3],
                    'bank_name': row[4]
                }
            return None
            
        except Exception as e:
            logger.error(f"Failed to get bank info: {e}")
            return None
    
    def create_payment(
        self,
        claim_reference: str,
        client_email: str,
        total_amount: float,
        client_share: float,
        platform_fee: float
    ) -> bool:
        """
        Create a pending payment record.
        
        Args:
            claim_reference: Claim reference
            client_email: Client email
            total_amount: Total amount recovered
            client_share: Amount to pay to client
            platform_fee: Your commission
            
        Returns:
            True if successful
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO manual_payments
                (claim_reference, client_email, total_amount, client_share, 
                 platform_fee, payment_status)
                VALUES (?, ?, ?, ?, ?, 'pending')
            """, (claim_reference, client_email, total_amount, client_share, platform_fee))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Payment created: {claim_reference} - {client_share}€ to {client_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create payment: {e}")
            return False
    
    def mark_payment_as_paid(
        self,
        claim_reference: str,
        payment_method: str = "virement",
        transaction_reference: Optional[str] = None,
        notes: Optional[str] = None
    ) -> bool:
        """
        Mark a payment as completed.
        
        Args:
            claim_reference: Claim reference
            payment_method: Payment method (virement, cheque, etc.)
            transaction_reference: Bank transaction reference
            notes: Optional notes
            
        Returns:
            True if successful
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE manual_payments
                SET payment_status = 'paid',
                    payment_date = CURRENT_TIMESTAMP,
                    payment_method = ?,
                    transaction_reference = ?,
                    notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE claim_reference = ?
            """, (payment_method, transaction_reference, notes, claim_reference))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Payment marked as paid: {claim_reference}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark payment as paid: {e}")
            return False
    
    def get_pending_payments(self) -> List[Dict[str, Any]]:
        """Get all pending payments."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    mp.claim_reference,
                    mp.client_email,
                    mp.total_amount,
                    mp.client_share,
                    mp.platform_fee,
                    mp.created_at,
                    cb.iban,
                    cb.account_holder_name,
                    cb.bank_name
                FROM manual_payments mp
                LEFT JOIN client_bank_info cb ON mp.client_email = cb.client_email
                WHERE mp.payment_status = 'pending'
                ORDER BY mp.created_at DESC
            """)
            
            rows = cursor.fetchall()
            conn.close()
            
            payments = []
            for row in rows:
                payments.append({
                    'claim_reference': row[0],
                    'client_email': row[1],
                    'total_amount': row[2],
                    'client_share': row[3],
                    'platform_fee': row[4],
                    'created_at': row[5],
                    'iban': row[6],
                    'account_holder_name': row[7],
                    'bank_name': row[8],
                    'has_bank_info': row[6] is not None
                })
            
            return payments
            
        except Exception as e:
            logger.error(f"Failed to get pending payments: {e}")
            return []
    
    def get_payment_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get payment history."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    claim_reference,
                    client_email,
                    client_share,
                    payment_status,
                    payment_date,
                    payment_method,
                    transaction_reference
                FROM manual_payments
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            history = []
            for row in rows:
                history.append({
                    'claim_reference': row[0],
                    'client_email': row[1],
                    'client_share': row[2],
                    'payment_status': row[3],
                    'payment_date': row[4],
                    'payment_method': row[5],
                    'transaction_reference': row[6]
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to get payment history: {e}")
            return []


# Convenience functions
def add_bank_info(client_email: str, iban: str, **kwargs) -> bool:
    """Add client bank information."""
    manager = ManualPaymentManager()
    return manager.add_client_bank_info(client_email, iban, **kwargs)


def create_pending_payment(
    claim_reference: str,
    client_email: str,
    total_amount: float,
    commission_rate: float = 0.20
) -> bool:
    """Create a pending payment."""
    manager = ManualPaymentManager()
    client_share = total_amount * (1 - commission_rate)
    platform_fee = total_amount * commission_rate
    
    return manager.create_payment(
        claim_reference, client_email, total_amount, client_share, platform_fee
    )


def mark_as_paid(claim_reference: str, **kwargs) -> bool:
    """Mark payment as completed."""
    manager = ManualPaymentManager()
    return manager.mark_payment_as_paid(claim_reference, **kwargs)


if __name__ == "__main__":
    # Test manual payment manager
    print("="*70)
    print("MANUAL PAYMENT MANAGER - Test")
    print("="*70)
    
    manager = ManualPaymentManager()
    
    # Test 1: Add bank info
    print("\n1. Adding client bank info...")
    success = manager.add_client_bank_info(
        client_email="client@test.com",
        iban="FR7630006000011234567890189",
        bic="BNPAFRPP",
        account_holder_name="Jean Dupont",
        bank_name="BNP Paribas"
    )
    print(f"   {'✅' if success else '❌'} Bank info added")
    
    # Test 2: Create pending payment
    print("\n2. Creating pending payment...")
    success = create_pending_payment(
        claim_reference="CLM-TEST-001",
        client_email="client@test.com",
        total_amount=100.0
    )
    print(f"   {'✅' if success else '❌'} Payment created")
    
    # Test 3: Get pending payments
    print("\n3. Getting pending payments...")
    pending = manager.get_pending_payments()
    print(f"   Found {len(pending)} pending payment(s)")
    if pending:
        for p in pending:
            print(f"   - {p['claim_reference']}: {p['client_share']}€ to {p['client_email']}")
            print(f"     IBAN: {p['iban'] or 'Not provided'}")
    
    # Test 4: Mark as paid
    print("\n4. Marking payment as paid...")
    success = mark_as_paid(
        claim_reference="CLM-TEST-001",
        payment_method="Virement bancaire",
        transaction_reference="VIR-2026-001"
    )
    print(f"   {'✅' if success else '❌'} Payment marked as paid")
    
    # Test 5: Check history
    print("\n5. Payment history...")
    history = manager.get_payment_history(limit=5)
    print(f"   Found {len(history)} payment(s) in history")
    
    print("\n" + "="*70)
    print("✅ Test Complete")
    print("="*70)
