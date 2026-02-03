"""
Scrapers package for collecting real-world dispute data.
"""

from .base_scraper import BaseScraper
from .trustpilot_scraper import TrustpilotScraper

__all__ = ['BaseScraper', 'TrustpilotScraper']
