"""
Password Management Module - Secure password hashing and verification.

Uses bcrypt for secure password hashing with salt.
"""

import bcrypt
import sqlite3
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class PasswordManager:
    """Manage client passwords with bcrypt hashing."""
    
    def __init__(self, db_path: str = "database/passwords.db"):
        """
        Initialize the password manager.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """Create the database and tables if they don't exist."""
        Path(self.db_path).parent.mkdir(exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS client_passwords (
                client_email TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"Password database initialized at {self.db_path}")
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password as string
        """
        # Generate salt and hash password
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            password: Plain text password to verify
            hashed: Hashed password from database
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    def set_client_password(self, client_email: str, password: str) -> bool:
        """
        Set or update a client's password.
        
        Args:
            client_email: Client email address
            password: Plain text password
            
        Returns:
            True if successful, False otherwise
        """
        try:
            hashed = self.hash_password(password)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO client_passwords 
                (client_email, password_hash, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (client_email, hashed))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Password set for {client_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set password: {e}")
            return False
    
    def verify_client_password(self, client_email: str, password: str) -> bool:
        """
        Verify a client's password.
        
        Args:
            client_email: Client email address
            password: Plain text password to verify
            
        Returns:
            True if password is correct, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT password_hash 
                FROM client_passwords 
                WHERE client_email = ?
            """, (client_email,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                stored_hash = result[0]
                return self.verify_password(password, stored_hash)
            else:
                logger.warning(f"No password found for {client_email}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to verify password: {e}")
            return False
    
    def has_password(self, client_email: str) -> bool:
        """
        Check if a client has a password set.
        
        Args:
            client_email: Client email address
            
        Returns:
            True if password exists, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) 
                FROM client_passwords 
                WHERE client_email = ?
            """, (client_email,))
            
            count = cursor.fetchone()[0]
            conn.close()
            
            return count > 0
            
        except Exception as e:
            logger.error(f"Failed to check password existence: {e}")
            return False
    
    def delete_password(self, client_email: str) -> bool:
        """
        Delete a client's password (RGPD compliance).
        
        Args:
            client_email: Client email address
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM client_passwords 
                WHERE client_email = ?
            """, (client_email,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Password deleted for {client_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete password: {e}")
            return False


# Convenience functions for easy import
def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return PasswordManager.hash_password(password)


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return PasswordManager.verify_password(password, hashed)


def set_client_password(client_email: str, password: str) -> bool:
    """Set or update a client's password."""
    manager = PasswordManager()
    return manager.set_client_password(client_email, password)


def verify_client_password(client_email: str, password: str) -> bool:
    """Verify a client's password."""
    manager = PasswordManager()
    return manager.verify_client_password(client_email, password)


def has_password(client_email: str) -> bool:
    """Check if a client has a password set."""
    manager = PasswordManager()
    return manager.has_password(client_email)


if __name__ == "__main__":
    # Test the password manager
    print("="*70)
    print("PASSWORD MANAGER - Test")
    print("="*70)
    
    test_email = "test@example.com"
    test_password = "SecurePassword123!"
    
    # Set password
    print(f"\n1. Setting password for {test_email}...")
    success = set_client_password(test_email, test_password)
    print(f"   ✅ Success: {success}")
    
    # Verify correct password
    print(f"\n2. Verifying correct password...")
    is_valid = verify_client_password(test_email, test_password)
    print(f"   ✅ Valid: {is_valid}")
    
    # Verify wrong password
    print(f"\n3. Verifying wrong password...")
    is_valid = verify_client_password(test_email, "WrongPassword")
    print(f"   ❌ Valid: {is_valid} (should be False)")
    
    # Check if password exists
    print(f"\n4. Checking if password exists...")
    exists = has_password(test_email)
    print(f"   ✅ Exists: {exists}")
    
    print("\n" + "="*70)
    print("✅ Test Complete")
    print("="*70)
