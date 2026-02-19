"""
Tests for POD Scrapers.
"""

import unittest
from unittest.mock import MagicMock
import requests
from src.scrapers.colissimo_scraper import ColissimoScraper

class TestColissimoScraper(unittest.TestCase):
    
    def setUp(self):
        self.scraper = ColissimoScraper()
        # Directly mock the session object on the instance
        self.scraper.session = MagicMock()
        
    def test_get_pod_delivered(self):
        # Mock HTML response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"""
        <html>
            <body>
                <h2 class="status">Votre colis est livr\xc3\xa9</h2>
                <p class="date">le 18/02/2026</p>
                <div class="timeline-item">
                    <span class="time">10:00</span>
                    <span class="label">Livr\xc3\xa9</span>
                </div>
            </body>
        </html>
        """
        # Configure the mock session to return our mock response
        self.scraper.session.get.return_value = mock_response
        
        result = self.scraper.get_pod("6A123456")
        
        self.assertIsNotNone(result)
        self.assertEqual(result['status'], "Votre colis est livré")
        self.assertTrue(result['is_delivered'])
        self.assertEqual(result['delivery_date'], "le 18/02/2026")
        
    def test_get_pod_not_found(self):
        # Mock 404 behavior
        mock_response = MagicMock()
        mock_response.status_code = 404
        # Configure the mock to raise HTTPError when raise_for_status is called
        # We use a real HTTPError for realism
        error = requests.exceptions.HTTPError("404 Client Error")
        mock_response.raise_for_status.side_effect = error
        
        self.scraper.session.get.return_value = mock_response
        
        result = self.scraper.get_pod("UNKNOWN")
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
