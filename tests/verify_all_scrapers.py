
import logging
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.scrapers.colissimo_scraper import ColissimoScraper
from src.scrapers.mondial_relay_scraper import MondialRelayScraper
from src.scrapers.chronopost_scraper import ChronopostScraper
from src.connectors.dhl_connector import DHLConnector

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ScraperTest')

def test_scrapers():
    print("--- STARTING SCRAPER VERIFICATION ---")
    
    # 1. Colissimo
    print("\n[TEST] Colissimo Scraper")
    try:
        colissimo = ColissimoScraper()
        # Test with a dummy number (expecting 'not_found' or None, but no crash)
        result = colissimo.get_pod("6A12345678901")
        print(f"Result for dummy number: {result['status'] if result else 'None'}")
    except Exception as e:
        print(f"FAILED: {e}")

    # 2. Mondial Relay
    print("\n[TEST] Mondial Relay Scraper")
    try:
        mr = MondialRelayScraper()
        # Requires zip code
        result = mr.get_tracking("12345678", "75000")
        print(f"Result for dummy number/zip: {result['status'] if result else 'None'}")
    except Exception as e:
        print(f"FAILED: {e}")

    # 3. Chronopost
    print("\n[TEST] Chronopost Scraper")
    try:
        chronopost = ChronopostScraper()
        result = chronopost.get_tracking("EE123456789FR")
        print(f"Result for dummy number: {result['status'] if result else 'None'}")
    except Exception as e:
        print(f"FAILED: {e}")

    # 4. DHL (Even if rejected, code should run)
    print("\n[TEST] DHL Connector")
    try:
        dhl = DHLConnector(api_key="TEST", api_secret="TEST")
        result = dhl.get_tracking("1234567890")
        print(f"Result for dummy number: {result['status'] if result else 'None'}")
    except Exception as e:
        print(f"FAILED: {e}")

    print("\n--- VERIFICATION COMPLETE ---")

if __name__ == "__main__":
    test_scrapers()
