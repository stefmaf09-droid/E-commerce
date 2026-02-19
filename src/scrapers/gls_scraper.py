"""
GLS Scraper.
Retrieves tracking information from the GLS public API.
GLS provides a semi-public JSON endpoint accessible without authentication.
"""

import logging
import requests
import re
from typing import Optional, Dict, Any, List
from datetime import datetime
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class GLSScraper(BaseScraper):
    """Scraper for GLS public tracking API."""

    # GLS public tracking API (no auth required)
    API_URL = "https://gls-group.eu/app/service/open/rest/EU/fr/rstt001"
    TRACK_PAGE_URL = "https://gls-group.eu/FR/fr/suivi-colis.html"

    def get_tracking(self, tracking_number: str) -> Optional[Dict[str, Any]]:
        """
        Get tracking information for a GLS parcel.

        Args:
            tracking_number: The parcel tracking number.

        Returns:
            Dictionary containing tracking information or None if failed.
        """
        try:
            return self._fetch_api(tracking_number)
        except Exception as e:
            logger.error(f"GLS tracking failed for {tracking_number}: {e}")
            return self._fallback_response(tracking_number, str(e))

    def scrape(self, **kwargs) -> List[Dict]:
        raise NotImplementedError("Use get_tracking() for single parcel tracking")

    def _fetch_api(self, tracking_number: str) -> Optional[Dict[str, Any]]:
        """Fetch from GLS public REST API."""
        params = {
            'match': tracking_number,
            'caller': 'witt002',
            'milis': str(int(datetime.now().timestamp() * 1000)),
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/javascript, */*',
            'Referer': self.TRACK_PAGE_URL,
            'Origin': 'https://gls-group.eu',
        }

        resp = requests.get(self.API_URL, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        return self._parse_api(data, tracking_number)

    def _parse_api(self, data: dict, tracking_number: str) -> Dict[str, Any]:
        """Parse GLS API response."""
        try:
            # GLS API returns: {"tuDetail": {"progressBar": {...}, "history": [...], ...}}
            tu_detail = data.get('tuDetail', data)
            if not tu_detail:
                return self._fallback_response(tracking_number, "Empty response")

            # Status from progress bar or history
            progress = tu_detail.get('progressBar', {})
            status_text = progress.get('statusText', tu_detail.get('status', 'Unknown'))

            is_delivered = any(
                kw in (status_text or '').lower()
                for kw in ['livré', 'delivered', 'remis', 'distribué']
            )

            # Delivery date
            delivery_date = tu_detail.get('deliveryDate') or tu_detail.get('deliveredDate')

            # History
            history = []
            for event in tu_detail.get('history', []):
                date_str = event.get('date', '')
                time_str = event.get('time', '')
                desc = event.get('evtDscr', event.get('description', ''))
                location = event.get('address', {})
                loc_str = f"{location.get('city', '')} {location.get('countryCode', '')}".strip() if isinstance(location, dict) else str(location)

                history.append({
                    'date': f"{date_str} {time_str}".strip(),
                    'status': desc,
                    'location': loc_str
                })

            return {
                'carrier': 'GLS',
                'tracking_number': tracking_number,
                'status': status_text,
                'is_delivered': is_delivered,
                'delivery_date': delivery_date,
                'history': history,
                'pod_url': tu_detail.get('podImgUrl'),
                'scraped_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.warning(f"GLS parse error: {e}")
            return self._fallback_response(tracking_number, str(e))

    def _fallback_response(self, tracking_number: str, error: str) -> Dict[str, Any]:
        return {
            'carrier': 'GLS',
            'tracking_number': tracking_number,
            'status': 'error',
            'is_delivered': False,
            'delivery_date': None,
            'history': [],
            'pod_url': None,
            'error': error,
            'scraped_at': datetime.now().isoformat()
        }
