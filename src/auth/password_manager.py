"""
Password Management Module - Secure password hashing and verification.

Uses bcrypt for secure password hashing with salt.

Storage backend follows DATABASE_TYPE (see src.config.Config):
- 'sqlite' (default, local dev): a local file at db_path.
- 'postgres': the same Supabase/Neon Postgres database used for the rest of
  the app (clients, disputes, ...), via src.database.database_manager's
  connection helper. This keeps logins in sync with client records instead
  of living in a local SQLite file that can be out of sync with (or wiped
  independently of) the production database.
"""

import bcrypt
import sqlite3
import logging
from pathlib import Path
from typing import Optional

from src.config import Config

logger = logging.getLogger(__name__)


class PasswordManager:
    """Manage client passwords with bcrypt hashing."""

    def __init__(self, db_path: str = "database/passwords.db"):
        """
        Initialize the password manager.

        Args:
            db_path: Path to the SQLite database file (used only when
                DATABASE_TYPE is 'sqlite' or unset).
        """
        self.db_path = db_path
        self.db_type = (Config.get('DATABASE_TYPE', 'sqlite') or 'sqlite').lower()
        self._ensure_db_exists()

    def _get_connection(self):
        """Open a new connection to the active backend (SQLite or Postgres)."""
        if self.db_type == 'sqlite':
            return sqlite3.connect(self.db_path)
        from src.database.database_manager import create_postgres_connection
        return create_postgres_connection(Config.get_database_url())

    def _q(self, query: str) -> str:
        """Adapt a query written with '?' placeholders to the active backend."""
        return query.replace('?', '%s') if self.db_type != 'sqlite' else query

    def _ensure_db_exists(self):
        """Create the database and tables if they don't exist."""
        if self.db_type == 'sqlite':
            Path(self.db_path).parent.mkdir(exist_ok=True)

        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            if self.db_type == 'sqlite':
                # Check if table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='client_passwords'")
                table_exists = cursor.fetchone()

                if not table_exists:
                    cursor.execute("""
                        CREATE TABLE client_passwords (
                            client_email TEXT PRIMARY KEY,
                            password_hash TEXT NOT NULL,
                            role TEXT DEFAULT 'client',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                else:
                    # Check if role column exists (Migration)
                    cursor.execute("PRAGMA table_info(client_passwords)")
                    columns = [col[1] for col in cursor.fetchall()]
                    if 'role' not in columns:
                        logger.info("Migrating client_passwords table: adding 'role' column")
                        cursor.execute("ALTER TABLE client_passwords ADD COLUMN role TEXT DEFAULT 'client'")
            else:
                # Postgres: idempotent single statement, no migration needed
                # since 'role' is part of the table from creation.
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS client_passwords (
                        client_email TEXT PRIMARY KEY,
                        password_hash TEXT NOT NULL,
                        role TEXT DEFAULT 'client',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

            conn.commit()
        finally:
            conn.close()
        logger.info(f"Password database initialized (backend: {self.db_type})")

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

    def set_client_password(self, client_email: str, password: str, role: str = None) -> bool:
        """
        Set or update a client's password.

        Args:
            client_email: Client email address
            password: Plain text password
            role: Optional role to set (defaults to 'client' for new users if not provided)

        Returns:
            True if successful, False otherwise
        """
        try:
            hashed = self.hash_password(password)

            conn = self._get_connection()
            cursor = conn.cursor()

            # Check if user exists to decide on role behavior
            cursor.execute(self._q("SELECT role FROM client_passwords WHERE client_email = ?"), (client_email,))
            existing = cursor.fetchone()

            if existing:
                # Update existing user - preserve role unless explicitly changed
                if role:
                    cursor.execute(self._q("""
                        UPDATE client_passwords
                        SET password_hash = ?, role = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE client_email = ?
                    """), (hashed, role, client_email))
                else:
                    cursor.execute(self._q("""
                        UPDATE client_passwords
                        SET password_hash = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE client_email = ?
                    """), (hashed, client_email))
            else:
                # New user
                user_role = role if role else 'client'
                cursor.execute(self._q("""
                    INSERT INTO client_passwords
                    (client_email, password_hash, role, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """), (client_email, hashed, user_role))

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
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(self._q("""
                SELECT password_hash
                FROM client_passwords
                WHERE client_email = ?
            """), (client_email,))

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

    def get_user_role(self, client_email: str) -> str:
        """
        Get the role of a user.

        Args:
            client_email: Client email address

        Returns:
            Role string (e.g., 'admin', 'client') or 'client' if not found/error
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(self._q("SELECT role FROM client_passwords WHERE client_email = ?"), (client_email,))
            result = cursor.fetchone()
            conn.close()

            if result and result[0]:
                return result[0]
            return 'client'

        except Exception as e:
            logger.error(f"Failed to get user role: {e}")
            return 'client'

    def set_user_role(self, client_email: str, role: str) -> bool:
        """
        Set the role for a user.

        Args:
            client_email: Client email address
            role: Role to set ('admin', 'client')

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(self._q("""
                UPDATE client_passwords
                SET role = ?, updated_at = CURRENT_TIMESTAMP
                WHERE client_email = ?
            """), (role, client_email))

            rows = cursor.rowcount
            conn.commit()
            conn.close()

            if rows > 0:
                logger.info(f"Role set to {role} for {client_email}")
                return True
            else:
                logger.warning(f"User {client_email} not found when setting role")
                return False

        except Exception as e:
            logger.error(f"Failed to set user role: {e}")
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
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(self._q("""
                SELECT COUNT(*)
                FROM client_passwords
                WHERE client_email = ?
            """), (client_email,))

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
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(self._q("""
                DELETE FROM client_passwords
                WHERE client_email = ?
            """), (client_email,))

            conn.commit()
            conn.close()

            logger.info(f"Password deleted for {client_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete password: {e}")
            return False

    def get_all_users(self) -> list:
        """
        Get all users and their roles.

        Returns:
            List of dictionaries containing user details (email, role, created_at)
        """
        try:
            conn = self._get_connection()

            if self.db_type == 'sqlite':
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
            else:
                from psycopg2 import extras
                cursor = conn.cursor(cursor_factory=extras.DictCursor)

            cursor.execute("""
                SELECT client_email, role, created_at, updated_at
                FROM client_passwords
                ORDER BY created_at DESC
            """)

            users = [dict(row) for row in cursor.fetchall()]
            conn.close()

            return users

        except Exception as e:
            logger.error(f"Failed to get all users: {e}")
            return []


# Convenience functions for easy import
def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return PasswordManager.hash_password(password)


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return PasswordManager.verify_password(password, hashed)


def set_client_password(client_email: str, password: str, role: str = None) -> bool:
    """Set or update a client's password."""
    manager = PasswordManager()
    return manager.set_client_password(client_email, password, role)


def verify_client_password(client_email: str, password: str) -> bool:
    """Verify a client's password."""
    manager = PasswordManager()
    return manager.verify_client_password(client_email, password)


def get_user_role(client_email: str) -> str:
    """Get the role of a user."""
    manager = PasswordManager()
    return manager.get_user_role(client_email)


def set_user_role(client_email: str, role: str) -> bool:
    """Set the role for a user."""
    manager = PasswordManager()
    return manager.set_user_role(client_email, role)


def has_password(client_email: str) -> bool:
    """Check if a client has a password set."""
    manager = PasswordManager()
    return manager.has_password(client_email)
