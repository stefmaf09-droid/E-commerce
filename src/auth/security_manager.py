
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from src.database.database_manager import get_db_manager

logger = logging.getLogger(__name__)

class SecurityManager:
    """Gère la sécurité, l'audit et les contrôles d'accès de grade bancaire."""
    
    def __init__(self, db_manager=None):
        self.db = db_manager or get_db_manager()

    def log_action(self, 
                   user_id: int, 
                   user_type: str, 
                   action: str, 
                   resource_type: str, 
                   resource_id: int, 
                   prev_state: Optional[Dict] = None, 
                   new_state: Optional[Dict] = None,
                   metadata: Optional[Dict] = None):
        """Enregistre une action critique dans les logs d'audit immuables."""
        
        conn = self.db.get_connection()
        try:
            conn.execute("""
                INSERT INTO audit_logs (
                    user_id, user_type, action, resource_type, resource_id,
                    previous_state, new_state, ip_address, user_agent
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, user_type, action, resource_type, resource_id,
                json.dumps(prev_state) if prev_state else None,
                json.dumps(new_state) if new_state else None,
                metadata.get('ip') if metadata else None,
                metadata.get('ua') if metadata else None
            ))
            conn.commit()
            logger.info(f"Audit log created: {action} by {user_type}:{user_id}")
        finally:
            conn.close()

    def get_audit_trail(self, limit: int = 50) -> list:
        """Récupère les derniers logs d'audit pour l'interface admin."""
        conn = self.db.get_connection()
        try:
            return conn.execute("""
                SELECT * FROM audit_logs 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,)).fetchall()
        finally:
            conn.close()

    def verify_sso_session(self, token: str) -> bool:
        """Vérifie la session SSO via Okta/Azure AD. À implémenter en production."""
        # TODO: Intégrer la vérification réelle du token SSO
        # Exemple :
        # from okta_jwt_verifier import JWTVerifier
        # verifier = JWTVerifier(...)
        # return verifier.verify_access_token(token)
        raise NotImplementedError("SSO verification not implemented. Security risk if left as True.")
