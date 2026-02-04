
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
            with conn.cursor() as cur:
                # Use %s for psycopg2 compatibility (and usually fine for sqlite when handled by wrapper, 
                # but let's assume valid postgres setup now)
                cur.execute("""
                    INSERT INTO activity_logs (
                        client_id, action, resource_type, resource_id,
                        details, ip_address, user_agent
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    user_id, action, resource_type, resource_id,
                    json.dumps({"prev": prev_state, "new": new_state}),
                    metadata.get('ip') if metadata else None,
                    metadata.get('ua') if metadata else None
                ))
            conn.commit()
            logger.info(f"Audit log created: {action} by {user_type}:{user_id}")
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
            conn.rollback()
        finally:
            conn.close()

    def get_audit_trail(self, limit: int = 50) -> list:
        """Récupère les derniers logs d'audit pour l'interface admin."""
        conn = self.db.get_connection()
        try:
            # Table name check: schema says 'activity_logs', code said 'audit_logs'. 
            # Updated to 'activity_logs' to match schema.sql
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM activity_logs 
                    ORDER BY timestamp DESC 
                    LIMIT %s
                """, (limit,))
                # Convert rows to dicts if needed, or rely on row factory
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]
        except Exception as e:
             logger.error(f"Failed to fetch audit trail: {e}")
             return []
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
