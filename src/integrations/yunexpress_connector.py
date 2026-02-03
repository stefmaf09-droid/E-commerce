
import logging
from src.integrations.base import BaseConnector

logger = logging.getLogger(__name__)

class YunExpressConnector(BaseConnector):
    """Connecteur pour YunExpress (Logistique Asie-Europe)."""
    
    def __init__(self, api_key: str, merchant_id: str):
        super().__init__(api_key, merchant_id)
        self.carrier_name = "YunExpress"

    def get_tracking_status(self, tracking_number: str) -> str:
        """Suivi spécifique pour les colis venant d'Asie."""
        logger.info(f"Tracking YunExpress: {tracking_number}")
        # Souvent YunExpress transmet à un transporteur local (Colissimo, GLS)
        return "in_transit_international"

    def submit_claim(self, claim_data: dict) -> bool:
        """
        Gère les litiges sur le trajet international.
        Note: Les conditions d'indemnisation sont souvent plus strictes.
        """
        logger.info(f"Submitting YunExpress claim for {claim_data.get('order_id')}")
        return True
