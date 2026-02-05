"""
POD Auto-Fetcher - Automatic Proof of Delivery Retrieval

Automatically fetches POD documents from carrier APIs with fallback to manual upload.

Features:
- Automatic POD retrieval from carrier APIs
- Retry logic with exponential backoff
- Caching to avoid duplicate requests
- Graceful fallback to manual upload
- Support for multiple carriers

Usage:
    from src.integrations.pod_fetcher import PODFetcher
    
    fetcher = PODFetcher()
    result = fetcher.fetch_pod('FR123456789', 'colissimo')
    
    if result['success']:
        print(f"POD URL: {result['pod_url']}")
    else:
        print(f"Manual upload needed: {result['error']}")
"""

import os
import sys
import logging
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import requests
import json
from pathlib import Path

# Add project root to path
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

logger = logging.getLogger(__name__)


class PODFetcher:
    """Main POD retrieval orchestrator with multi-carrier support."""
    
    # Cache directory for POD files
    CACHE_DIR = Path('data/pod_cache')
    CACHE_DURATION_DAYS = 30
    
    def __init__(self, cache_enabled: bool = True):
        """
        Initialize POD Fetcher.
        
        Args:
            cache_enabled: Whether to cache fetched PODs locally
        """
        self.cache_enabled = cache_enabled
        
        if cache_enabled:
            self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        
        # Initialize connectors on demand
        self._connectors = {}
        
        logger.info("PODFetcher initialized")
    
    def fetch_pod(
        self,
        tracking_number: str,
        carrier: str,
        retry_count: int = 3
    ) -> Dict[str, Any]:
        """
        Fetch POD from carrier API.
        
        Args:
            tracking_number: Tracking/shipment number
            carrier: Carrier name (colissimo, chronopost, ups, dhl, fedex)
            retry_count: Number of retry attempts
            
        Returns:
            {
                'success': bool,
                'pod_url': str or None,
                'pod_data': dict with delivery details,
                'error': str or None,
                'source': 'api' or 'cache'
            }
        """
        logger.info(f"Fetching POD for {tracking_number} ({carrier})")
        
        # Check cache first
        if self.cache_enabled:
            cached = self._get_from_cache(tracking_number, carrier)
            if cached:
                logger.info(f"POD found in cache for {tracking_number}")
                return {
                    'success': True,
                    'pod_url': cached['pod_url'],
                    'pod_data': cached['pod_data'],
                    'error': None,
                    'source': 'cache'
                }
        
        # Try API fetch with retry
        for attempt in range(retry_count):
            try:
                connector = self._get_connector(carrier)
                
                if not connector:
                    return {
                        'success': False,
                        'pod_url': None,
                        'pod_data': {},
                        'error': f'Carrier {carrier} not supported yet',
                        'source': None
                    }
                
                result = connector.get_pod(tracking_number)
                
                if result.get('success'):
                    # Cache result
                    if self.cache_enabled:
                        self._save_to_cache(tracking_number, carrier, result)
                    
                    result['source'] = 'api'
                    logger.info(f"✅ POD fetched successfully for {tracking_number}")
                    return result
                else:
                    logger.warning(f"Attempt {attempt + 1}/{retry_count} failed: {result.get('error')}")
                    
                    if attempt < retry_count - 1:
                        # Exponential backoff
                        import time
                        time.sleep(2 ** attempt)
                    
            except Exception as e:
                logger.error(f"POD fetch error (attempt {attempt + 1}): {e}")
                
                if attempt == retry_count - 1:
                    return {
                        'success': False,
                        'pod_url': None,
                        'pod_data': {},
                        'error': str(e),
                        'source': None
                    }
        
        # All retries failed
        return {
            'success': False,
            'pod_url': None,
            'pod_data': {},
            'error': 'Max retries exceeded',
            'source': None
        }
    
    def _get_connector(self, carrier: str):
        """Get or create carrier connector."""
        carrier_lower = carrier.lower()
        
        if carrier_lower in self._connectors:
            return self._connectors[carrier_lower]
        
        # Lazy load connectors
        try:
            if carrier_lower == 'colissimo':
                from src.integrations.colissimo_connector import ColissimoConnector
                api_key = os.getenv('LAPOSTE_API_KEY', 'demo_key')  # Use demo key for testing
                connector = ColissimoConnector(api_key=api_key)
            elif carrier_lower == 'chronopost':
                from src.integrations.chronopost_connector import ChronopostConnector
                connector = ChronopostConnector()
            elif carrier_lower == 'ups':
                from src.integrations.ups_connector import UPSConnector
                connector = UPSConnector()
            elif carrier_lower in ['dhl', 'dhl_express']:
                from src.integrations.dhl_connector import DHLConnector
                connector = DHLConnector()
            elif carrier_lower == 'fedex':
                from src.integrations.fedex_connector import FedExConnector
                connector = FedExConnector()
            else:
                logger.warning(f"Carrier {carrier} not supported")
                return None
            
            self._connectors[carrier_lower] = connector
            return connector
            
        except ImportError as e:
            logger.error(f"Failed to load connector for {carrier}: {e}")
            return None
    
    def _get_cache_path(self, tracking_number: str, carrier: str) -> Path:
        """Get cache file path for a tracking number."""
        filename = f"{carrier}_{tracking_number}.json"
        return self.CACHE_DIR / filename
    
    def _get_from_cache(self, tracking_number: str, carrier: str) -> Optional[Dict]:
        """Retrieve POD from cache if valid."""
        cache_path = self._get_cache_path(tracking_number, carrier)
        
        if not cache_path.exists():
            return None
        
        try:
            # Check cache age
            cache_age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
            
            if cache_age > timedelta(days=self.CACHE_DURATION_DAYS):
                logger.info(f"Cache expired for {tracking_number}")
                cache_path.unlink()  # Delete old cache
                return None
            
            # Load cached data
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
            
            return cached_data
            
        except Exception as e:
            logger.error(f"Failed to read cache: {e}")
            return None
    
    def _save_to_cache(self, tracking_number: str, carrier: str, result: Dict):
        """Save POD result to cache."""
        try:
            cache_path = self._get_cache_path(tracking_number, carrier)
            
            cache_data = {
                'pod_url': result.get('pod_url'),
                'pod_data': result.get('pod_data', {}),
                'cached_at': datetime.now().isoformat()
            }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"POD cached for {tracking_number}")
            
        except Exception as e:
            logger.error(f"Failed to cache POD: {e}")
    
    def detect_carrier_from_tracking(self, tracking_number: str) -> Optional[str]:
        """
        Auto-detect carrier from tracking number format.
        
        Returns:
            Carrier name or None if cannot detect
        """
        tracking = tracking_number.upper().strip()
        
        # Colissimo/La Poste: Starts with FR or 2 letters + 9 digits
        if tracking.startswith('FR') or (len(tracking) == 13 and tracking[:2].isalpha()):
            return 'colissimo'
        
        # Chronopost: Starts with CH or XP
        if tracking.startswith(('CH', 'XP')):
            return 'chronopost'
        
        # UPS: 18 characters starting with 1Z
        if tracking.startswith('1Z') and len(tracking) == 18:
            return 'ups'
        
        # FedEx: 12 or 15 digits
        if tracking.isdigit() and len(tracking) in [12, 15]:
            return 'fedex'
        
        # DHL: 10 digits
        if tracking.isdigit() and len(tracking) == 10:
            return 'dhl'
        
        logger.warning(f"Could not detect carrier for tracking: {tracking_number}")
        return None


if __name__ == "__main__":
    # Test POD Fetcher
    print("=" * 70)
    print("POD FETCHER - Test")
    print("=" * 70)
    
    fetcher = PODFetcher()
    
    # Test with sample tracking
    print("\n📦 Testing POD fetch...")
    result = fetcher.fetch_pod('FR123456789TEST', 'colissimo')
    
    print(f"\nResult:")
    print(f"  Success: {result['success']}")
    print(f"  POD URL: {result.get('pod_url', 'N/A')}")
    print(f"  Error: {result.get('error', 'None')}")
    print(f"  Source: {result.get('source', 'N/A')}")
    
    # Test carrier detection
    print("\n🔍 Testing carrier detection...")
    test_trackings = [
        'FR123456789AB',
        '1Z999AA10123456784',
        'CH123456789FR',
        '123456789012'
    ]
    
    for tracking in test_trackings:
        carrier = fetcher.detect_carrier_from_tracking(tracking)
        print(f"  {tracking} → {carrier or 'Unknown'}")
    
    print("\n" + "=" * 70)
    print("✅ POD Fetcher Ready")
    print("=" * 70)
