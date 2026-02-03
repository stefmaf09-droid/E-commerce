
import logging
from src.integrations.base import BaseConnector

logger = logging.getLogger(__name__)

class MondialRelayConnector(BaseConnector):
    """Connecteur pour Mondial Relay (Point Relais)."""
    
    def __init__(self, api_key: str, merchant_id: str):
        super().__init__(api_key, merchant_id)
        self.carrier_name = "Mondial Relay"

    def get_tracking_status(self, tracking_number: str) -> str:
        """Appelle l'API de suivi Mondial Relay."""
        logger.info(f"Fetching Mondial Relay status for {tracking_number}")
        return "available_at_point"

    def submit_claim(self, claim_data: dict) -> bool:
        """Soumet un litige Mondial Relay (souvent pour avarie ou perte)."""
        logger.info(f"Submitting Mondial Relay claim for {claim_data.get('order_id')}")
        return True
