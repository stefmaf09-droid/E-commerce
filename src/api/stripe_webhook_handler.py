
import logging
import stripe
from typing import Dict, Any
from src.database.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

class StripeWebhookHandler:
    """Traite les événements Stripe Connect."""
    
    def __init__(self, db_manager: DatabaseManager = None):
        self.db = db_manager or DatabaseManager()

    def handle_event(self, payload: str, sig_header: str, webhook_secret: str) -> bool:
        """
        Vérifie et oriente l'événement Stripe.
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        except ValueError as e:
            # Invalid payload
            logger.error(f"Invalid payload: {e}")
            return False
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            logger.error(f"Invalid signature: {e}")
            return False

        # Handle the event
        if event['type'] == 'account.updated':
            return self._handle_account_updated(event['data']['object'])
        elif event['type'] == 'transfer.created':
            return self._handle_transfer_created(event['data']['object'])
        elif event['type'] == 'payout.failed':
            return self._handle_payout_failed(event['data']['object'])
        else:
            logger.info(f"Unhandled event type {event['type']}")
            return True

    def _handle_account_updated(self, account: Dict[str, Any]) -> bool:
        """Met à jour le statut d'onboarding du client."""
        account_id = account['id']
        details_submitted = account.get('details_submitted', False)
        charges_enabled = account.get('charges_enabled', False)
        payouts_enabled = account.get('payouts_enabled', False)
        
        status = 'pending'
        if details_submitted and charges_enabled and payouts_enabled:
            status = 'active'
        elif details_submitted:
            status = 'restricted' # Needs more info or verification
            
        try:
            # Rechercher le client par stripe_connect_id
            conn = self.db.get_connection()
            client = conn.execute("SELECT id FROM clients WHERE stripe_connect_id = ?", (account_id,)).fetchone()
            conn.close()
            
            if client:
                self.db.update_client(
                    client[0], 
                    stripe_onboarding_status=status,
                    stripe_onboarding_completed=1 if status == 'active' else 0
                )
                logger.info(f"Stripe account {account_id} updated to status: {status}")
                return True
            else:
                logger.warning(f"Client with Stripe account {account_id} not found")
                return False
        except Exception as e:
            logger.error(f"Error updating client from webhook: {e}")
            return False

    def _handle_transfer_created(self, transfer: Dict[str, Any]) -> bool:
        """Log le succès d'un virement vers le marchand."""
        transfer_id = transfer['id']
        amount = transfer['amount'] / 100
        destination = transfer['destination']
        
        logger.info(f"Transfer {transfer_id} of {amount} created for account {destination}")
        
        # Trouver le paiement associé dans notre BDD
        try:
            conn = self.db.get_connection()
            payment = conn.execute("SELECT id, claim_id FROM payments WHERE stripe_transfer_id = ?", (transfer_id,)).fetchone()
            conn.close()
            
            if payment:
                self.db.update_payment(payment[0], payment_status='completed', paid_at='CURRENT_TIMESTAMP')
                # Mettre aussi à jour la réclamation
                self.db.update_claim(payment[1], payment_status='paid')
                return True
            return False
        except Exception as e:
            logger.error(f"Error handling transfer webhook: {e}")
            return False

    def _handle_payout_failed(self, payout: Dict[str, Any]) -> bool:
        """Alerte en cas d'échec de virement Stripe."""
        logger.error(f"Payout failed for account {payout.get('destination')}: {payout.get('failure_code')}")
        # Logique d'alerte système ici
        return True
