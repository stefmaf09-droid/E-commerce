"""
Mondial Relay Scraper.
Retrieves tracking information from the Mondial Relay public tracking page.
Requires both Tracking Number and Zip Code.
"""

import logging
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any, List
from datetime import datetime
import re
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class MondialRelayScraper(BaseScraper):
    """Scraper for Mondial Relay public tracking page."""
    
    BASE_URL = "https://www.mondialrelay.fr/suivi-de-colis/"
    
    def get_tracking(self, tracking_number: str, zip_code: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get tracking information for a Mondial Relay parcel.
        
        Args:
            tracking_number: The parcel tracking number (8, 10, or 12 digits).
            zip_code: The recipient's postal code (Required for Mondial Relay).
            
        Returns:
            Dictionary containing tracking information or None if failed.
        """
        if not zip_code:
            logger.warning(f"Zip code is required for Mondial Relay tracking: {tracking_number}")
            return None
            
        # Mondial Relay supports direct URL with parameters
        url = f"{self.BASE_URL}?numeroExpedition={tracking_number}&codePostal={zip_code}"
        
        soup = self._fetch_page(url)
        if not soup:
            logger.error(f"Failed to fetch tracking page for {tracking_number}")
            return None
            
        try:
            return self._parse_tracking_page(soup, tracking_number)
        except Exception as e:
            logger.error(f"Error parsing Mondial Relay page for {tracking_number}: {e}")
            return None

    def scrape(self, **kwargs) -> List[Dict]:
        """
        Implementation of abstract method.
        Not used for single tracking.
        """
        raise NotImplementedError("Use get_tracking() for single parcel tracking")

    def _parse_tracking_page(self, soup: BeautifulSoup, tracking_number: str) -> Optional[Dict[str, Any]]:
        """Parse the tracking page HTML."""
        
        # Check for error messages
        error_container = soup.find('div', class_=lambda x: x and 'alert-danger' in x)
        if error_container and "aucun colis" in error_container.get_text().lower():
             logger.info(f"Tracking number {tracking_number} not found.")
             return {'status': 'not_found', 'error': 'Number not found'}

        # Status is often in a specific step container or detailed list
        # We need to adapt this based on the actual HTML structure
        # Assuming standard structure based on inspection:
        
        # 1. Delivery Status
        # Look for the last active step or status message
        steps = soup.select('.step-content')
        status_text = "Unknown"
        is_delivered = False
        delivery_date = None
        
        # Attempt to find the main status header
        main_status = soup.find('p', class_='text-marketing') # Often contains "Votre colis est livré"
        if main_status:
            status_text = main_status.get_text(strip=True)
        
        # Check for "Livré" keyword
        if 'livré' in status_text.lower():
            is_delivered = True
            
        # 2. History / Timeline
        history: List[Dict[str, str]] = []
        timeline_items = soup.select('.timeline-item') # Hypothetical selector, adjust if needed
        
        # If specific timeline selectors aren't standard, we might scrape the steps
        if not timeline_items:
             # Try scraping steps
             for step in steps:
                 date_elem = step.find('span', class_='date')
                 label_elem = step.find('span', class_='label')
                 if date_elem and label_elem:
                     history.append({
                         'date': date_elem.get_text(strip=True),
                         'status': label_elem.get_text(strip=True)
                     })

        # Try to extract delivery date from status or history
        if is_delivered:
             # Look for date in status text or last history item
             # Regex for date: dd/mm/yyyy
             date_match = re.search(r'\d{2}/\d{2}/\d{4}', status_text)
             if date_match:
                 delivery_date = date_match.group(0)
             elif history:
                 delivery_date = history[0].get('date') # Assuming newest first

        return {
            'carrier': 'Mondial Relay',
            'tracking_number': tracking_number,
            'status': status_text,
            'is_delivered': is_delivered,
            'delivery_date': delivery_date,
            'history': history,
            'pod_url': None, # Scraper likely won't get a legal POD signature image easily
            'scraped_at': datetime.now().isoformat()
        }
