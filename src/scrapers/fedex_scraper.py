"""
FedEx Scraper.
Retrieves tracking information from the FedEx public tracking page.
Uses the public web tracking endpoint (no API key required).
"""

import logging
import requests
import re
from typing import Optional, Dict, Any, List
from datetime import datetime
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class FedExScraper(BaseScraper):
    """Scraper for FedEx public tracking page."""

    # FedEx public tracking endpoint (returns JSON)
    TRACK_URL = "https://www.fedex.com/trackingCal/track"

    def get_tracking(self, tracking_number: str) -> Optional[Dict[str, Any]]:
        """
        Get tracking information for a FedEx parcel.

        Args:
            tracking_number: The parcel tracking number.

        Returns:
            Dictionary containing tracking information or None if failed.
        """
        try:
            return self._fetch_via_api(tracking_number)
        except Exception as e:
            logger.error(f"FedEx tracking failed for {tracking_number}: {e}")
            return self._fallback_response(tracking_number, str(e))

    def scrape(self, **kwargs) -> List[Dict]:
        raise NotImplementedError("Use get_tracking() for single parcel tracking")

    def _fetch_via_api(self, tracking_number: str) -> Optional[Dict[str, Any]]:
        """Fetch via FedEx public tracking JSON endpoint."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://www.fedex.com',
            'Referer': f'https://www.fedex.com/fr-fr/tracking.html?tracknumbers={tracking_number}',
            'X-Requested-With': 'XMLHttpRequest',
        }

        payload = {
            'data': f'{{"TrackPackagesRequest":{{"appType":"WTRK","uniqueKey":"","processingParameters":{{}},"trackingInfoList":[{{"trackNumberInfo":{{"trackingNumber":"{tracking_number}","trackingQualifier":"","trackingCarrier":""}}}}]}}}}',
            'action': 'trackpackages',
            'locale': 'fr_FR',
            'version': '99',
            'format': 'json',
        }

        resp = requests.post(self.TRACK_URL, headers=headers, data=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        return self._parse_api_response(data, tracking_number)

    def _parse_api_response(self, data: dict, tracking_number: str) -> Optional[Dict[str, Any]]:
        """Parse the FedEx JSON API response."""
        try:
            track_reply = data.get('TrackPackagesResponse', {})
            packages = track_reply.get('packageList', [])
            if not packages:
                return self._fallback_response(tracking_number, "No packages found")

            pkg = packages[0]
            keyStatus = pkg.get('keyStatus', 'Unknown')
            is_delivered = 'délivré' in keyStatus.lower() or 'delivered' in keyStatus.lower()

            # Delivery date
            delivery_date = None
            if is_delivered:
                delivery_date = pkg.get('deliveryDate', '') or pkg.get('actualDeliveryTime', '')

            # History
            history = []
            for event in pkg.get('scanEventList', []):
                history.append({
                    'date': event.get('date', '') + ' ' + event.get('time', ''),
                    'status': event.get('status', ''),
                    'location': event.get('scanLocation', '')
                })

            return {
                'carrier': 'FedEx',
                'tracking_number': tracking_number,
                'status': keyStatus,
                'is_delivered': is_delivered,
                'delivery_date': delivery_date,
                'history': history,
                'pod_url': None,
                'scraped_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.warning(f"FedEx response parsing failed: {e}")
            return self._fallback_response(tracking_number, str(e))

    def _fallback_response(self, tracking_number: str, error: str) -> Dict[str, Any]:
        """Return a structured error response."""
        return {
            'carrier': 'FedEx',
            'tracking_number': tracking_number,
            'status': 'error',
            'is_delivered': False,
            'delivery_date': None,
            'history': [],
            'pod_url': None,
            'error': error,
            'scraped_at': datetime.now().isoformat()
        }
