"""
UPS API Connector (OAuth 2.0).
Uses 'Authorization' and 'Tracking' APIs.
"""

import logging
import os
import requests
import base64
import time
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class UPSConnector:
    """Connector for UPS OAuth API."""
    
    BASE_URL = "https://onlinetools.ups.com" # Production
    # BASE_URL = "https://wwwcie.ups.com" # Staging/Test
    
    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None, account_number: Optional[str] = None):
        """
        Initialize UPS Connector.
        
        Args:
            client_id: UPS Client ID (OAuth).
            client_secret: UPS Client Secret.
            account_number: UPS Account Number (optional, sometimes needed for headers).
        """
        self.client_id = client_id or os.getenv('UPS_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('UPS_CLIENT_SECRET')
        self.account_number = account_number or os.getenv('UPS_ACCOUNT_NUMBER')
        
        self.access_token = None
        self.token_expiry = 0

    def _get_access_token(self) -> Optional[str]:
        """
        Get or refresh OAuth access token.
        """
        if self.access_token and time.time() < self.token_expiry:
            return self.access_token
            
        if not self.client_id or not self.client_secret:
            logger.error("UPS Client ID or Secret missing.")
            return None
            
        url = f"{self.BASE_URL}/security/v1/oauth/token"
        
        # Basic Auth for Token Endpoint
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "grant_type": "client_credentials"
        }
        
        try:
            response = requests.post(url, headers=headers, data=data, timeout=10)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get('access_token')
            # Set expiry (usually includes 'expires_in' seconds, default to 3600 if missing)
            expires_in = int(token_data.get('expires_in', 3600))
            self.token_expiry = time.time() + expires_in - 60 # Buffer 60s
            
            return self.access_token
            
        except Exception as e:
            logger.error(f"Failed to get UPS Access Token: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"UPS Response: {e.response.text}")
            return None

    def get_tracking(self, tracking_number: str) -> Optional[Dict[str, Any]]:
        """
        Get tracking information from UPS API.
        """
        token = self._get_access_token()
        if not token:
            return None
            
        url = f"{self.BASE_URL}/api/track/v1/details/{tracking_number}"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "transId": str(int(time.time())),
            "transactionSrc": "RecoursEcommerce"
        }
        
        params = {
            "locale": "fr_FR",
            "returnSignature": "false"
        }
        
        try:
            logger.info(f"Fetching UPS tracking for {tracking_number}")
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return self._parse_response(data, tracking_number)
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return {'status': 'not_found', 'error': 'Tracking number not found'}
            logger.error(f"UPS API Error: {e}")
            if e.response:
                logger.error(f"Response: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"UPS Connector Error: {e}")
            return None

    def _parse_response(self, data: Dict[str, Any], tracking_number: str) -> Dict[str, Any]:
        """Parse raw UPS API response."""
        try:
            track_response = data.get('trackResponse', {})
            shipment = track_response.get('shipment', [{}])[0]
            package = shipment.get('package', [{}])[0]
            activity = package.get('activity', [{}])[0]
            status_obj = activity.get('status', {})
            
            status_code = status_obj.get('code')
            status_desc = status_obj.get('description', 'Unknown')
            
            # UPS delivered code is usually 'D'
            is_delivered = status_obj.get('type') == 'D' or 'deliver' in status_desc.lower()
            
            date = activity.get('date', '')
            time_str = activity.get('time', '')
            delivery_date = f"{date} {time_str}".strip()
            
            return {
                'carrier': 'UPS',
                'tracking_number': tracking_number,
                'status': status_desc,
                'status_code': status_code,
                'is_delivered': is_delivered,
                'delivery_date': delivery_date,
                'events': package.get('activity', [])
            }
        except Exception as e:
            logger.error(f"Error parsing UPS response: {e}")
            return {'raw': data}
