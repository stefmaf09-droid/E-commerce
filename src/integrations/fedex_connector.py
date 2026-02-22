"""
FedEx Track API v3 Connector

API Documentation: https://developer.fedex.com/api/en-us/catalog/track/v1/docs.html
Authentication: OAuth 2.0 Client Credentials
Response Format: JSON

Features:
- POD retrieval from tracking number
- Delivery status tracking
- Signature and recipient information
- OAuth 2.0 token management

Rate Limits:
- Production: 3000 requests/day
- Sandbox: Unlimited (testing)
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import requests
import json

logger = logging.getLogger(__name__)


class FedExConnector:
    """FedEx Track API v3 connector for POD retrieval."""
    
    # API Endpoints
    BASE_URL_PROD = "https://apis.fedex.com"
    BASE_URL_SANDBOX = "https://apis-sandbox.fedex.com"
    
    TOKEN_ENDPOINT = "/oauth/token"
    TRACK_ENDPOINT = "/track/v1/trackingnumbers"
    
    # Delivery status codes
    DELIVERED_STATUSES = ['DL', 'DELIVERED']
    
    def __init__(
        self,
        client_id: str = None,
        client_secret: str = None,
        use_sandbox: bool = False
    ):
        """
        Initialize FedEx connector.
        
        Args:
            client_id: FedEx API Client ID
            client_secret: FedEx API Client Secret
            use_sandbox: Use sandbox environment for testing
        """
        self.client_id = client_id or os.getenv('FEDEX_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('FEDEX_CLIENT_SECRET')
        self.use_sandbox = use_sandbox or os.getenv('FEDEX_USE_SANDBOX', 'false').lower() == 'true'
        
        self.base_url = self.BASE_URL_SANDBOX if self.use_sandbox else self.BASE_URL_PROD
        
        if not self.client_id or not self.client_secret:
            logger.warning("FedEx credentials not configured - POD fetch will fail")
        
        # OAuth token cache
        self._access_token = None
        self._token_expires_at = None
        
        self.carrier_name = "FedEx"  # For compatibility
    
    def _get_access_token(self) -> Optional[str]:
        """
        Get OAuth 2.0 access token (cached or new).
        
        Returns:
            Access token string or None if failed
        """
        # Return cached token if still valid
        if self._access_token and self._token_expires_at:
            if datetime.now() < self._token_expires_at:
                return self._access_token
        
        # Request new token
        if not self.client_id or not self.client_secret:
            logger.error("FedEx credentials missing")
            return None
        
        try:
            url = f"{self.base_url}{self.TOKEN_ENDPOINT}"
            
            payload = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            logger.info(f"Requesting FedEx OAuth token")
            response = requests.post(url, data=payload, headers=headers, timeout=10)
            
            response.raise_for_status()
            
            token_data = response.json()
            self._access_token = token_data.get('access_token')
            expires_in = token_data.get('expires_in', 3600)  # Default 1 hour
            
            # Cache token with 5-minute buffer
            self._token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)
            
            logger.info("✅ FedEx OAuth token obtained successfully")
            return self._access_token
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get FedEx OAuth token: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting FedEx token: {e}")
            return None
    
    def get_tracking_details(self, tracking_number: str) -> Dict[str, Any]:
        """
        Get detailed tracking information.
        Uses API if credentials are available, otherwise falls back to FedExScraper.
        """
        token = self._get_access_token()
        
        if not token:
            logger.info(f"FedEx credentials missing or invalid, falling back to scraper for {tracking_number}")
            from src.scrapers.fedex_scraper import FedExScraper
            scraper = FedExScraper()
            result = scraper.get_tracking(tracking_number)
            
            if result and result.get('status') != 'error':
                return {
                    'success': True,
                    'status': 'DELIVERED' if result.get('is_delivered') else 'IN_TRANSIT',
                    'status_description': result.get('status'),
                    'tracking_number': tracking_number,
                    'delivery_date': result.get('delivery_date'),
                    'events': result.get('history', []),
                    'raw_data': {'source': 'scraper'}
                }

            return {
                'success': False,
                'error': 'Failed to authenticate with FedEx API and scraper fallback failed',
                'tracking_number': tracking_number
            }
        
        try:
            url = f"{self.base_url}{self.TRACK_ENDPOINT}"
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}',
                'X-locale': 'en_US'
            }
            
            payload = {
                'includeDetailedScans': True,
                'trackingInfo': [
                    {
                        'trackingNumberInfo': {
                            'trackingNumber': tracking_number
                        }
                    }
                ]
            }
            
            logger.info(f"Fetching FedEx tracking for {tracking_number}")
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            
            response.raise_for_status()
            
            data = response.json()
            return self._parse_tracking_response(data, tracking_number)
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"FedEx API HTTP error for {tracking_number}: {e}")
            return {
                'success': False,
                'error': f'FedEx API error: {e.response.status_code}',
                'tracking_number': tracking_number
            }
        except Exception as e:
            logger.error(f"FedEx tracking failed for {tracking_number}: {e}")
            return {
                'success': False,
                'error': str(e),
                'tracking_number': tracking_number
            }
    
    def _parse_tracking_response(
        self,
        response_data: Dict,
        tracking_number: str
    ) -> Dict[str, Any]:
        """Parse FedEx API response to structured data."""
        try:
            # Navigate response structure
            output = response_data.get('output', {})
            complete_track_results = output.get('completeTrackResults', [])
            
            if not complete_track_results:
                return {
                    'success': False,
                    'error': 'No tracking results found',
                    'tracking_number': tracking_number,
                    'status': 'UNKNOWN'
                }
            
            # Get first result (single tracking number)
            track_result = complete_track_results[0]
            track_results = track_result.get('trackResults', [])
            
            if not track_results:
                return {
                    'success': False,
                    'error': 'No track results in response',
                    'tracking_number': tracking_number,
                    'status': 'UNKNOWN'
                }
            
            shipment = track_results[0]
            
            # Get latest status
            latest_status_detail = shipment.get('latestStatusDetail', {})
            status_code = latest_status_detail.get('code', '')
            status_description = latest_status_detail.get('description', '')
            
            # Determine delivery status
            is_delivered = status_code in self.DELIVERED_STATUSES
            status = 'DELIVERED' if is_delivered else 'IN_TRANSIT'
            
            tracking_data = {
                'success': True,
                'tracking_number': tracking_number,
                'status': status,
                'status_description': status_description,
                'events': []
            }
            
            # Extract delivery details if delivered
            if is_delivered:
                delivery_details = shipment.get('deliveryDetails', {})
                actual_delivery = delivery_details.get('actualDeliveryAddress', {})
                
                # Get delivery timestamp
                scan_events = shipment.get('scanEvents', [])
                delivery_event = None
                
                for event in scan_events:
                    if event.get('eventType') == 'DL' or 'DELIVERED' in event.get('eventDescription', '').upper():
                        delivery_event = event
                        break
                
                tracking_data.update({
                    'delivery_date': delivery_event.get('date') if delivery_event else None,
                    'delivery_time': delivery_event.get('derivedStatusCode') if delivery_event else None,
                    'recipient_name': delivery_details.get('receivedByName', 'N/A'),
                    'delivery_location': actual_delivery.get('city', 'N/A'),
                })
            
            # Add scan events
            scan_events = shipment.get('scanEvents', [])
            for event in scan_events:
                tracking_data['events'].append({
                    'type': event.get('eventType', ''),
                    'date': event.get('date', ''),
                    'description': event.get('eventDescription', ''),
                    'location': event.get('scanLocation', {}).get('city', '')
                })
            
            return tracking_data
            
        except Exception as e:
            logger.error(f"Failed to parse FedEx response: {e}")
            return {
                'success': False,
                'error': f'Parse error: {str(e)}',
                'tracking_number': tracking_number
            }
    
    def get_pod(self, tracking_number: str) -> Dict[str, Any]:
        """
        Fetch POD (Proof of Delivery) for a tracking number.
        
        Args:
            tracking_number: FedEx tracking number
            
        Returns:
            {
                'success': bool,
                'pod_url': str or None,
                'pod_data': {...},
                'error': str or None,
                'source': 'fedex'
            }
        """
        logger.info(f"Fetching FedEx POD for {tracking_number}")
        
        # Get tracking details
        tracking = self.get_tracking_details(tracking_number)
        
        if not tracking.get('success'):
            return {
                'success': False,
                'pod_url': None,
                'pod_data': {},
                'error': tracking.get('error', 'Unknown error'),
                'source': 'fedex'
            }
        
        # Check if delivered
        if tracking.get('status') != 'DELIVERED':
            return {
                'success': False,
                'pod_url': None,
                'pod_data': {},
                'error': f"Package not delivered yet (status: {tracking.get('status')})",
                'source': 'fedex'
            }
        
        # Extract POD data
        pod_data = {
            'delivery_date': tracking.get('delivery_date'),
            'delivery_time': tracking.get('delivery_time'),
            'recipient_name': tracking.get('recipient_name', 'Recipient'),
            'delivery_location': tracking.get('delivery_location', 'Delivery Address'),
            'tracking_events': tracking.get('events', [])
        }
        
        # FedEx POD URL (tracking page)
        pod_url = f"https://www.fedex.com/fedextrack/?trknbr={tracking_number}"
        
        return {
            'success': True,
            'pod_url': pod_url,
            'pod_data': pod_data,
            'error': None,
            'source': 'fedex'
        }
    
    # Legacy compatibility methods
    def get_tracking_status(self, tracking_number: str) -> str:
        """Legacy compatibility method."""
        tracking = self.get_tracking_details(tracking_number)
        return tracking.get('status', 'UNKNOWN').lower()
    
    def submit_claim(self, claim_data: dict) -> bool:
        """Legacy compatibility method (not implemented)."""
        logger.warning("FedEx claim submission not implemented")
        return False


if __name__ == "__main__":
    # Test connector
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    print("="*70)
    print("FEDEX CONNECTOR - Test")
    print("="*70)
    
    # Check credentials
    client_id = os.getenv('FEDEX_CLIENT_ID')
    client_secret = os.getenv('FEDEX_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("\n⚠️  Warning: FedEx credentials not found in environment")
        print("   Set FEDEX_CLIENT_ID and FEDEX_CLIENT_SECRET")
        print("   Using demo mode (will fail)\n")
    
    # Test with sandbox
    connector = FedExConnector(use_sandbox=True)
    
    # Test tracking number
    test_tracking = "123456789012"
    
    print(f"\n📦 Testing POD fetch for: {test_tracking}")
    result = connector.get_pod(test_tracking)
    
    print(f"\nResult:")
    print(f"  Success: {result['success']}")
    print(f"  POD URL: {result['pod_url']}")
    print(f"  Error: {result['error']}")
    print(f"  Source: {result['source']}")
    
    if result['success']:
        print(f"\nPOD Data:")
        for key, value in result['pod_data'].items():
            if key != 'tracking_events':
                print(f"  {key}: {value}")
    
    print("\n" + "="*70)
    print("✅ FedEx Connector Ready")
    print("="*70)
