
import hmac
import hashlib
import logging
from typing import Dict, Any
from datetime import datetime
from src.database.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

class WebhookHandler:
    """
    Traite les payloads entrants des services de tracking (Webhooks).
    Supporte: AfterShip, Shopify (format générique)
    """

    def __init__(self, db_manager: DatabaseManager = None):
        self.db = db_manager or DatabaseManager()
        self._ensure_table_exists()

    def _ensure_table_exists(self):
        """Crée la table webhook_events si elle n'existe pas encore."""
        try:
            conn = self.db.get_connection()
            conn.execute("""
                CREATE TABLE IF NOT EXISTS webhook_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tracking_number TEXT NOT NULL,
                    event_tag TEXT NOT NULL,
                    payload_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Could not ensure webhook_events table: {e}")

    def verify_signature(self, raw_body: bytes, secret: str, received_hmac: str) -> bool:
        """
        Valide la signature HMAC-SHA256 d'un webhook entrant.
        Compatible Shopify (X-Shopify-Hmac-Sha256) et AfterShip.

        Args:
            raw_body:      Corps brut de la requête HTTP (bytes)
            secret:        Secret partagé configuré dans le service
            received_hmac: Valeur reçue dans le header (base64 ou hex)

        Returns:
            True si la signature est valide
        """
        import base64
        expected_bytes = hmac.new(
            secret.encode('utf-8'),
            raw_body,
            hashlib.sha256
        ).digest()
        # Détecter hex en premier (SHA-256 hex = 64 chars hexadécimaux)
        # base64.b64decode peut accepter faussement un hexdigest, donc on teste hex avant
        received_bytes = None
        if len(received_hmac) == 64 and all(c in '0123456789abcdefABCDEF' for c in received_hmac):
            try:
                received_bytes = bytes.fromhex(received_hmac)
            except Exception:
                pass
        if received_bytes is None:
            try:
                received_bytes = base64.b64decode(received_hmac)
            except Exception:
                return False
        return hmac.compare_digest(expected_bytes, received_bytes)

    def handle_tracking_update(self, payload: Dict[str, Any]) -> bool:
        """
        Traite un événement de changement de statut de colis.
        Exemple AfterShip payload: {"msg": {"slug": "ups", "tracking_number": "...", "tag": "Delivered"}}
        """
        try:
            msg = payload.get('msg', {})
            tracking_number = msg.get('tracking_number')
            new_status = msg.get('tag') # Delivered, OutForDelivery, Lost, etc.
            
            if not tracking_number or not new_status:
                logger.error("Missing data in webhook payload")
                return False
            
            logger.info(f"Webhook received: {tracking_number} -> {new_status}")
            
            # Idempotency Check
            conn = self.db.get_connection()
            existing = conn.execute(
                "SELECT 1 FROM webhook_events WHERE tracking_number = ? AND event_tag = ?",
                (tracking_number, new_status)
            ).fetchone()
            if existing:
                logger.info(f"Webhook event already processed: {tracking_number} / {new_status}")
                conn.close()
                return True
            
            # 1. Rechercher la réclamation associée
            claim = conn.execute("SELECT id, status, payment_status, dispute_type FROM claims WHERE tracking_number = ?", 
                               (tracking_number,)).fetchone()
            
            if not claim:
                logger.warning(f"No claim found for tracking {tracking_number}")
                conn.close()
                return False
            
            claim_id, current_status, payment_status, dispute_type = claim
            
            # 2. Logique de mise à jour automatique basée sur le statut
            automation_status = 'automated'
            status_to_update = None
            
            if new_status == 'Delivered':
                if dispute_type == 'lost':
                    logger.warning(f"Bypass possibility: Claim {claim_id} marked as 'lost' but now 'Delivered'")
                    status_to_update = 'rejected'
                    automation_status = 'action_required'
                    # Déclencher une alerte bypass
                    self._trigger_bypass_alert(claim_id, tracking_number)
                else:
                    status_to_update = 'under_review'
            
            elif new_status == 'Lost':
                status_to_update = 'under_review'
                
            elif new_status == 'InTransit':
                status_to_update = 'submitted'
                
            elif new_status == 'OutForDelivery':
                status_to_update = 'under_review'
                
            elif new_status == 'Exception':
                status_to_update = 'under_review'
                automation_status = 'action_required'
                logger.error(f"Carrier exception detected for {tracking_number}")

            # Appliquer la mise à jour si nécessaire
            if status_to_update:
                self.db.update_claim(claim_id, status=status_to_update, automation_status=automation_status)

            # 3. Déclenchement de l'analyse Bypass si le statut est 'Compensated' 
            if (new_status == 'Compensated' or new_status == 'Delivered') and payment_status == 'unpaid':
                self._trigger_bypass_alert(claim_id, tracking_number)
            
            # Enregistrer l'événement (Idempotence)
            import json
            conn.execute(
                "INSERT INTO webhook_events (tracking_number, event_tag, payload_json) VALUES (?, ?, ?)",
                (tracking_number, new_status, json.dumps(payload))
            )
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return False

    def _trigger_bypass_alert(self, claim_id: int, tracking_number: str):
        """Helper pour créer une alerte bypass."""
        try:
            from src.automation.follow_up_manager import FollowUpManager
            manager = FollowUpManager(self.db)
            manager._create_bypass_alert({
                'id': claim_id, 
                'tracking_number': tracking_number, 
                'claim_reference': f"AUTO-WH-ALERT-{claim_id}"
            })
        except Exception as e:
            logger.error(f"Failed to trigger bypass alert: {e}")
