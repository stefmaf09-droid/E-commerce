"""
Onboarding Manager - Track and manage client onboarding progress.

Handles step-by-step onboarding flow for new clients.
"""

import sqlite3
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class OnboardingManager:
    """Manage client onboarding status and progression."""
    
    def __init__(self, client_email: Optional[str] = None, db_path: str = "database/client_data.db"):
        """Initialize onboarding manager."""
        self.client_email = client_email
        self.db_path = db_path
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """Create onboarding_status table if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS onboarding_status (
                client_email TEXT PRIMARY KEY,
                account_created BOOLEAN DEFAULT TRUE,
                store_connected BOOLEAN DEFAULT FALSE,
                bank_info_added BOOLEAN DEFAULT FALSE,
                onboarding_complete BOOLEAN DEFAULT FALSE,
                current_step INTEGER DEFAULT 1,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def get_onboarding_status(self, client_email: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current onboarding status for client.
        
        Args:
            client_email: Optional email, uses self.client_email if not provided
        
        Returns:
            Dictionary with status of each step
        """
        email = client_email or self.client_email
        if not email:
            raise ValueError("client_email must be provided either in constructor or method call")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                account_created,
                store_connected,
                bank_info_added,
                onboarding_complete,
                current_step
            FROM onboarding_status
            WHERE client_email = ?
        """, (email,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'account_created': bool(row[0]),
                'store_connected': bool(row[1]),
                'bank_info_added': bool(row[2]),
                'onboarding_complete': bool(row[3]),
                'current_step': row[4]
            }
        else:
            # Return default status (not yet initialized)
            return {
                'account_created': False,
                'store_connected': False,
                'bank_info_added': False,
                'onboarding_complete': False,
                'current_step': 0
            }
    
    def initialize_onboarding(self, client_email: Optional[str] = None) -> Dict[str, Any]:
        """Initialize onboarding record for new client."""
        email = client_email or self.client_email
        if not email:
            raise ValueError("client_email must be provided either in constructor or method call")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR IGNORE INTO onboarding_status
            (client_email, account_created, current_step)
            VALUES (?, TRUE, 1)
        """, (email,))
        
        conn.commit()
        conn.close()
        
        return {
            'account_created': True,
            'store_connected': False,
            'bank_info_added': False,
            'onboarding_complete': False,
            'current_step': 1
        }
    
    def get_current_step(self, client_email: Optional[str] = None) -> str:
        """
        Get current onboarding step name.
        
        Args:
            client_email: Optional email, uses self.client_email if not provided
        
        Returns:
            Step name ('store_setup', 'bank_info', 'welcome')
        """
        status = self.get_onboarding_status(client_email)
        
        # Map to step names
        if not status['store_connected']:
            return 'store_setup'
        elif not status['bank_info_added']:
            return 'bank_info'
        else:
            return 'welcome'
    
    def mark_step_complete(self, client_email: str, step: str) -> bool:
        """
        Mark a specific step as complete.
        
        Args:
            client_email: Client email
            step: Step name ('store_setup', 'bank_info', 'welcome')
            
        Returns:
            True if successful
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Map step names to database columns and step index
            step_mapping = {
                'store_setup': ('store_connected', 1),
                'bank_info': ('bank_info_added', 2),
                'welcome': ('onboarding_complete', 3)
            }

            mapping = step_mapping.get(step)
            if not mapping:
                logger.warning(f"Unknown step: {step}")
                return False
            db_column, step_index = mapping

            # Update the specific step and current_step
            cursor.execute(f"""
                UPDATE onboarding_status
                SET {db_column} = TRUE,
                    current_step = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE client_email = ?
            """, (step_index, client_email))

            # Vérification de cohérence
            cursor.execute("SELECT store_connected, bank_info_added, onboarding_complete, current_step FROM onboarding_status WHERE client_email = ?", (client_email,))
            row = cursor.fetchone()
            if row:
                expected_step = 1
                if row[0]: expected_step = 2
                if row[1]: expected_step = 3
                if row[2]: expected_step = 3
                if row[3] != expected_step:
                    logger.warning(f"Désynchronisation onboarding: current_step={row[3]}, attendu={expected_step} pour {client_email}")

            conn.commit()
            conn.close()

            logger.info(f"Onboarding step '{step}' completed for {client_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to mark step complete: {e}")
            return False
    
    def mark_step_incomplete(self, client_email: str, step: str) -> bool:
        """
        Mark a specific step as incomplete (for back navigation).
        
        Args:
            client_email: Client email
            step: Step name ('store_setup', 'bank_info', 'welcome')
            
        Returns:
            True if successful
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Map step names to database columns
            step_mapping = {
                'store_setup': 'store_connected',
                'bank_info': 'bank_info_added',
                'welcome': 'onboarding_complete'
            }
            
            db_column = step_mapping.get(step)
            if not db_column:
                logger.warning(f"Unknown step: {step}")
                return False
            
            # Update the specific step
            cursor.execute(f"""
                UPDATE onboarding_status
                SET {db_column} = FALSE,
                    updated_at = CURRENT_TIMESTAMP
                WHERE client_email = ?
            """, (client_email,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Onboarding step '{step}' marked incomplete for {client_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark step incomplete: {e}")
            return False
    
    def mark_complete(self, client_email: Optional[str] = None) -> bool:
        """
        Mark entire onboarding as complete.
        
        Args:
            client_email: Optional email, uses self.client_email if not provided
        
        Returns:
            True if successful
        """
        email = client_email or self.client_email
        if not email:
            raise ValueError("client_email must be provided either in constructor or method call")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE onboarding_status
                SET onboarding_complete = TRUE,
                    completed_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE client_email = ?
            """, (email,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Onboarding completed for {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark onboarding complete: {e}")
            return False
    
    def is_onboarding_complete(self, client_email: Optional[str] = None) -> bool:
        """
        Check if onboarding is complete.
        
        Args:
            client_email: Optional email, uses self.client_email if not provided
        
        Returns:
            True if onboarding is finished
        """
        status = self.get_onboarding_status(client_email)
        return status['onboarding_complete']


if __name__ == "__main__":
    # Test onboarding manager
    print("="*70)
    print("ONBOARDING MANAGER - Test")
    print("="*70)
    
    test_email = "test@example.com"
    manager = OnboardingManager(test_email)
    
    # Test 1: Get initial status
    print("\n1. Initial status:")
    status = manager.get_onboarding_status()
    print(f"   Current step: {status['current_step']}")
    print(f"   Store connected: {status['store_connected']}")
    print(f"   Complete: {status['onboarding_complete']}")
    
    # Test 2: Mark store connected
    print("\n2. Marking store as connected...")
    manager.mark_step_complete('store_connected')
    status = manager.get_onboarding_status()
    print(f"   Current step: {status['current_step']}")
    print(f"   Store connected: {status['store_connected']}")
    
    # Test 3: Mark bank info added
    print("\n3. Marking bank info added...")
    manager.mark_step_complete('bank_info_added')
    status = manager.get_onboarding_status()
    print(f"   Current step: {status['current_step']}")
    print(f"   Bank info: {status['bank_info_added']}")
    
    # Test 4: Complete onboarding
    print("\n4. Completing onboarding...")
    manager.mark_complete()
    print(f"   Is complete: {manager.is_onboarding_complete()}")
    
    print("\n" + "="*70)
    print("✅ Test Complete")
    print("="*70)
