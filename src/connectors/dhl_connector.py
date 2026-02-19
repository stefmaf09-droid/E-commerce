"""
DHL API Connector.
Uses 'Shipment Tracking - Unified' API.
"""

import logging
import os
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class DHLConnector:
    """Connector for DHL Express API."""
    
    # Unified Tracking API URL
    BASE_URL = "https://api-eu.dhl.com/track/shipments"

    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        """
        Initialize DHL Connector.
        
        Args:
            api_key: DHL API Key.
            api_secret: DHL API Secret.
        """
        self.api_key = api_key or os.getenv('DHL_API_KEY')
        self.api_secret = api_secret or os.getenv('DHL_API_SECRET')
        
    def get_tracking(self, tracking_number: str) -> Optional[Dict[str, Any]]:
        """
        Get tracking information from DHL API.
        
        Args:
            tracking_number: DHL tracking number
            
        Returns:
            Dictionary with tracking data or None
        """
        if not self.api_key:
            logger.warning("No DHL API Key provided. Cannot fetch tracking.")
            return None
            
        headers = {
            'DHL-API-Key': self.api_key,
            'Accept': 'application/json'
        }
        
        params = {
            'trackingNumber': tracking_number,
            'service': 'express' # Optional, filters for express
        }
        
        try:
            logger.info(f"Fetching DHL tracking for {tracking_number}")
            response = requests.get(
                self.BASE_URL,
                headers=headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            return self._parse_response(data)
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return {'status': 'not_found', 'error': 'Tracking number not found'}
            elif e.response.status_code == 401:
                logger.error("DHL API Unauthorized - Check API Key")
            logger.error(f"DHL API HTTP Error: {e}")
            return None
        except Exception as e:
            logger.error(f"DHL Connector Error: {e}")
            return None
            
    def _parse_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse raw DHL API response into standardized format."""
        try:
            shipments = data.get('shipments', [])
            if not shipments:
                return None
                
            shipment = shipments[0]
            status_obj = shipment.get('status', {})
            
            # Standardize status
            status_code = status_obj.get('statusCode', '').lower()
            is_delivered = status_code == 'delivered'
            
            return {
                'carrier': 'DHL',
                'tracking_number': shipment.get('id'),
                'status': status_obj.get('status', 'Unknown'),
                'status_code': status_code,
                'is_delivered': is_delivered,
                'delivery_date': status_obj.get('timestamp'),
                'events': shipment.get('events', [])
            }
        except Exception as e:
            logger.error(f"Error parsing DHL response: {e}")
            return {'raw': data}
