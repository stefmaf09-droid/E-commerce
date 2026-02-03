"""
Base scraper class.

Abstract class that all specific scrapers must inherit from.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
import logging
import json
from pathlib import Path
from datetime import datetime

from .utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract base class for web scrapers."""
    
    def __init__(
        self, 
        rate_limit: float = 1.0,
        output_dir: str = "data/scraped"
    ):
        """
        Initialize base scraper.
        
        Args:
            rate_limit: Requests per second
            output_dir: Directory to save scraped data
        """
        self.rate_limiter = RateLimiter(requests_per_second=rate_limit)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    @abstractmethod
    def scrape(self, **kwargs) -> List[Dict]:
        """
        Scrape data from the source.
        
        Returns:
            List of scraped items
        """
        pass
    
    def _fetch_page(self, url: str, timeout: int = 30) -> Optional[BeautifulSoup]:
        """
        Fetch and parse a web page.
        
        Args:
            url: URL to fetch
            timeout: Request timeout in seconds
            
        Returns:
            BeautifulSoup object or None if failed
        """
        try:
            with self.rate_limiter:
                logger.info(f"Fetching: {url}")
                response = self.session.get(url, timeout=timeout)
                response.raise_for_status()
                
                return BeautifulSoup(response.content, 'lxml')
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def save_data(self, data: List[Dict], filename: str):
        """
        Save scraped data to JSON file.
        
        Args:
            data: Data to save
            filename: Output filename (without path)
        """
        output_path = self.output_dir / filename
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'scraped_at': datetime.now().isoformat(),
                    'count': len(data),
                    'data': data
                }, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved {len(data)} items to {output_path}")
            
        except Exception as e:
            logger.error(f"Error saving data: {e}")
    
    def load_data(self, filename: str) -> Optional[List[Dict]]:
        """
        Load previously scraped data.
        
        Args:
            filename: Input filename (without path)
            
        Returns:
            List of items or None if not found
        """
        input_path = self.output_dir / filename
        
        if not input_path.exists():
            logger.warning(f"File not found: {input_path}")
            return None
        
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
                return content.get('data', [])
                
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return None
