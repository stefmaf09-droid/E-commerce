"""
UPS Tracking API Connector with OAuth 2.0

API Documentation: https://developer.ups.com/api/reference/tracking
Authentication: OAuth 2.0 Client Credentials
Response Format: REST JSON

Features:
- OAuth 2.0 token management with auto-refresh
- POD retrieval from tracking number
- Signature image URLs
- Delivery confirmation details
"""

import os
import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import requests

logger = logging.getLogger(__name__)


class UPSConnector:
    """UPS Tracking API connector with OAuth 2.0 authentication."""
    
    # Production endpoints
    AUTH_URL = "https://onlinetools.ups.com/security/v1/oauth/token"
    TRACK_URL = "https://onlinetools.ups.com/api/track/v1/details"
    
    # Test/Sandbox endpoints (uncomment for testing)
    # AUTH_URL = "https://wwwcie.ups.com/security/v1/oauth/token"
    # TRACK_URL = "https://wwwcie.ups.com/api/track/v1/details"
    
    def __init__(
        self,
        client_id: str = None,
        client_secret: str = None
    ):
        """
        Initialize UPS connector.
        
        Args:
            client_id: UPS OAuth client ID
            client_secret: UPS OAuth client secret
        """
        self.client_id = client_id or os.getenv('UPS_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('UPS_CLIENT_SECRET')
        
        self.access_token = None
        self.token_expires_at = None
        
        if not self.client_id or not self.client_secret:
            logger.warning("UPS credentials not configured - POD fetch will fail")
    
    def _get_access_token(self) -> Optional[str]:
        """
        Get or refresh OAuth 2.0 access token.
        
        Returns:
            Access token string or None if failed
        """
        # Check if existing token is still valid
        if self.access_token and self.token_expires_at:
            if datetime.now() < self.token_expires_at:
                logger.debug("Using cached UPS OAuth token")
                return self.access_token
        
        # Request new token
        logger.info("Requesting new UPS OAuth token")
        
        try:
            response = requests.post(
                self.AUTH_URL,
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                data={
                    'grant_type': 'client_credentials',
                    'client_id': self.client_id,
                    'client_secret': self.client_secret
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data['access_token']
                
                # Set expiration (subtract 60s for safety margin)
                expires_in = data.get('expires_in', 3600)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)
                
                logger.info(f"UPS OAuth token obtained (expires in {expires_in}s)")
                return self.access_token
            else:
                logger.error(f"UPS OAuth failed: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get UPS OAuth token: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting UPS token: {e}")
            return None
    
    def get_tracking_details(self, tracking_number: str) -> Dict[str, Any]:
        """
        Get detailed tracking information.
        
        Args:
            tracking_number: UPS tracking number (1Z format)
            
        Returns:
            Tracking data dictionary
        """
        if not self.client_id or not self.client_secret:
            return {
                'success': False,
                'error': 'UPS credentials not configured',
                'tracking_number': tracking_number
            }
        
        # Get access token
        token = self._get_access_token()
        if not token:
            return {
                'success': False,
                'error': 'Failed to obtain OAuth token',
                'tracking_number': tracking_number
            }
        
        try:
            # Prepare request
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'transId': str(uuid.uuid4()),
                'transactionSrc': 'Refundly'
            }
            
            # Make API call
            url = f"{self.TRACK_URL}/{tracking_number}"
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_tracking_data(data, tracking_number)
            else:
                logger.error(f"UPS API error {response.status_code}: {response.text}")
                return {
                    'success': False,
                    'error': f'API error: {response.status_code}',
                    'tracking_number': tracking_number
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"UPS API request failed for {tracking_number}: {e}")
            return {
                'success': False,
                'error': str(e),
                'tracking_number': tracking_number
            }
        except Exception as e:
            logger.error(f"Unexpected error tracking {tracking_number}: {e}")
            return {
                'success': False,
                'error': str(e),
                'tracking_number': tracking_number
            }
    
    def _parse_tracking_data(
        self,
        data: Dict,
        tracking_number: str
    ) -> Dict[str, Any]:
        """Parse UPS API response to structured data."""
        try:
            # Navigate response structure
            track_response = data.get('trackResponse', {})
            shipments = track_response.get('shipment', [])
            
            if not shipments:
                return {
                    'success': False,
                    'error': 'No shipment data found',
                    'tracking_number': tracking_number
                }
            
            shipment = shipments[0]
            packages = shipment.get('package', [])
            
            if not packages:
                return {
                    'success': False,
                    'error': 'No package data found',
                    'tracking_number': tracking_number
                }
            
            package = packages[0]
            
            # Get delivery information
            delivery_info = package.get('deliveryInformation', {})
            current_status = package.get('currentStatus', {})
            
            # Determine status
            status_code = current_status.get('code', '')
            status_description = current_status.get('description', 'Unknown')
            
            # Check if delivered
            is_delivered = delivery_info.get('receivedBy') is not None
            
            tracking_data = {
                'success': True,
                'tracking_number': tracking_number,
                'status': 'DELIVERED' if is_delivered else 'IN_TRANSIT',
                'status_code': status_code,
                'status_description': status_description
            }
            
            # Add delivery details if delivered
            if is_delivered:
                tracking_data.update({
                    'delivery_date': delivery_info.get('deliveryDate'),
                    'delivery_time': delivery_info.get('deliveryTime'),
                    'recipient_name': delivery_info.get('receivedBy'),
                    'delivery_location': delivery_info.get('location'),
                    'signature_url': delivery_info.get('signatureImage', {}).get('url')
                })
            
            # Add activity history
            activities = package.get('activity', [])
            tracking_data['events'] = []
            
            for activity in activities:
                tracking_data['events'].append({
                    'date': activity.get('date'),
                    'time': activity.get('time'),
                    'status': activity.get('status', {}).get('description', ''),
                    'location': activity.get('location', {}).get('address', {}).get('city', '')
                })
            
            return tracking_data
            
        except Exception as e:
            logger.error(f"Failed to parse UPS response: {e}")
            return {
                'success': False,
                'error': f'Parse error: {str(e)}',
                'tracking_number': tracking_number
            }
    
    def get_pod(self, tracking_number: str) -> Dict[str, Any]:
        """
        Fetch POD (Proof of Delivery) for a tracking number.
        
        Args:
            tracking_number: UPS tracking number
            
        Returns:
            {
                'success': bool,
                'pod_url': str or None,
                'pod_data': {...},
                'error': str or None,
                'source': 'ups'
            }
        """
        logger.info(f"Fetching UPS POD for {tracking_number}")
        
        # Get tracking details
        tracking = self.get_tracking_details(tracking_number)
        
        if not tracking.get('success'):
            return {
                'success': False,
                'pod_url': None,
                'pod_data': {},
                'error': tracking.get('error', 'Unknown error'),
                'source': 'ups'
            }
        
        # Check if delivered
        if tracking.get('status') != 'DELIVERED':
            return {
                'success': False,
                'pod_url': None,
                'pod_data': {},
                'error': f"Package not delivered yet (status: {tracking.get('status')})",
                'source': 'ups'
            }
        
        # Extract POD data
        pod_data = {
            'delivery_date': tracking.get('delivery_date'),
            'delivery_time': tracking.get('delivery_time'),
            'recipient_name': tracking.get('recipient_name', 'Recipient'),
            'delivery_location': tracking.get('delivery_location', 'Address'),
            'signature_url': tracking.get('signature_url'),
            'tracking_events': tracking.get('events', [])
        }
        
        # UPS POD URL (signature is often the POD proof)
        pod_url = tracking.get('signature_url') or f"https://www.ups.com/track?tracknum={tracking_number}"
        
        return {
            'success': True,
            'pod_url': pod_url,
            'pod_data': pod_data,
            'error': None,
            'source': 'ups'
        }


if __name__ == "__main__":
    # Test connector
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    print("="*70)
    print("UPS CONNECTOR - Test")
    print("="*70)
    
    # Test with credentials from environment
    connector = UPSConnector(
        client_id=os.getenv('UPS_CLIENT_ID', 'demo_client_id'),
        client_secret=os.getenv('UPS_CLIENT_SECRET', 'demo_secret')
    )
    
    # Test OAuth
    print("\n🔐 Testing OAuth token...")
    token = connector._get_access_token()
    
    if token:
        print(f"✅ OAuth token obtained: {token[:20]}...")
    else:
        print("❌ OAuth token failed (expected without real credentials)")
    
    # Test tracking number (use real one if available)
    test_tracking = "1Z999AA10123456784"
    
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
    print("✅ UPS Connector Ready")
    print("="*70)
