"""
Mondial Relay Web Services API Connector

API Documentation: https://www.mondialrelay.fr/media/511247/Documentation-WebService-MR.pdf
Authentication: Username + Password (Enseigne + Marque)
Response Format: SOAP/XML

Features:
- POD retrieval from tracking number
- Delivery status tracking
- Point Relais (pickup point) information

Rate Limits:
- No specific limit (use reasonable throttling)
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Check for SOAP library
try:
    import zeep
    from zeep import Client
    from zeep.exceptions import Fault
except ImportError:
    zeep = None
    Client = None
    Fault = Exception


class MondialRelayConnector:
    """Mondial Relay Web Services connector for POD retrieval."""
    
    # WSDL URL
    WSDL_URL = "https://www.mondialrelay.fr/webservice/Web_Services.asmx?WSDL"
    
    # Delivery status codes
    DELIVERED_CODES = ['LIV', '99']  # Livré, Livraison effectuée
    AVAILABLE_CODES = ['DIS', '24']  # Disponible au Point Relais
    
    def __init__(
        self,
        username: str = None,
        password: str = None,
        enseigne: str = None
    ):
        """
        Initialize Mondial Relay connector.
        
        Args:
            username: Mondial Relay Enseigne code
            password: Mondial Relay security key
            enseigne: Enseigne code (often same as username)
        """
        self.username = username or os.getenv('MONDIAL_RELAY_ENSEIGNE')
        self.password = password or os.getenv('MONDIAL_RELAY_PASSWORD')
        self.enseigne = enseigne or self.username
        
        if not zeep:
            logger.error("zeep library not installed. Run: pip install zeep")
            raise ImportError("zeep library required for Mondial Relay connector")
        
        if not self.username or not self.password:
            logger.warning("Mondial Relay credentials not configured - POD fetch will fail")
        
        self.client = None
        self.carrier_name = "Mondial Relay"
    
    def _get_client(self) -> Client:
        """Get or create SOAP client."""
        if self.client is None:
            try:
                self.client = zeep.Client(wsdl=self.WSDL_URL)
                logger.info("Mondial Relay SOAP client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Mondial Relay client: {e}")
                raise
        
        return self.client
    
    def get_tracking_details(self, tracking_number: str) -> Dict[str, Any]:
        """
        Get detailed tracking information.
        
        Args:
            tracking_number: Mondial Relay expedition number
            
        Returns:
            Tracking data dictionary
        """
        if not self.username or not self.password:
            return {
                'success': False,
                'error': 'Mondial Relay credentials not configured',
                'tracking_number': tracking_number
            }
        
        try:
            client = self._get_client()
            
            # Call SOAP service (WSI2_TracingColisDetaille)
            response = client.service.WSI2_TracingColisDetaille(
                Enseigne=self.enseigne,
                Expedition=tracking_number,
                Langue='FR',
                Security=self.password
            )
            
            return self._parse_tracking_response(response, tracking_number)
            
        except Fault as e:
            logger.error(f"Mondial Relay SOAP fault for {tracking_number}: {e}")
            return {
                'success': False,
                'error': f'SOAP error: {str(e)}',
                'tracking_number': tracking_number
            }
        except Exception as e:
            logger.error(f"Mondial Relay tracking failed for {tracking_number}: {e}")
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
            # Check response status
            stat = getattr(response, 'STAT', None)
            
            if stat != '0':
                error_msg = f"Mondial Relay error code: {stat}"
                return {
                    'success': False,
                    'error': error_msg,
                    'tracking_number': tracking_number,
                    'status': 'UNKNOWN'
                }
            
            # Get tracking events
            events_list = getattr(response, 'Tracing', [])
            
            if not events_list:
                return {
                    'success': False,
                    'error': 'No tracking events found',
                    'tracking_number': tracking_number,
                    'status': 'UNKNOWN'
                }
            
            # Find latest event
            latest_event = events_list[-1] if events_list else None
            latest_code = getattr(latest_event, 'Libelle', '') if latest_event else ''
            
            # Determine status
            if any(code in latest_code for code in self.DELIVERED_CODES):
                status = 'DELIVERED'
            elif any(code in latest_code for code in self.AVAILABLE_CODES):
                status = 'AVAILABLE_AT_POINT'
            else:
                status = 'IN_TRANSIT'
            
            tracking_data = {
                'success': True,
                'tracking_number': tracking_number,
                'status': status,
                'events': []
            }
            
            # Extract delivery/pickup info if delivered
            if status in ['DELIVERED', 'AVAILABLE_AT_POINT']:
                if latest_event:
                    tracking_data.update({
                        'delivery_date': getattr(latest_event, 'Date', None),
                        'delivery_time': getattr(latest_event, 'Heure', None),
                        'recipient_name': getattr(latest_event, 'Destinataire', 'N/A'),
                        'delivery_location': getattr(latest_event, 'NomPointRelais', 'Point Relais'),
                    })
            
            # Add all events
            for event in events_list:
                tracking_data['events'].append({
                    'code': getattr(event, 'Code_Evenement', ''),
                    'date': getattr(event, 'Date', ''),
                    'time': getattr(event, 'Heure', ''),
                    'description': getattr(event, 'Libelle', ''),
                    'location': getattr(event, 'NomPointRelais', '')
                })
            
            return tracking_data
            
        except Exception as e:
            logger.error(f"Failed to parse Mondial Relay response: {e}")
            return {
                'success': False,
                'error': f'Parse error: {str(e)}',
                'tracking_number': tracking_number
            }
    
    def get_pod(self, tracking_number: str) -> Dict[str, Any]:
        """
        Fetch POD (Proof of Delivery) for a tracking number.
        
        Args:
            tracking_number: Mondial Relay expedition number
            
        Returns:
            {
                'success': bool,
                'pod_url': str or None,
                'pod_data': {...},
                'error': str or None,
                'source': 'mondial_relay'
            }
        """
        logger.info(f"Fetching Mondial Relay POD for {tracking_number}")
        
        # Get tracking details
        tracking = self.get_tracking_details(tracking_number)
        
        if not tracking.get('success'):
            return {
                'success': False,
                'pod_url': None,
                'pod_data': {},
                'error': tracking.get('error', 'Unknown error'),
                'source': 'mondial_relay'
            }
        
        # Check if delivered or available
        status = tracking.get('status')
        if status not in ['DELIVERED', 'AVAILABLE_AT_POINT']:
            return {
                'success': False,
                'pod_url': None,
                'pod_data': {},
                'error': f"Package not delivered yet (status: {status})",
                'source': 'mondial_relay'
            }
        
        # Extract POD data
        pod_data = {
            'delivery_date': tracking.get('delivery_date'),
            'delivery_time': tracking.get('delivery_time'),
            'recipient_name': tracking.get('recipient_name', 'Client'),
            'delivery_location': tracking.get('delivery_location', 'Point Relais'),
            'tracking_events': tracking.get('events', [])
        }
        
        # Mondial Relay tracking URL
        pod_url = f"https://www.mondialrelay.fr/suivi-de-colis/?numeroExpedition={tracking_number}"
        
        return {
            'success': True,
            'pod_url': pod_url,
            'pod_data': pod_data,
            'error': None,
            'source': 'mondial_relay'
        }
    
    # Legacy compatibility methods
    def get_tracking_status(self, tracking_number: str) -> str:
        """Legacy compatibility method."""
        tracking = self.get_tracking_details(tracking_number)
        status = tracking.get('status', 'UNKNOWN')
        
        # Map to legacy format
        if status == 'AVAILABLE_AT_POINT':
            return 'available_at_point'
        else:
            return status.lower()
    
    def submit_claim(self, claim_data: dict) -> bool:
        """Legacy compatibility method (not implemented)."""
        logger.warning("Mondial Relay claim submission not implemented")
        return False


if __name__ == "__main__":
    # Test connector
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    print("="*70)
    print("MONDIAL RELAY CONNECTOR - Test")
    print("="*70)
    
    # Check if zeep is installed
    if not zeep:
        print("\n❌ Error: zeep library not installed")
        print("   Install with: pip install zeep")
        sys.exit(1)
    
    # Check credentials
    username = os.getenv('MONDIAL_RELAY_ENSEIGNE')
    password = os.getenv('MONDIAL_RELAY_PASSWORD')
    
    if not username or not password:
        print("\n⚠️  Warning: Mondial Relay credentials not found in environment")
        print("   Set MONDIAL_RELAY_ENSEIGNE and MONDIAL_RELAY_PASSWORD")
        print("   Using demo mode (will fail)\n")
    
    connector = MondialRelayConnector()
    
    # Test tracking number
    test_tracking = "12345678901"
    
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
    print("✅ Mondial Relay Connector Ready")
    print("="*70)
