
from typing import Dict, Type
from src.integrations.carrier_base import CarrierConnector
from src.integrations.dhl_connector import DHLConnector
from src.integrations.colissimo_connector import ColissimoConnector

class CarrierFactory:
    """Factory to get the appropriate carrier connector."""
    
    @staticmethod
    def get_connector(carrier_name: str, config: Dict[str, str] = {}) -> CarrierConnector:
        """
        Get a connector instance for the specified carrier.
        
        Args:
            carrier_name: Name of the carrier (e.g., 'DHL', 'Colissimo')
            config: Configuration dictionary with API keys, etc.
            
        Returns:
            Instance of CarrierConnector
        """
        name = carrier_name.lower()
        
        if 'dhl' in name:
            return DHLConnector(
                api_key=config.get('DHL_API_KEY', 'mock-key'),
                merchant_id=config.get('DHL_MERCHANT_ID', 'mock-id')
            )
        elif 'colissimo' in name or 'laposte' in name:
            return ColissimoConnector(
                api_key=config.get('COLISSIMO_API_KEY', 'mock-key')
            )
        else:
            raise ValueError(f"Unsupported carrier: {carrier_name}")
