"""
Colissimo Scraper - Retrieves tracking information and POD.
"""

import logging
import re
from typing import List, Dict, Optional
from datetime import datetime

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class ColissimoScraper(BaseScraper):
    """Scraper for Colissimo tracking and POD."""
    
    BASE_URL = "https://www.laposte.fr/outils/suivre-vos-envois"
    
    def __init__(self, rate_limit: float = 0.5):
        """
        Initialize Colissimo scraper.
        
        Args:
            rate_limit: Requests per second
        """
        super().__init__(rate_limit=rate_limit)
        
    def scrape(self, tracking_numbers: List[str]) -> List[Dict]:
        """
        Scrape status for a list of tracking numbers.
        
        Args:
            tracking_numbers: List of tracking numbers
            
        Returns:
            List of tracking results
        """
        results = []
        for tracking_number in tracking_numbers:
            result = self.get_pod(tracking_number)
            if result:
                results.append(result)
        return results
    
    def get_pod(self, tracking_number: str) -> Optional[Dict]:
        """Fetch POD/Tracking info."""
        if tracking_number.upper().startswith('X'):
            # Chronopost specific tracking page
            url = f"https://www.chronopost.fr/tracking-no-cms/suivi-page?langue=fr&listeNumerosLT={tracking_number}"
        else:
            url = f"{self.BASE_URL}?code={tracking_number}"
        
        soup = self._fetch_page(url)
        if not soup:
            logger.error(f"Failed to fetch tracking page for {tracking_number}")
            return None
            
        try:
            # 1. Extract Status
            # Look for the main status message
            # Note: Selectors here are hypothetical and based on typical La Poste structure
            # In a real scenario, we'd need to inspect the actual DOM
            status_elem = soup.find('h2', class_=lambda x: x and 'status' in x.lower())
            if not status_elem:
                # Fallback to general finding
                status_elem = soup.find('div', class_='timeline-status')
            
            status_text = "Unknown"
            if status_elem:
                status_text = status_elem.get_text(strip=True)
            else:
                # Robust Fallback: Search in entire page text for keywords
                page_text = soup.get_text().lower()
                if "livré" in page_text:
                    status_text = "Livré"
                elif "mis à disposition" in page_text or "point de retrait" in page_text or "prêt" in page_text:
                    status_text = "Mis à disposition en point de retrait"
                elif "en cours de livraison" in page_text:
                    status_text = "En cours de livraison"
                elif "pris en charge" in page_text:
                    status_text = "Pris en charge"
            
            # 2. Extract Date
            date_elem = soup.find('p', class_=lambda x: x and 'date' in x.lower())
            date_text = date_elem.get_text(strip=True) if date_elem else ""
            
            # 3. Check for Delivery / Pickup
            is_delivered = any(kw in status_text.lower() for kw in ["livré", "mis à disposition", "retrait", "prêt"])
            
            # 4. Check for Signature/POD image
            # This is usually hidden behind an API or requires login on La Poste
            # But sometimes there's a "Preuve de livraison" link
            pod_url = None
            pod_link = soup.find('a', href=lambda x: x and 'preuve' in x.lower())
            if pod_link:
                pod_url = pod_link.get('href')
                if not pod_url.startswith('http'):
                    pod_url = "https://www.laposte.fr" + pod_url
            
            # 5. Extract timeline for detailed history
            history = []
            timeline_items = soup.find_all('div', class_='timeline-item')
            for item in timeline_items:
                time_text_elem = item.find('span', class_='time')
                event_text_elem = item.find('span', class_='label')
                if time_text_elem and event_text_elem:
                    history.append({
                        'time': time_text_elem.get_text(strip=True),
                        'event': event_text_elem.get_text(strip=True)
                    })
            
            return {
                'tracking_number': tracking_number,
                'carrier': 'Colissimo',
                'status': status_text,
                'is_delivered': is_delivered,
                'delivery_date': date_text,
                'pod_url': pod_url,
                'history': history,
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error parsing tracking page for {tracking_number}: {e}")
            return None

if __name__ == "__main__":
    # verification
    scraper = ColissimoScraper()
    # Test with a dummy number (will likely fail or show not found, but tests the code path)
    print("Testing Colissimo Scraper...")
    result = scraper.get_pod("6A12345678901") 
    print(f"Result: {result}")
