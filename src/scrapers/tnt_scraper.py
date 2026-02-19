"""
TNT Scraper.
Retrieves tracking information from the TNT public tracking API.
TNT (FedEx subsidiary) has a public JSON tracking endpoint.
"""

import logging
import requests
import re
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any, List
from datetime import datetime
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class TNTScraper(BaseScraper):
    """Scraper for TNT public tracking endpoint."""

    # TNT public tracking API
    API_URL = "https://www.tnt.com/api/v3/shipment"
    PAGE_URL = "https://www.tnt.com/express/fr_fr/site/shipping-tools/tracking.html"

    def get_tracking(self, tracking_number: str) -> Optional[Dict[str, Any]]:
        """
        Get tracking information for a TNT parcel.

        Args:
            tracking_number: The parcel tracking number.

        Returns:
            Dictionary containing tracking information or None if failed.
        """
        try:
            return self._fetch_api(tracking_number)
        except Exception as e:
            logger.warning(f"TNT API failed for {tracking_number}: {e}")

        # Fallback: HTML page
        try:
            return self._fetch_html(tracking_number)
        except Exception as e:
            logger.error(f"TNT scraping failed for {tracking_number}: {e}")
            return self._fallback_response(tracking_number, str(e))

    def scrape(self, **kwargs) -> List[Dict]:
        raise NotImplementedError("Use get_tracking() for single parcel tracking")

    def _fetch_api(self, tracking_number: str) -> Optional[Dict[str, Any]]:
        """Fetch from TNT tracking API."""
        params = {
            'con': tracking_number,
            'searchType': 'CON',
            'locale': 'fr_FR',
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Referer': self.PAGE_URL,
        }

        resp = requests.get(self.API_URL, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        return self._parse_api(data, tracking_number)

    def _parse_api(self, data: dict, tracking_number: str) -> Optional[Dict[str, Any]]:
        """Parse TNT API JSON response."""
        try:
            # TNT typically returns {"shipmentList": [...]}
            shipments = data.get('shipmentList', [data]) if 'shipmentList' in data else [data]
            if not shipments:
                return self._fallback_response(tracking_number, "No shipments found")

            s = shipments[0]

            # Summary status
            summary = s.get('summary', {})
            status_text = summary.get('statusDescription', s.get('status', 'Unknown'))

            is_delivered = any(
                kw in (status_text or '').lower()
                for kw in ['delivered', 'livré', 'remis', 'distribué']
            )

            delivery_date = summary.get('deliveryDate') or s.get('deliveryDate')

            # History from scanHistory
            history = []
            for event in s.get('scanHistory', s.get('events', [])):
                history.append({
                    'date': event.get('date', '') + ' ' + event.get('time', ''),
                    'status': event.get('statusDescription', event.get('description', '')),
                    'location': event.get('location', {}).get('depotCity', '') if isinstance(event.get('location'), dict) else ''
                })

            return {
                'carrier': 'TNT',
                'tracking_number': tracking_number,
                'status': status_text,
                'is_delivered': is_delivered,
                'delivery_date': delivery_date,
                'history': history,
                'pod_url': s.get('podUrl'),
                'scraped_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.warning(f"TNT parse error: {e}")
            return None

    def _fetch_html(self, tracking_number: str) -> Optional[Dict[str, Any]]:
        """Fallback: scrape the HTML tracking page."""
        url = f"{self.PAGE_URL}?searchType=CON&cons={tracking_number}&locale=fr_FR"
        soup = self._fetch_page(url)
        if not soup:
            return self._fallback_response(tracking_number, "Failed to fetch HTML")

        # Try to find status
        status_el = soup.select_one('.shipment-status, .tracking-status, h3.status')
        status_text = status_el.get_text(strip=True) if status_el else "Unknown"

        is_delivered = any(kw in status_text.lower() for kw in ['delivered', 'livré'])

        # History from table
        history = []
        for row in soup.select('table tr, .scan-event'):
            cols = row.find_all('td')
            if len(cols) >= 2:
                history.append({
                    'date': cols[0].get_text(strip=True),
                    'status': cols[-1].get_text(strip=True)
                })

        return {
            'carrier': 'TNT',
            'tracking_number': tracking_number,
            'status': status_text,
            'is_delivered': is_delivered,
            'delivery_date': None,
            'history': history,
            'pod_url': None,
            'scraped_at': datetime.now().isoformat()
        }

    def _fallback_response(self, tracking_number: str, error: str) -> Dict[str, Any]:
        return {
            'carrier': 'TNT',
            'tracking_number': tracking_number,
            'status': 'error',
            'is_delivered': False,
            'delivery_date': None,
            'history': [],
            'pod_url': None,
            'error': error,
            'scraped_at': datetime.now().isoformat()
        }
