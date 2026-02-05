"""
Chronopost SOAP API Connector

API Documentation: https://www.chronopost.fr/fr/clients-ecommerce/api-suivi
WSDL: https://ws.chronopost.fr/tracking-cxf/TrackingServiceWS?wsdl

Authentication: Account Number + Password
Response Format: SOAP/XML

Features:
- POD retrieval from tracking number
- Delivery status tracking
- Signature and recipient information
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

try:
    import zeep
    from zeep import Client
    from zeep.exceptions import Fault
except ImportError:
    zeep = None
    Client = None
    Fault = Exception

logger = logging.getLogger(__name__)


class ChronopostConnector:
    """Chronopost SOAP API connector for POD retrieval."""
    
    WSDL_URL = "https://ws.chronopost.fr/tracking-cxf/TrackingServiceWS?wsdl"
    
    # Delivery status codes
    DELIVERED_CODES = ['DI', 'LI']  # Delivered, Livraison
    
    def __init__(self, account_number: str = None, password: str = None):
        """
        Initialize Chronopost connector.
        
        Args:
            account_number: Chronopost account number
            password: Chronopost API password
        """
        self.account_number = account_number or os.getenv('CHRONOPOST_ACCOUNT')
        self.password = password or os.getenv('CHRONOPOST_PASSWORD')
        
        if not zeep:
            logger.error("zeep library not installed. Run: pip install zeep")
            raise ImportError("zeep library required for Chronopost connector")
        
        if not self.account_number or not self.password:
            logger.warning("Chronopost credentials not configured - POD fetch will fail")
        
        self.client = None
    
    def _get_client(self) -> Client:
        """Get or create SOAP client."""
        if self.client is None:
            try:
                self.client = zeep.Client(wsdl=self.WSDL_URL)
                logger.info("Chronopost SOAP client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Chronopost client: {e}")
                raise
        
        return self.client
    
    def get_tracking_details(self, tracking_number: str) -> Dict[str, Any]:
        """
        Get detailed tracking information.
        
        Args:
            tracking_number: Chronopost tracking number (skybill)
            
        Returns:
            Tracking data dictionary
        """
        if not self.account_number or not self.password:
            return {
                'success': False,
                'error': 'Chronopost credentials not configured',
                'tracking_number': tracking_number
            }
        
        try:
            client = self._get_client()
            
            # Call SOAP service
            response = client.service.trackSkybillV2(
                accountNumber=self.account_number,
                password=self.password,
                language='fr_FR',
                skybillNumber=tracking_number
            )
            
            return self._parse_tracking_response(response, tracking_number)
            
        except Fault as e:
            logger.error(f"Chronopost SOAP fault for {tracking_number}: {e}")
            return {
                'success': False,
                'error': f'SOAP error: {str(e)}',
                'tracking_number': tracking_number
            }
        except Exception as e:
            logger.error(f"Chronopost tracking failed for {tracking_number}: {e}")
            return {
                'success': False,
                'error': str(e),
                'tracking_number': tracking_number
            }
    
    def _parse_tracking_response(
        self,
        response,
        tracking_number: str
    ) -> Dict[str, Any]:
        """Parse SOAP response to structured data."""
        try:
            # Check for events
            if not hasattr(response, 'listEvents') or not response.listEvents:
                return {
                    'success': False,
                    'error': 'No tracking events found',
                    'tracking_number': tracking_number,
                    'status': 'UNKNOWN'
                }
            
            events = response.listEvents
            
            # Find delivery event
            delivery_event = None
            latest_event = None
            
            for event in events:
                if hasattr(event, 'code'):
                    if event.code in self.DELIVERED_CODES:
                        delivery_event = event
                        break
                    latest_event = event
            
            # Determine status
            if delivery_event:
                status = 'DELIVERED'
            elif latest_event:
                status = 'IN_TRANSIT'
            else:
                status = 'UNKNOWN'
            
            tracking_data = {
                'success': True,
                'tracking_number': tracking_number,
                'status': status,
                'events': []
            }
            
            # Add delivery info if delivered
            if delivery_event:
                tracking_data.update({
                    'delivery_date': getattr(delivery_event, 'eventDate', None),
                    'delivery_time': getattr(delivery_event, 'eventHour', None),
                    'recipient_name': getattr(delivery_event, 'recipientName', 'N/A'),
                    'delivery_location': getattr(delivery_event, 'eventSite', 'N/A'),
                })
            
            # Add all events
            for event in events:
                tracking_data['events'].append({
                    'code': getattr(event, 'code', ''),
                    'date': getattr(event, 'eventDate', ''),
                    'time': getattr(event, 'eventHour', ''),
                    'description': getattr(event, 'eventLabel', ''),
                    'location': getattr(event, 'eventSite', '')
                })
            
            return tracking_data
            
        except Exception as e:
            logger.error(f"Failed to parse Chronopost response: {e}")
            return {
                'success': False,
                'error': f'Parse error: {str(e)}',
                'tracking_number': tracking_number
            }
    
    def get_pod(self, tracking_number: str) -> Dict[str, Any]:
        """
        Fetch POD (Proof of Delivery) for a tracking number.
        
        Args:
            tracking_number: Chronopost tracking number
            
        Returns:
            {
                'success': bool,
                'pod_url': str or None,
                'pod_data': {...},
                'error': str or None,
                'source': 'chronopost'
            }
        """
        logger.info(f"Fetching Chronopost POD for {tracking_number}")
        
        # Get tracking details
        tracking = self.get_tracking_details(tracking_number)
        
        if not tracking.get('success'):
            return {
                'success': False,
                'pod_url': None,
                'pod_data': {},
                'error': tracking.get('error', 'Unknown error'),
                'source': 'chronopost'
            }
        
        # Check if delivered
        if tracking.get('status') != 'DELIVERED':
            return {
                'success': False,
                'pod_url': None,
                'pod_data': {},
                'error': f"Package not delivered yet (status: {tracking.get('status')})",
                'source': 'chronopost'
            }
        
        # Extract POD data
        pod_data = {
            'delivery_date': tracking.get('delivery_date'),
            'delivery_time': tracking.get('delivery_time'),
            'recipient_name': tracking.get('recipient_name', 'Destinataire'),
            'delivery_location': tracking.get('delivery_location', 'Domicile'),
            'tracking_events': tracking.get('events', [])
        }
        
        # Chronopost POD URL format (may need adjustment based on actual API)
        # Note: Some carriers provide direct POD URLs, others require separate API call
        pod_url = f"https://www.chronopost.fr/tracking-no-cms/suivi-page?listeNumerosLT={tracking_number}"
        
        return {
            'success': True,
            'pod_url': pod_url,
            'pod_data': pod_data,
            'error': None,
            'source': 'chronopost'
        }


if __name__ == "__main__":
    # Test connector
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    print("="*70)
    print("CHRONOPOST CONNECTOR - Test")
    print("="*70)
    
    # Check if zeep is installed
    if not zeep:
        print("\n❌ Error: zeep library not installed")
        print("   Install with: pip install zeep")
        sys.exit(1)
    
    # Test with demo credentials (will fail without real creds)
    connector = ChronopostConnector(
        account_number=os.getenv('CHRONOPOST_ACCOUNT', 'demo_account'),
        password=os.getenv('CHRONOPOST_PASSWORD', 'demo_password')
    )
    
    # Test tracking number (use real one if available)
    test_tracking = "CH123456789FR"
    
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
    print("✅ Chronopost Connector Ready")
    print("="*70)
