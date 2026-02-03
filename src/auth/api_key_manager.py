
import secrets
import hashlib
from typing import Optional, Tuple
from src.database.database_manager import get_db_manager

class APIKeyManager:
    """Gère les clés d'API sécurisées pour les clients Enterprise."""
    
    def __init__(self, db_manager=None):
        self.db = db_manager or get_db_manager()

    def generate_key(self, client_id: int, name: str = "Default Key") -> str:
        """Génère une nouvelle clé d'API (non réversible)."""
        raw_key = f"rk_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        conn = self.db.get_connection()
        try:
            conn.execute("""
                INSERT INTO api_keys (client_id, key_hash, name, prefix)
                VALUES (?, ?, ?, ?)
            """, (client_id, key_hash, name, raw_key[:6]))
            conn.commit()
            return raw_key # Seul moment où la clé brute est visible
        finally:
            conn.close()

    def verify_key(self, raw_key: str) -> Optional[int]:
        """Vérifie la clé et retourne le client_id associé."""
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        conn = self.db.get_connection()
        try:
            row = conn.execute("""
                SELECT client_id FROM api_keys 
                WHERE key_hash = ? AND is_active = 1
            """, (key_hash,)).fetchone()
            return row[0] if row else None
        finally:
            conn.close()
