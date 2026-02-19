"""
Scrapers package for collecting real-world dispute data.
"""

from .base_scraper import BaseScraper
from .trustpilot_scraper import TrustpilotScraper
from .colissimo_scraper import ColissimoScraper
from .chronopost_scraper import ChronopostScraper
from .mondial_relay_scraper import MondialRelayScraper
from .fedex_scraper import FedExScraper
from .dpd_scraper import DPDScraper
from .gls_scraper import GLSScraper
from .tnt_scraper import TNTScraper

__all__ = [
    'BaseScraper',
    'TrustpilotScraper',
    'ColissimoScraper',
    'ChronopostScraper',
    'MondialRelayScraper',
    'FedExScraper',
    'DPDScraper',
    'GLSScraper',
    'TNTScraper',
]
