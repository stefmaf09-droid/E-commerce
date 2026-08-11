"""
Secure credentials management with encryption - MULTI-STORE SUPPORT.
Stores API keys, OAuth tokens, and other sensitive credentials securely.
Supports multiple stores per client.

Storage backend follows DATABASE_TYPE (see src.config.Config), same as
PasswordManager: SQLite locally, or the shared Supabase/Neon Postgres
database in production, so credentials don't live only on a local disk
that can be wiped or out of sync with the rest of the app's data.
"""

import os
import json
import sqlite3
from typing import Dict, Optional, Any, List
from cryptography.fernet import Fernet
from pathlib import Path
import logging

from src.config import Config

logger = logging.getLogger(__name__)


class CredentialsManager:
    """Manage encrypted storage of API credentials with multi-store support."""

    def __init__(self, db_path: str = "database/credentials.db"):
        """
        Initialize the credentials manager.
        """
        self.db_path = db_path
        self.db_type = (Config.get('DATABASE_TYPE', 'sqlite') or 'sqlite').lower()
        self._ensure_db_exists()
        self._encryption_key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self._encryption_key)

    def _get_connection(self):
        """Open a new connection to the active backend (SQLite or Postgres)."""
        if self.db_type == 'sqlite':
            return sqlite3.connect(self.db_path)
        from src.database.database_manager import create_postgres_connection
        return create_postgres_connection(Config.get_database_url())

    def _q(self, query: str) -> str:
        """Adapt a query written with '?' placeholders to the active backend."""
        return query.replace('?', '%s') if self.db_type != 'sqlite' else query

    @staticmethod
    def _as_bytes(value) -> bytes:
        """Normalize a BYTEA/BLOB column read back from either backend to bytes
        (psycopg2 can hand back a memoryview for BYTEA columns)."""
        if isinstance(value, memoryview):
            return bytes(value)
        return value

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
        if self.db_type == 'sqlite':
            Path(self.db_path).parent.mkdir(exist_ok=True)

        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            if self.db_type == 'sqlite':
                # Check if we need to migrate from old schema
                cursor.execute("PRAGMA table_info(credentials)")
                columns = [col[1] for col in cursor.fetchall()]

                if columns and 'id' not in columns:
                    logger.info("Migrating credentials table to multi-store schema...")
                    # Drop and recreate (old single-store schema)
                    cursor.execute("DROP TABLE credentials")
                    cursor.execute("DROP TABLE sync_status")

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
            else:
                # Postgres: no legacy single-store schema to migrate from.
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS credentials (
                        id SERIAL PRIMARY KEY,
                        client_id TEXT NOT NULL,
                        platform TEXT NOT NULL,
                        store_name TEXT,
                        credentials_encrypted BYTEA NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(client_id, platform, store_name)
                    )
                """)

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sync_status (
                        id SERIAL PRIMARY KEY,
                        credential_id INTEGER NOT NULL,
                        last_sync TIMESTAMP,
                        last_order_id TEXT,
                        status TEXT DEFAULT 'active',
                        FOREIGN KEY (credential_id) REFERENCES credentials(id)
                    )
                """)

            conn.commit()
        finally:
            conn.close()
        logger.info(f"Credentials database initialized (backend: {self.db_type})")

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

            conn = self._get_connection()
            cursor = conn.cursor()

            if self.db_type == 'sqlite':
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
            else:
                cursor.execute("""
                    INSERT INTO credentials
                    (client_id, platform, store_name, credentials_encrypted, updated_at)
                    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (client_id, platform, store_name) DO UPDATE
                    SET credentials_encrypted = EXCLUDED.credentials_encrypted,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING id
                """, (client_id, platform, store_name, encrypted))

                credential_id = cursor.fetchone()[0]

                cursor.execute("""
                    INSERT INTO sync_status (credential_id)
                    VALUES (%s)
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
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(self._q("""
                SELECT id, platform, store_name, credentials_encrypted
                FROM credentials
                WHERE client_id = ?
                ORDER BY created_at
            """), (client_id,))

            results = cursor.fetchall()
            conn.close()

            stores = []
            for row in results:
                store_id, platform, store_name, encrypted = row
                decrypted = self.cipher.decrypt(self._as_bytes(encrypted))
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

    def list_clients(self) -> List[tuple]:
        """List all unique clients and their platforms."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT client_id, platform, created_at FROM credentials")
            results = cursor.fetchall()
            conn.close()
            return results
        except Exception as e:
            logger.error(f"Failed to list clients: {e}")
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
            conn = self._get_connection()
            cursor = conn.cursor()

            if store_id:
                cursor.execute(self._q("DELETE FROM sync_status WHERE credential_id = ?"), (store_id,))
                cursor.execute(self._q("DELETE FROM credentials WHERE id = ? AND client_id = ?"), (store_id, client_id))
            else:
                cursor.execute(self._q("""
                    DELETE FROM sync_status
                    WHERE credential_id IN (SELECT id FROM credentials WHERE client_id = ?)
                """), (client_id,))
                cursor.execute(self._q("DELETE FROM credentials WHERE client_id = ?"), (client_id,))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Failed to delete credentials: {e}")
            return False
