import logging
import requests
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from src.integrations.carrier_base import CarrierConnector
from src.utils.retry_handler import RetryHandler
from src.config import Config

logger = logging.getLogger(__name__)

class DHLConnector(CarrierConnector):
    """Connecteur pour DHL Express / Global Mail."""
    
    def __init__(self, api_key: Optional[str] = None, merchant_id: Optional[str] = None):
        """
        DHL connector.

        Notes:
        - `merchant_id` is kept for backward compatibility with earlier code paths,
          but is not required for the Unified Tracking endpoint.
        - If parameters are omitted, values are loaded from `src.config.Config`.
        """
        resolved_api_key = api_key or Config.get("DHL_API_KEY") or Config.get("DHL_APIKEY")
        resolved_merchant_id = merchant_id or Config.get("DHL_MERCHANT_ID")
        super().__init__({'api_key': resolved_api_key, 'merchant_id': resolved_merchant_id})
        self.api_url = "https://api-eu.dhl.com/track/shipments"

    @RetryHandler.with_retry(max_retries=3, base_delay=2.0)
    def get_tracking_details(self, tracking_number: str) -> Dict[str, Any]:
        """
        Get detailed tracking information for a package using DHL API.
        """
        logger.info(f"Fetching DHL tracking details for {tracking_number}")
        
        api_key = (self.credentials or {}).get("api_key")
        if not api_key:
            # Keep a graceful dev-mode behavior if not configured
            return {
                "status": "UNKNOWN",
                "carrier": "DHL",
                "tracking_number": tracking_number,
                "delivery_date": None,
                "events": [],
                "raw_data": {"error": "DHL_API_KEY not configured"},
            }

        headers = {"DHL-API-Key": api_key, "Accept": "application/json"}
        params = {"trackingNumber": tracking_number, "service": "express"}

        resp = requests.get(self.api_url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json() or {}

        shipments = data.get("shipments", []) or []
        if not shipments:
            return {
                "status": "UNKNOWN",
                "carrier": "DHL",
                "tracking_number": tracking_number,
                "delivery_date": None,
                "events": [],
                "raw_data": data,
            }

        shipment = shipments[0]
        status_obj = shipment.get("status", {}) or {}
        status_code = (status_obj.get("statusCode") or "").upper()
        status = "DELIVERED" if status_code == "DELIVERED" else (status_code or "IN_TRANSIT")

        return {
            "status": status,
            "carrier": "DHL",
            "tracking_number": shipment.get("id") or tracking_number,
            "delivery_date": status_obj.get("timestamp"),
            "events": shipment.get("events", []) or [],
            "raw_data": data,
        }
        
    def get_proof_of_delivery(self, tracking_number: str) -> Optional[bytes]:
        """Retrieve POD if available (not implemented)."""
        logger.info(f"Fetching POD for {tracking_number}")
        return None

    # Compatibility helpers -------------------------------------------------
    def get_tracking(self, tracking_number: str) -> Dict[str, Any]:
        """
        Compatibility method used by some scripts/tests and the universal tracker.
        Returns a simplified dict similar to other connectors.
        """
        details = self.get_tracking_details(tracking_number)
        return {
            "carrier": details.get("carrier", "DHL"),
            "tracking_number": details.get("tracking_number", tracking_number),
            "status": details.get("status", "UNKNOWN"),
            "delivery_date": details.get("delivery_date"),
            "events": details.get("events", []),
            "raw_data": details.get("raw_data", {}),
        }

    def submit_claim(self, claim_data: dict) -> bool:
        """Soumet une réclamation internationale DHL."""
        logger.info(f"Submitting DHL international claim for order {claim_data.get('order_id')}")
        # Les réclamations DHL demandent souvent une preuve de valeur
        if not claim_data.get('invoice_url'):
            logger.warning("DHL claim missing invoice")
            # return False
        return True
