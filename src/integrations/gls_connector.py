"""
GLS Parcel API Connector

API Documentation: https://gls-group.eu/GROUP/en/it-services
Authentication: API Key
Response Format: JSON

Features:
- POD retrieval from tracking number
- Delivery status tracking
- Signature and recipient information

Rate Limits:
- 1000 requests/day (standard)
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import requests

logger = logging.getLogger(__name__)


class GLSConnector:
    """GLS Parcel API connector for POD retrieval."""
    
    # API Endpoints
    BASE_URL = "https://api.gls-group.eu/public/v1"
    TRACKING_ENDPOINT = "/tracking"
    POD_ENDPOINT = "/proof-of-delivery"
    
    # Delivery status codes
    DELIVERED_STATUSES = ['DELIVERED', 'DEL']
    
    def __init__(self, api_key: str = None, username: str = None):
        """
        Initialize GLS connector.
        
        Args:
            api_key: GLS API Key
            username: GLS account username (for some endpoints)
        """
        self.api_key = api_key or os.getenv('GLS_API_KEY')
        self.username = username or os.getenv('GLS_USERNAME')
        
        if not self.api_key:
            logger.warning("GLS API key not configured - POD fetch will fail")
        
        self.carrier_name = "GLS"
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        if self.api_key:
            headers['X-API-Key'] = self.api_key
        
        if self.username:
            headers['X-Username'] = self.username
        
        return headers
    
    def get_tracking_details(self, tracking_number: str) -> Dict[str, Any]:
        """
        Get detailed tracking information.
        Uses API if key is available, otherwise falls back to GLSScraper.
        """
        if not self.api_key:
            logger.info(f"GLS API key missing, falling back to scraper for {tracking_number}")
            from src.scrapers.gls_scraper import GLSScraper
            scraper = GLSScraper()
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
                'error': 'GLS API key missing and scraper fallback failed',
                'tracking_number': tracking_number
            }
        
        try:
            url = f"{self.BASE_URL}{self.TRACKING_ENDPOINT}/{tracking_number}"
            headers = self._get_headers()
            
            logger.info(f"Fetching GLS tracking for {tracking_number}")
            response = requests.get(url, headers=headers, timeout=15)
            
            response.raise_for_status()
            
            data = response.json()
            return self._parse_tracking_response(data, tracking_number)
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"GLS API HTTP error for {tracking_number}: {e}")
            
            # Handle common errors
            if e.response.status_code == 401:
                error_msg = 'Authentication failed - check API key'
            elif e.response.status_code == 404:
                error_msg = 'Tracking number not found'
            elif e.response.status_code == 429:
                error_msg = 'Rate limit exceeded - try again later'
            else:
                error_msg = f'GLS API error: {e.response.status_code}'
            
            return {
                'success': False,
                'error': error_msg,
                'tracking_number': tracking_number
            }
        except Exception as e:
            logger.error(f"GLS tracking failed for {tracking_number}: {e}")
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
        """Parse GLS API response to structured data."""
        try:
            # Navigate GLS response structure
            tracking_info = response_data.get('tuStatus', [])
            
            if not tracking_info:
                return {
                    'success': False,
                    'error': 'No tracking information found',
                    'tracking_number': tracking_number,
                    'status': 'UNKNOWN'
                }
            
            # Get latest status
            latest = tracking_info[0] if tracking_info else {}
            status_code = latest.get('statusCode', '')
            status_text = latest.get('statusText', '')
            
            # Determine delivery status
            is_delivered = status_code in self.DELIVERED_STATUSES
            status = 'DELIVERED' if is_delivered else 'IN_TRANSIT'
            
            tracking_data = {
                'success': True,
                'tracking_number': tracking_number,
                'status': status,
                'status_description': status_text,
                'events': []
            }
            
            # Extract delivery details if delivered
            if is_delivered:
                delivery_info = latest.get('deliveryInfo', {})
                
                tracking_data.update({
                    'delivery_date': latest.get('date'),
                    'delivery_time': latest.get('time'),
                    'recipient_name': delivery_info.get('recipient', 'N/A'),
                    'delivery_location': delivery_info.get('location', 'N/A'),
                })
            
            # Add all tracking events
            for event in tracking_info:
                tracking_data['events'].append({
                    'code': event.get('statusCode', ''),
                    'date': event.get('date', ''),
                    'time': event.get('time', ''),
                    'description': event.get('statusText', ''),
                    'location': event.get('location', '')
                })
            
            return tracking_data
            
        except Exception as e:
            logger.error(f"Failed to parse GLS response: {e}")
            return {
                'success': False,
                'error': f'Parse error: {str(e)}',
                'tracking_number': tracking_number
            }
    
    def get_pod(self, tracking_number: str) -> Dict[str, Any]:
        """
        Fetch POD (Proof of Delivery) for a tracking number.
        
        Args:
            tracking_number: GLS tracking/parcel number
            
        Returns:
            {
                'success': bool,
                'pod_url': str or None,
                'pod_data': {...},
                'error': str or None,
                'source': 'gls'
            }
        """
        logger.info(f"Fetching GLS POD for {tracking_number}")
        
        # Get tracking details first
        tracking = self.get_tracking_details(tracking_number)
        
        if not tracking.get('success'):
            return {
                'success': False,
                'pod_url': None,
                'pod_data': {},
                'error': tracking.get('error', 'Unknown error'),
                'source': 'gls'
            }
        
        # Check if delivered
        if tracking.get('status') != 'DELIVERED':
            return {
                'success': False,
                'pod_url': None,
                'pod_data': {},
                'error': f"Package not delivered yet (status: {tracking.get('status')})",
                'source': 'gls'
            }
        
        # Try to get POD document URL
        pod_url = None
        try:
            url = f"{self.BASE_URL}{self.POD_ENDPOINT}/{tracking_number}"
            headers = self._get_headers()
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                pod_data_response = response.json()
                pod_url = pod_data_response.get('podUrl') or pod_data_response.get('documentUrl')
        except Exception as e:
            logger.warning(f"Could not fetch POD document URL: {e}")
            # Fallback to tracking page
            pod_url = f"https://gls-group.eu/track/{tracking_number}"
        
        # Extract POD data
        pod_data = {
            'delivery_date': tracking.get('delivery_date'),
            'delivery_time': tracking.get('delivery_time'),
            'recipient_name': tracking.get('recipient_name', 'Recipient'),
            'delivery_location': tracking.get('delivery_location', 'Delivery Address'),
            'tracking_events': tracking.get('events', [])
        }
        
        # Fallback URL if no direct POD
        if not pod_url:
            pod_url = f"https://gls-group.eu/track/{tracking_number}"
        
        return {
            'success': True,
            'pod_url': pod_url,
            'pod_data': pod_data,
            'error': None,
            'source': 'gls'
        }
    
    # Legacy compatibility methods
    def get_tracking_status(self, tracking_number: str) -> str:
        """Legacy compatibility method."""
        tracking = self.get_tracking_details(tracking_number)
        return tracking.get('status', 'UNKNOWN').lower()
    
    def submit_claim(self, claim_data: dict) -> bool:
        """Legacy compatibility method (not implemented)."""
        logger.warning("GLS claim submission not implemented")
        return False


if __name__ == "__main__":
    # Test connector
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    print("="*70)
    print("GLS CONNECTOR - Test")
    print("="*70)
    
    # Check credentials
    api_key = os.getenv('GLS_API_KEY')
    
    if not api_key:
        print("\n⚠️  Warning: GLS API key not found in environment")
        print("   Set GLS_API_KEY")
        print("   Using demo mode (will fail)\n")
    
    connector = GLSConnector()
    
    # Test tracking number
    test_tracking = "1234567890"
    
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
    print("✅ GLS Connector Ready")
    print("="*70)
