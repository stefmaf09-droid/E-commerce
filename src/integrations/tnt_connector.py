
import logging
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
from src.integrations.carrier_base import CarrierConnector
from src.utils.retry_handler import RetryHandler

logger = logging.getLogger(__name__)

class TNTConnector(CarrierConnector):
    """
    Connecteur pour TNT (FedEx Express) utilisant leur API publique.
    Remplace le TNTScraper legacy.
    """
    
    API_URL = "https://www.tnt.com/api/v3/shipment"
    PAGE_URL = "https://www.tnt.com/express/fr_fr/site/shipping-tools/tracking.html"

    def __init__(self, credentials: Optional[Dict[str, Any]] = None):
        super().__init__(credentials or {})
        self.carrier_name = "TNT"

    @RetryHandler.with_retry(max_retries=3, base_delay=2.0)
    def get_tracking_details(self, tracking_number: str) -> Dict[str, Any]:
        """Récupère les détails de suivi via l'API TNT."""
        logger.info(f"Fetching TNT tracking for {tracking_number}")
        
        params = {
            'con': tracking_number,
            'searchType': 'CON',
            'locale': 'fr_FR',
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Referer': self.PAGE_URL,
        }

        try:
            resp = requests.get(self.API_URL, params=params, headers=headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            
            return self._parse_api_response(data, tracking_number)
        except Exception as e:
            logger.error(f"TNT API Error for {tracking_number}: {e}")
            return {
                "success": False,
                "error": str(e),
                "status": "UNKNOWN",
                "tracking_number": tracking_number
            }

    def get_proof_of_delivery(self, tracking_number: str) -> Optional[bytes]:
        """Télécharge la preuve de livraison (POD) TNT."""
        logger.info(f"Downloading TNT POD for {tracking_number}")
        
        tracking = self.get_tracking_details(tracking_number)
        pod_url = tracking.get('raw_data', {}).get('pod_url')
        
        if not pod_url:
            logger.warning(f"No POD URL found for TNT {tracking_number}")
            return None
            
        try:
            # TNT POD URLs might be relative or require authentication
            if pod_url.startswith('/'):
                pod_url = "https://www.tnt.com" + pod_url
                
            resp = requests.get(pod_url, timeout=20)
            resp.raise_for_status()
            return resp.content
        except Exception as e:
            logger.error(f"Failed to download TNT POD: {e}")
            return None

    def _parse_api_response(self, data: Dict, tracking_number: str) -> Dict[str, Any]:
        """Parse TNT API response."""
        try:
            shipments = data.get('shipmentList', [])
            if not shipments and 'summary' in data:
                shipments = [data]
                
            if not shipments:
                return {"success": False, "error": "No data", "tracking_number": tracking_number}

            s = shipments[0]
            summary = s.get('summary', {})
            status_text = summary.get('statusDescription', s.get('status', 'Unknown'))

            is_delivered = any(
                kw in (status_text or '').lower()
                for kw in ['delivered', 'livré', 'remis', 'distribué']
            )

            history = []
            for event in s.get('scanHistory', []):
                history.append({
                    'timestamp': event.get('date', '') + ' ' + event.get('time', ''),
                    'description': event.get('statusDescription', ''),
                    'location': event.get('location', {}).get('depotCity', '') if isinstance(event.get('location'), dict) else ''
                })

            return {
                "success": True,
                "status": "DELIVERED" if is_delivered else "IN_TRANSIT",
                "status_description": status_text,
                "carrier": "TNT",
                "tracking_number": tracking_number,
                "delivery_date": summary.get('deliveryDate'),
                "events": history,
                "raw_data": {
                    "pod_url": s.get('podUrl'),
                    "api_full": data
                }
            }
        except Exception as e:
            logger.warning(f"TNT Parse Error: {e}")
            return {"success": False, "error": f"Parse error: {e}", "tracking_number": tracking_number}
