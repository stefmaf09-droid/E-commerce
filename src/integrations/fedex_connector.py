
import logging
from src.integrations.base import BaseConnector

logger = logging.getLogger(__name__)

class FedExConnector(BaseConnector):
    """Connecteur pour FedEx / TNT."""
    
    def __init__(self, api_key: str, merchant_id: str):
        super().__init__(api_key, merchant_id)
        self.carrier_name = "FedEx"

    def get_tracking_status(self, tracking_number: str) -> str:
        """Simule l'interrogation de l'API FedEx."""
        logger.info(f"Fetching FedEx status for {tracking_number}")
        return "delivered"

    def submit_claim(self, claim_data: dict) -> bool:
        """Soumet une réclamation FedEx."""
        logger.info(f"Submitting FedEx claim for order {claim_data.get('order_id')}")
        return True
