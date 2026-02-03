import pytest
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
from bs4 import BeautifulSoup
import requests
from src.scrapers.base_scraper import BaseScraper
from src.scrapers.trustpilot_scraper import TrustpilotScraper

# Concrete implementation for testing BaseScraper
class ConcreteScraper(BaseScraper):
    def scrape(self, **kwargs):
        return [{'id': 1, 'data': 'test'}]

class TestBaseScraper:
    def test_init(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            scraper = ConcreteScraper(output_dir=tmpdir)
            assert scraper.output_dir == Path(tmpdir)
            assert os.path.exists(tmpdir)
            assert 'User-Agent' in scraper.session.headers

    @patch('requests.Session.get')
    def test_fetch_page_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"<html><body><h1>Test</h1></body></html>"
        mock_get.return_value = mock_response
        
        scraper = ConcreteScraper()
        soup = scraper._fetch_page("http://example.com")
        assert soup is not None
        assert soup.find('h1').text == "Test"

    @patch('requests.Session.get')
    def test_fetch_page_failure(self, mock_get):
        mock_get.side_effect = requests.exceptions.RequestException("Error")
        scraper = ConcreteScraper()
        soup = scraper._fetch_page("http://example.com")
        assert soup is None

    def test_save_load_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            scraper = ConcreteScraper(output_dir=tmpdir)
            data = [{'a': 1}, {'b': 2}]
            filename = "test_data.json"
            
            scraper.save_data(data, filename)
            loaded = scraper.load_data(filename)
            
            assert len(loaded) == 2
            assert loaded[0]['a'] == 1
            
            # Test loading non-existent file
            assert scraper.load_data("missing.json") is None

class TestTrustpilotScraper:
    @pytest.fixture
    def scraper(self):
        return TrustpilotScraper()

    def test_scrape_calls_subfunctions(self, scraper):
        with patch.object(scraper, '_scrape_carrier', return_value=[{'id': 1}]) as mock_scrape:
            results = scraper.scrape(carriers=['colissimo'])
            assert len(results) == 1
            mock_scrape.assert_called_once()

    def test_extract_reviews_from_page(self, scraper):
        html = """
        <article class="review-card">
            <div class="star-rating" data-service-review-rating="1"></div>
            <h2 class="review-title">Mauvais service</h2>
            <p class="review-content">Colis en retard de 3 jours et abîmé</p>
            <time datetime="2026-01-20T10:00:00Z"></time>
            <span class="user-name">Jean D.</span>
        </article>
        """
        soup = BeautifulSoup(html, 'lxml')
        reviews = scraper._extract_reviews_from_page(soup, 'colissimo', min_rating=5)
        
        assert len(reviews) == 1
        assert reviews[0]['rating'] == 1
        assert reviews[0]['patterns']['has_delay'] is True
        assert reviews[0]['author_initials'] == 'Je'

    @patch.object(TrustpilotScraper, '_fetch_page')
    @patch('time.sleep')
    def test_scrape_carrier_pagination(self, mock_sleep, mock_fetch, scraper):
        mock_fetch.side_effect = [
            BeautifulSoup('<article class="review"><div class="star"></div><p class="content">Test</p></article>', 'lxml'),
            BeautifulSoup('<article class="review"><div class="star"></div><p class="content">Test</p></article>', 'lxml'),
            None
        ]
        
        with patch.object(scraper, '_extract_reviews_from_page', return_value=[{'id': 1}]):
            reviews = scraper._scrape_carrier('colissimo', 'http://url', max_pages=3, min_rating=5)
            assert len(reviews) == 2
            assert mock_fetch.call_count == 3  # Page 1, Page 2, Page 3 (None)
