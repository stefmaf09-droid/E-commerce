"""
Magic Links generator for secure, time-limited OAuth authorization links.

Generates unique, secure links that allow clients to authorize API access in 1 click.
"""

import secrets
import hashlib
from typing import Dict, Optional
from datetime import datetime, timedelta
import sqlite3
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class MagicLinksManager:
    """Manage magic links for OAuth authorization."""
    
    def __init__(self, db_path: str = "database/credentials.db", base_url: str = "http://localhost:5000"):
        """
        Initialize magic links manager.
        
        Args:
            db_path: Path to SQLite database
            base_url: Base URL of the application (for generating callback URLs)
        """
        self.db_path = db_path
        self.base_url = base_url.rstrip('/')
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """Create magic_links table if it doesn't exist."""
        Path(self.db_path).parent.mkdir(exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS magic_links (
                link_id TEXT PRIMARY KEY,
                client_email TEXT NOT NULL,
                platform TEXT NOT NULL,
                token_hash TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                used BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                used_at TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("Magic links table ensured")
    
    def generate_magic_link(
        self, 
        client_email: str, 
        platform: str,
        expires_in_hours: int = 24
    ) -> Dict[str, str]:
        """
        Generate a magic link for OAuth authorization.
        
        Args:
            client_email: Client's email address
            platform: Platform name ('shopify', 'woocommerce', etc.)
            expires_in_hours: Link expiration time in hours
            
        Returns:
            Dictionary with 'link_id', 'token', 'url', and 'expires_at'
        """
        # Generate unique link ID and secret token
        link_id = secrets.token_urlsafe(16)
        secret_token = secrets.token_urlsafe(32)
        
        # Hash the token for storage
        token_hash = hashlib.sha256(secret_token.encode()).hexdigest()
        
        # Calculate expiration
        expires_at = datetime.now() + timedelta(hours=expires_in_hours)
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO magic_links 
            (link_id, client_email, platform, token_hash, expires_at)
            VALUES (?, ?, ?, ?, ?)
        """, (link_id, client_email, platform, token_hash, expires_at))
        
        conn.commit()
        conn.close()
        
        # Generate the full URL
        magic_url = f"{self.base_url}/oauth/authorize/{link_id}?token={secret_token}"
        
        logger.info(f"Generated magic link for {client_email} ({platform})")
        
        return {
            'link_id': link_id,
            'token': secret_token,
            'url': magic_url,
            'expires_at': expires_at.isoformat()
        }
    
    def validate_magic_link(self, link_id: str, token: str) -> Optional[Dict[str, str]]:
        """
        Validate a magic link and return client info if valid.
        
        Args:
            link_id: Link identifier
            token: Secret token
            
        Returns:
            Dictionary with client info if valid, None otherwise
        """
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT client_email, platform, expires_at, used
            FROM magic_links
            WHERE link_id = ? AND token_hash = ?
        """, (link_id, token_hash))
        
        result = cursor.fetchone()
        
        if not result:
            logger.warning(f"Invalid magic link: {link_id}")
            conn.close()
            return None
        
        client_email, platform, expires_at_str, used = result
        expires_at = datetime.fromisoformat(expires_at_str)
        
        # Check if expired
        if datetime.now() > expires_at:
            logger.warning(f"Expired magic link: {link_id}")
            conn.close()
            return None
        
        # Check if already used
        if used:
            logger.warning(f"Already used magic link: {link_id}")
            conn.close()
            return None
        
        conn.close()
        
        logger.info(f"Valid magic link for {client_email} ({platform})")
        
        return {
            'client_email': client_email,
            'platform': platform,
            'link_id': link_id
        }
    
    def mark_as_used(self, link_id: str) -> bool:
        """
        Mark a magic link as used.
        
        Args:
            link_id: Link identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE magic_links
                SET used = 1, used_at = CURRENT_TIMESTAMP
                WHERE link_id = ?
            """, (link_id,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Marked magic link as used: {link_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark link as used: {e}")
            return False
    
    def cleanup_expired_links(self) -> int:
        """
        Delete expired magic links from database.
        
        Returns:
            Number of deleted links
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM magic_links
                WHERE expires_at < CURRENT_TIMESTAMP
            """)
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            logger.info(f"Cleaned up {deleted_count} expired magic links")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired links: {e}")
            return 0
    
    def get_link_stats(self, client_email: str) -> Dict[str, int]:
        """
        Get statistics for magic links of a specific client.
        
        Args:
            client_email: Client's email
            
        Returns:
            Dictionary with 'total', 'used', 'expired', 'active' counts
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total links
            cursor.execute("""
                SELECT COUNT(*) FROM magic_links WHERE client_email = ?
            """, (client_email,))
            total = cursor.fetchone()[0]
            
            # Used links
            cursor.execute("""
                SELECT COUNT(*) FROM magic_links WHERE client_email = ? AND used = 1
            """, (client_email,))
            used = cursor.fetchone()[0]
            
            # Expired links
            cursor.execute("""
                SELECT COUNT(*) FROM magic_links 
                WHERE client_email = ? AND expires_at < CURRENT_TIMESTAMP AND used = 0
            """, (client_email,))
            expired = cursor.fetchone()[0]
            
            # Active links
            cursor.execute("""
                SELECT COUNT(*) FROM magic_links 
                WHERE client_email = ? AND expires_at >= CURRENT_TIMESTAMP AND used = 0
            """, (client_email,))
            active = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total': total,
                'used': used,
                'expired': expired,
                'active': active
            }
            
        except Exception as e:
            logger.error(f"Failed to get link stats: {e}")
            return {'total': 0, 'used': 0, 'expired': 0, 'active': 0}
