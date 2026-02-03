
import logging
from typing import Dict, Any
from datetime import datetime
from src.database.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

class WebhookHandler:
    """
    Traite les payloads entrants des services de tracking (Webhooks).
    """
    
    def __init__(self, db_manager: DatabaseManager = None):
        self.db = db_manager or DatabaseManager()

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
            
            # 1. Rechercher la réclamation associée
            conn = self.db.get_connection()
            claim = conn.execute("SELECT id, status, payment_status FROM claims WHERE tracking_number = ?", 
                               (tracking_number,)).fetchone()
            conn.close()
            
            if not claim:
                logger.warning(f"No claim found for tracking {tracking_number}")
                return False
            
            claim_id = claim[0]
            
            # 2. Logique de mise à jour automatique
            if new_status == 'Delivered':
                # Si le colis est livré mais qu'un litige "Perte" était en cours
                # C'est une anomalie majeure (Potentiel Bypass ou erreur transporteur)
                conn = self.db.get_connection()
                current_claim = conn.execute("SELECT dispute_type FROM claims WHERE id = ?", (claim_id,)).fetchone()
                conn.close()
                
                if current_claim and current_claim[0] == 'lost':
                    logger.warning(f"Bypass possibility: Claim {claim_id} marked as 'lost' but now 'Delivered'")
                    self.db.update_claim(claim_id, automation_status='action_required', status='rejected')
                    
                    # Déclencher une alerte bypass
                    from src.automation.follow_up_manager import FollowUpManager
                    manager = FollowUpManager(self.db)
                    manager._create_bypass_alert({
                        'id': claim_id, 
                        'tracking_number': tracking_number, 
                        'claim_reference': f"AUTO-WH-DELIV-{claim_id}"
                    })
                else:
                    self.db.update_claim(claim_id, status='under_review', automation_status='automated')
            
            elif new_status == 'Lost':
                # Dossier validé par le transporteur en amont?
                self.db.update_claim(claim_id, automation_status='automated', status='under_review')
            
            # 3. Déclenchement de l'analyse Bypass si le statut est 'Compensated' (Spécifique certains providers)
            if new_status == 'Compensated' or new_status == 'Delivered':
                if claim[2] == 'unpaid':
                    from src.automation.follow_up_manager import FollowUpManager
                    manager = FollowUpManager(self.db)
                    manager._create_bypass_alert({'id': claim_id, 'tracking_number': tracking_number, 'claim_reference': 'AUTO-WH'})
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return False
