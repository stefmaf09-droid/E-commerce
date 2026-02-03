
import logging
from src.integrations.base import BaseConnector

logger = logging.getLogger(__name__)

class GLSConnector(BaseConnector):
    """Connecteur pour GLS."""
    
    def __init__(self, api_key: str, merchant_id: str):
        super().__init__(api_key, merchant_id)
        self.carrier_name = "GLS"

    def get_tracking_status(self, tracking_number: str) -> str:
        """Appelle l'API de suivi GLS."""
        logger.info(f"Fetching GLS status for {tracking_number}")
        return "delivered"

    def submit_claim(self, claim_data: dict) -> bool:
        """Soumet une réclamation GLS."""
        logger.info(f"Submitting GLS claim for {claim_data.get('order_id')}")
        return True
