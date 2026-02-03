"""
Trustpilot scraper for carrier reviews.

Scrapes customer reviews about shipping carriers to extract dispute patterns.
"""

from typing import List, Dict, Optional
import logging
from urllib.parse import urljoin
import time

from .base_scraper import BaseScraper
from .utils.text_processor import DisputePatternExtractor

logger = logging.getLogger(__name__)


class TrustpilotScraper(BaseScraper):
    """Scraper for Trustpilot carrier reviews."""
    
    # Carrier Trustpilot URLs
    CARRIERS = {
        'colissimo': 'https://fr.trustpilot.com/review/www.laposte.fr',
        'chronopost': 'https://fr.trustpilot.com/review/www.chronopost.fr',
        'dpd': 'https://fr.trustpilot.com/review/www.dpd.fr',
        'ups': 'https://fr.trustpilot.com/review/www.ups.com',
        'fedex': 'https://fr.trustpilot.com/review/www.fedex.com',
        'dhl': 'https://fr.trustpilot.com/review/www.dhl.fr'
    }
    
    def __init__(self, rate_limit: float = 0.5):  # Conservative: 1 req per 2 seconds
        """
        Initialize Trustpilot scraper.
        
        Args:
            rate_limit: Requests per second (default: 0.5 for safety)
        """
        super().__init__(rate_limit=rate_limit)
        self.text_processor = DisputePatternExtractor()
    
    def scrape(
        self, 
        carriers: Optional[List[str]] = None,
        max_pages: int = 3,
        min_rating: int = 3
    ) -> List[Dict]:
        """
        Scrape Trustpilot reviews for carriers.
        
        Args:
            carriers: List of carrier names to scrape (None = all)
            max_pages: Maximum pages per carrier
            min_rating: Only scrape reviews with rating <= this (1-5)
            
        Returns:
            List of review dictionaries
        """
        if carriers is None:
            carriers = list(self.CARRIERS.keys())
        
        all_reviews = []
        
        for carrier in carriers:
            if carrier not in self.CARRIERS:
                logger.warning(f"Unknown carrier: {carrier}")
                continue
            
            logger.info(f"Scraping {carrier} reviews...")
            carrier_reviews = self._scrape_carrier(
                carrier, 
                self.CARRIERS[carrier],
                max_pages,
                min_rating
            )
            
            all_reviews.extend(carrier_reviews)
            logger.info(f"Scraped {len(carrier_reviews)} reviews for {carrier}")
        
        return all_reviews
    
    def _scrape_carrier(
        self, 
        carrier_name: str, 
        base_url: str, 
        max_pages: int,
        min_rating: int
    ) -> List[Dict]:
        """Scrape reviews for a specific carrier."""
        reviews = []
        
        for page in range(1, max_pages + 1):
            # Trustpilot pagination
            if page == 1:
                url = base_url
            else:
                url = f"{base_url}?page={page}"
            
            soup = self._fetch_page(url)
            
            if not soup:
                logger.error(f"Failed to fetch page {page} for {carrier_name}")
                break
            
            # Extract reviews from page
            page_reviews = self._extract_reviews_from_page(soup, carrier_name, min_rating)
            
            if not page_reviews:
                logger.info(f"No more reviews found on page {page}")
                break
            
            reviews.extend(page_reviews)
            
            # Be extra careful with Trustpilot
            time.sleep(2)
        
        return reviews
    
    def _extract_reviews_from_page(
        self, 
        soup, 
        carrier_name: str,
        min_rating: int
    ) -> List[Dict]:
        """
        Extract review data from a Trustpilot page.
        
        Note: This is a simplified version. Real Trustpilot scraping
        would need more sophisticated selectors and potentially Selenium.
        """
        reviews = []
        
        # Note: Trustpilot's HTML structure changes frequently
        # This is a basic implementation that may need updates
        
        # Try to find review cards
        review_cards = soup.find_all('article', class_=lambda x: x and 'review' in x.lower())
        
        if not review_cards:
            # Alternative selector
            review_cards = soup.find_all('div', {'data-service-review-card-paper': True})
        
        for card in review_cards:
            try:
                review_data = self._parse_review_card(card, carrier_name)
                
                if review_data and review_data['rating'] <= min_rating:
                    # Extract dispute patterns
                    patterns = self.text_processor.extract_patterns(review_data['text'])
                    review_data['patterns'] = patterns
                    
                    reviews.append(review_data)
                    
            except Exception as e:
                logger.error(f"Error parsing review card: {e}")
                continue
        
        return reviews
    
    def _parse_review_card(self, card, carrier_name: str) -> Optional[Dict]:
        """
        Parse a single review card.
        
        Returns:
            Dictionary with review data or None if parsing failed
        """
        try:
            # Extract rating (1-5 stars)
            rating_elem = card.find('div', class_=lambda x: x and 'star' in x.lower())
            rating = 3  # Default if not found
            
            if rating_elem:
                # Try to extract from class or data attribute
                rating_text = rating_elem.get('data-service-review-rating', '')
                if rating_text:
                    rating = int(rating_text)
            
            # Extract title
            title_elem = card.find('h2', class_=lambda x: x and 'title' in x.lower())
            title = title_elem.get_text(strip=True) if title_elem else ''
            
            # Extract review text
            text_elem = card.find('p', class_=lambda x: x and 'content' in x.lower())
            if not text_elem:
                text_elem = card.find('div', class_=lambda x: x and 'content' in x.lower())
            
            text = text_elem.get_text(strip=True) if text_elem else ''
            
            # Extract date
            date_elem = card.find('time')
            date = date_elem.get('datetime', '') if date_elem else ''
            
            # Extract author (anonymized)
            author_elem = card.find('span', class_=lambda x: x and 'name' in x.lower())
            author_initials = author_elem.get_text(strip=True)[:2] if author_elem else 'XX'
            
            if not text:
                return None
            
            return {
                'carrier': carrier_name,
                'rating': rating,
                'title': title,
                'text': text,
                'date': date,
                'author_initials': author_initials,  # Privacy: only initials
                'source': 'trustpilot'
            }
            
        except Exception as e:
            logger.error(f"Error parsing review: {e}")
            return None


def main_test():
    """Test function for Trustpilot scraper."""
    logging.basicConfig(level=logging.INFO)
    
    scraper = TrustpilotScraper()
    
    # Test with just one carrier and 1 page
    print("Testing Trustpilot scraper with Colissimo (1 page)...")
    reviews = scraper.scrape(
        carriers=['colissimo'],
        max_pages=1,
        min_rating=3  # Only 1-3 star reviews
    )
    
    print(f"\n✅ Scraped {len(reviews)} reviews")
    
    if reviews:
        # Show first review
        first = reviews[0]
        print("\nFirst review:")
        print(f"- Carrier: {first['carrier']}")
        print(f"- Rating: {first['rating']}/5")
        print(f"- Title: {first['title']}")
        print(f"- Text: {first['text'][:200]}...")
        print(f"- Patterns: {first.get('patterns', {})}")
        
        # Save data
        scraper.save_data(reviews, 'trustpilot_test.json')
        print("\n✅ Data saved to data/scraped/trustpilot_test.json")
    else:
        print("\n⚠️ No reviews found. This might indicate:")
        print("  - Trustpilot's HTML structure has changed")
        print("  - Rate limiting or blocking")
        print("  - Network issues")


if __name__ == "__main__":  # pragma: no cover
    main_test()
