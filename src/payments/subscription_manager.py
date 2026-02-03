
import logging
from typing import Dict, Any, Optional
from src.database.database_manager import get_db_manager

logger = logging.getLogger(__name__)

class SubscriptionManager:
    """Moteur de gestion des abonnements et paliers de commission."""
    
    TIERS = {
        'standard': {'fee': 20.0, 'features': ['Dossiers illimités', 'Paiement Stripe Express']},
        'business': {'fee': 15.0, 'features': ['Commission réduite (15%)', 'Support prioritaire', 'Connecteur Gorgias']},
        'enterprise': {'fee': 10.0, 'features': ['Commission négociée (10%)', 'Accès API direct', 'Account Manager dédié']}
    }
    
    def __init__(self, db_manager=None):
        self.db = db_manager or get_db_manager()

    def update_tier(self, client_id: int, new_tier: str):
        """Change le palier d'abonnement d'un client."""
        if new_tier not in self.TIERS:
            raise ValueError(f"Tier {new_tier} inconnu.")
            
        fee = self.TIERS[new_tier]['fee']
        self.db.update_client(client_id, subscription_tier=new_tier, commission_rate=fee)
        logger.info(f"Client {client_id} upgraded to {new_tier} (Fee: {fee}%)")

    def get_billing_summary(self, client_id: int) -> Dict[str, Any]:
        """Retourne un résumé de la facturation actuelle du client."""
        conn = self.db.get_connection()
        client = conn.execute("SELECT subscription_tier, commission_rate FROM clients WHERE id = ?", (client_id,)).fetchone()
        conn.close()
        
        if not client:
            return {
                'tier': 'standard',
                'fee': 20.0,
                'perks': self.TIERS['standard']['features']
            }
            
        tier = client[0] if isinstance(client, tuple) else client['subscription_tier']
        fee = client[1] if isinstance(client, tuple) else client['commission_rate']
            
        return {
            'tier': tier,
            'fee': fee,
            'perks': self.TIERS.get(tier, self.TIERS['standard'])['features']
        }
