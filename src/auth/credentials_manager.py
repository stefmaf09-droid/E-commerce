"""
Secure credentials management with encryption - MULTI-STORE SUPPORT.
Stores API keys, OAuth tokens, and other sensitive credentials securely.
Supports multiple stores per client.
"""

import os
import json
import sqlite3
from typing import Dict, Optional, Any, List
from cryptography.fernet import Fernet
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class CredentialsManager:
    """Manage encrypted storage of API credentials with multi-store support."""
    
    def __init__(self, db_path: str = "database/credentials.db"):
        """
        Initialize the credentials manager.
        """
        self.db_path = db_path
        self._ensure_db_exists()
        self._encryption_key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self._encryption_key)
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get existing encryption key or create a new one."""
        key_file = Path("config/.secret_key")
        key_file.parent.mkdir(exist_ok=True)
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)
            return key
    
    def _ensure_db_exists(self):
        """Create the database and tables if they don't exist."""
        Path(self.db_path).parent.mkdir(exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if we need to migrate from old schema
        cursor.execute("PRAGMA table_info(credentials)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if columns and 'id' not in columns:
            logger.info("Migrating credentials table to multi-store schema...")
            # Backup old data
            cursor.execute("SELECT * FROM credentials")
            old_rows = cursor.fetchall()
            
            # Drop and recreate
            cursor.execute("DROP TABLE credentials")
            cursor.execute("DROP TABLE sync_status")
        
        # Create new tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                store_name TEXT,
                credentials_encrypted BLOB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(client_id, platform, store_name)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                credential_id INTEGER NOT NULL,
                last_sync TIMESTAMP,
                last_order_id TEXT,
                status TEXT DEFAULT 'active',
                FOREIGN KEY (credential_id) REFERENCES credentials(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def store_credentials(
        self, 
        client_id: str, 
        platform: str, 
        credentials: Dict[str, Any],
        store_name: str = None
    ) -> bool:
        """Store encrypted credentials."""
        try:
            if not store_name:
                store_name = credentials.get('shop_url', f'{platform.capitalize()} Store')
            
            credentials_json = json.dumps(credentials)
            encrypted = self.cipher.encrypt(credentials_json.encode())
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO credentials 
                (client_id, platform, store_name, credentials_encrypted, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (client_id, platform, store_name, encrypted))
            
            credential_id = cursor.lastrowid
            
            cursor.execute("""
                INSERT OR IGNORE INTO sync_status (credential_id)
                VALUES (?)
            """, (credential_id,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Failed to store credentials: {e}")
            return False
    
    def get_all_stores(self, client_id: str) -> List[Dict[str, Any]]:
        """Retrieve all stores for a client."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, platform, store_name, credentials_encrypted 
                FROM credentials 
                WHERE client_id = ?
                ORDER BY created_at
            """, (client_id,))
            
            results = cursor.fetchall()
            conn.close()
            
            stores = []
            for row in results:
                store_id, platform, store_name, encrypted = row
                decrypted = self.cipher.decrypt(encrypted)
                credentials = json.loads(decrypted.decode())
                
                stores.append({
                    'id': store_id,
                    'platform': platform,
                    'store_name': store_name or credentials.get('shop_url', f'{platform.capitalize()} Store'),
                    'credentials': credentials
                })
            return stores
        except Exception as e:
            logger.error(f"Failed to get stores: {e}")
            return []

    def get_credentials(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Backward compatibility for single store retrieval."""
        stores = self.get_all_stores(client_id)
        if stores:
            creds = stores[0]['credentials']
            creds['platform'] = stores[0]['platform']
            return creds
        return None
    
    def delete_credentials(self, client_id: str, store_id: int = None) -> bool:
        """Delete credentials."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if store_id:
                cursor.execute("DELETE FROM sync_status WHERE credential_id = ?", (store_id,))
                cursor.execute("DELETE FROM credentials WHERE id = ? AND client_id = ?", (store_id, client_id))
            else:
                cursor.execute("""
                    DELETE FROM sync_status 
                    WHERE credential_id IN (SELECT id FROM credentials WHERE client_id = ?)
                """, (client_id,))
                cursor.execute("DELETE FROM credentials WHERE client_id = ?", (client_id,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Failed to delete credentials: {e}")
            return False
