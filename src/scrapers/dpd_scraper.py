"""
DPD Scraper.
Retrieves tracking information from the DPD France public tracking page.
"""

import logging
import requests
import json
import re
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any, List
from datetime import datetime
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class DPDScraper(BaseScraper):
    """Scraper for DPD France public tracking page."""

    BASE_URL = "https://trace.dpd.fr/fr/trace/{tracking}"
    # JSON data API
    API_URL = "https://trace.dpd.fr/fr/trace/{tracking}/json"

    def get_tracking(self, tracking_number: str) -> Optional[Dict[str, Any]]:
        """
        Get tracking information for a DPD parcel.

        Args:
            tracking_number: The parcel tracking number.

        Returns:
            Dictionary containing tracking information or None if failed.
        """
        # Try JSON API first (cleaner)
        try:
            result = self._fetch_json_api(tracking_number)
            if result:
                return result
        except Exception as e:
            logger.warning(f"DPD JSON API failed for {tracking_number}: {e}")

        # Fallback to HTML scraping
        try:
            return self._fetch_html(tracking_number)
        except Exception as e:
            logger.error(f"DPD HTML scraping failed for {tracking_number}: {e}")
            return self._fallback_response(tracking_number, str(e))

    def scrape(self, **kwargs) -> List[Dict]:
        raise NotImplementedError("Use get_tracking() for single parcel tracking")

    def _fetch_json_api(self, tracking_number: str) -> Optional[Dict[str, Any]]:
        """Fetch from DPD JSON API endpoint."""
        url = self.API_URL.format(tracking=tracking_number)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Referer': f'https://trace.dpd.fr/fr/trace/{tracking_number}',
        }

        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        return self._parse_json_response(data, tracking_number)

    def _parse_json_response(self, data: dict, tracking_number: str) -> Optional[Dict[str, Any]]:
        """Parse DPD JSON API response."""
        try:
            # DPD JSON structure varies; try common paths
            shipments = data.get('shipments', data.get('parcels', [data]))
            if not shipments:
                return None

            shipment = shipments[0] if isinstance(shipments, list) else shipments

            # Status
            status_info = shipment.get('status', {})
            if isinstance(status_info, dict):
                status_text = status_info.get('label', status_info.get('description', 'Unknown'))
            else:
                status_text = str(status_info)

            is_delivered = any(
                kw in status_text.lower()
                for kw in ['livré', 'delivered', 'remis', 'distribué']
            )

            # Delivery date
            delivery_date = shipment.get('deliveryDate') or shipment.get('estimatedDeliveryDate')

            # History
            history = []
            for event in shipment.get('events', shipment.get('history', [])):
                history.append({
                    'date': event.get('date', '') + ' ' + event.get('time', ''),
                    'status': event.get('label', event.get('description', '')),
                    'location': event.get('location', {}).get('label', '') if isinstance(event.get('location'), dict) else ''
                })

            return {
                'carrier': 'DPD',
                'tracking_number': tracking_number,
                'status': status_text,
                'is_delivered': is_delivered,
                'delivery_date': delivery_date,
                'history': history,
                'pod_url': shipment.get('podUrl'),
                'scraped_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.warning(f"DPD JSON parse error: {e}")
            return None

    def _fetch_html(self, tracking_number: str) -> Optional[Dict[str, Any]]:
        """Fallback: scrape the HTML tracking page."""
        url = self.BASE_URL.format(tracking=tracking_number)
        soup = self._fetch_page(url)
        if not soup:
            return self._fallback_response(tracking_number, "Failed to fetch HTML")

        # Status
        status_el = soup.select_one('.timeline__step--current .timeline__label') or \
                    soup.select_one('.tracking-status') or \
                    soup.select_one('h2.status')
        status_text = status_el.get_text(strip=True) if status_el else "Unknown"

        is_delivered = any(kw in status_text.lower() for kw in ['livré', 'delivered', 'remis'])

        # History
        history = []
        for row in soup.select('.timeline__step, .tracking-event, tr'):
            cells = row.find_all(['td', 'li', 'span'])
            if len(cells) >= 2:
                history.append({
                    'date': cells[0].get_text(strip=True),
                    'status': cells[-1].get_text(strip=True)
                })

        return {
            'carrier': 'DPD',
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
            'carrier': 'DPD',
            'tracking_number': tracking_number,
            'status': 'error',
            'is_delivered': False,
            'delivery_date': None,
            'history': [],
            'pod_url': None,
            'error': error,
            'scraped_at': datetime.now().isoformat()
        }
