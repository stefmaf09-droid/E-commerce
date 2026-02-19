"""
Chronopost Scraper.
Retrieves tracking information from the Chronopost public tracking page.
"""

import logging
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any, List
from datetime import datetime
import re
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class ChronopostScraper(BaseScraper):
    """Scraper for Chronopost public tracking page."""
    
    BASE_URL = "https://www.chronopost.fr/tracking-no-cms/suivi-page"
    
    def get_tracking(self, tracking_number: str) -> Optional[Dict[str, Any]]:
        """
        Get tracking information for a Chronopost parcel.
        
        Args:
            tracking_number: The parcel tracking number.
            
        Returns:
            Dictionary containing tracking information or None if failed.
        """
        # Direct URL with parameters
        url = f"{self.BASE_URL}?listeNumerosLT={tracking_number}&langue=fr"
        
        soup = self._fetch_page(url)
        if not soup:
            logger.error(f"Failed to fetch tracking page for {tracking_number}")
            return None
            
        try:
            return self._parse_tracking_page(soup, tracking_number)
        except Exception as e:
            logger.error(f"Error parsing Chronopost page for {tracking_number}: {e}")
            return None

    def scrape(self, **kwargs) -> List[Dict]:
        """
        Implementation of abstract method.
        Not used for single tracking.
        """
        raise NotImplementedError("Use get_tracking() for single parcel tracking")

    def _parse_tracking_page(self, soup: BeautifulSoup, tracking_number: str) -> Optional[Dict[str, Any]]:
        """Parse the tracking page HTML."""
        
        # Check for error/invalid number
        # Chronopost might show "Aucun résultat" or similar in a container
        content_text = soup.get_text().lower()
        if "aucun résultat" in content_text or "nous n'avons pas d'information" in content_text:
             logger.info(f"Tracking number {tracking_number} not found or no info.")
             return {'status': 'not_found', 'error': 'Number not found'}

        # Status is usually in a banner or specific container
        status_text = "Unknown"
        is_delivered = False
        delivery_date = None
        
        # 1. Main Status
        # Selector based on inspection: .ch-colis-information or #banner-container h2/h3
        banner = soup.find(class_='ch-colis-information')
        if banner:
            status_text = banner.get_text(strip=True)
        else:
            # Fallback to finding the first strong/bold element in results
            first_strong = soup.select_one('#banner-container strong')
            if first_strong:
                status_text = first_strong.get_text(strip=True)

        # Check for "Livré"
        if 'livré' in status_text.lower():
            is_delivered = True

        # 2. History / Timeline
        history: List[Dict[str, str]] = []
        # Chronopost uses a table often with class 'suivi-colis-table' or similar structure in #tracking-container
        table = soup.select_one('table.table, table.suivi-colis-table')
        
        if table:
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    # Format usually: Date | Location | Event
                    date_text = cols[0].get_text(strip=True)
                    event_text = cols[-1].get_text(strip=True) # Last col is usually event
                    history.append({
                        'date': date_text,
                        'status': event_text
                    })
        
        # 3. Delivery Date Extraction
        if is_delivered:
             # Try regex on status
             date_match = re.search(r'\d{2}/\d{2}/\d{4}', status_text)
             if date_match:
                 delivery_date = date_match.group(0)
             elif history:
                 # Check history for "Livré" event
                 for event in history:
                     if 'livré' in event['status'].lower():
                         # Extract date from the date column (which might be "le 19/02/2026 à 10:00")
                         row_date = event['date']
                         date_match_row = re.search(r'\d{2}/\d{2}/\d{4}', row_date)
                         if date_match_row:
                             delivery_date = date_match_row.group(0)
                         break
                 if not delivery_date and history:
                     # Fallback to latest event date
                     delivery_date = history[0].get('date', '').split(' ')[0]

        return {
            'carrier': 'Chronopost',
            'tracking_number': tracking_number,
            'status': status_text,
            'is_delivered': is_delivered,
            'delivery_date': delivery_date,
            'history': history,
            'pod_url': None, 
            'scraped_at': datetime.now().isoformat()
        }
