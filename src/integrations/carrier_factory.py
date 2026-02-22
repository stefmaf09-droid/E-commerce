
from typing import Dict, Type, Any
from src.integrations.carrier_base import CarrierConnector
from src.integrations.dhl_connector import DHLConnector
from src.integrations.colissimo_connector import ColissimoConnector
from src.integrations.ups_connector import UPSConnector
from src.integrations.fedex_connector import FedExConnector
from src.integrations.gls_connector import GLSConnector
from src.integrations.mondial_relay_connector import MondialRelayConnector

class CarrierFactory:
    """Factory to get the appropriate carrier connector."""
    
    @staticmethod
    def get_connector(carrier_name: str, config: Dict[str, str] = {}) -> Any:
        """
        Get a connector instance for the specified carrier.
        
        Args:
            carrier_name: Name of the carrier (e.g., 'DHL', 'Colissimo', 'UPS')
            config: Configuration dictionary with API keys, etc.
            
        Returns:
            Connector instance
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
        elif 'ups' in name:
            return UPSConnector(
                client_id=config.get('UPS_CLIENT_ID'),
                client_secret=config.get('UPS_CLIENT_SECRET')
            )
        elif 'fedex' in name:
            return FedExConnector(
                client_id=config.get('FEDEX_CLIENT_ID'),
                client_secret=config.get('FEDEX_CLIENT_SECRET'),
                use_sandbox=config.get('FEDEX_USE_SANDBOX', 'false').lower() == 'true'
            )
        elif 'gls' in name:
            return GLSConnector(
                api_key=config.get('GLS_API_KEY')
            )
        elif 'mondial' in name:
            return MondialRelayConnector(
                username=config.get('MONDIAL_RELAY_ENSEIGNE'),
                password=config.get('MONDIAL_RELAY_PASSWORD')
            )
        else:
            # Fallback to Colissimo if unknown (logic based on tracking number might be needed)
            return ColissimoConnector(
                api_key=config.get('COLISSIMO_API_KEY', 'mock-key')
            )
