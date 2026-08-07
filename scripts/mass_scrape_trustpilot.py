"""
Mass scraping script for collecting comprehensive Trustpilot data.

This script scrapes reviews from all 6 major carriers with a goal of 1000+ reviews
to extract robust real-world dispute patterns.
"""

import sys
sys.path.insert(0, 'src')

from scrapers.trustpilot_scraper import TrustpilotScraper
from scrapers.utils.text_processor import DisputePatternExtractor
import logging
import json
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Run comprehensive Trustpilot scraping."""
    print("="*70)
    print("🕷️  TRUSTPILOT MASS SCRAPING - COLLECTING REAL DISPUTE DATA")
    print("="*70)
    print("\nObjectif: 1000+ avis pour patterns robustes")
    print("Transporteurs: Colissimo, Chronopost, DPD, UPS, FedEx, DHL")
    print("\n⚠️  Rate limiting: 0.5 req/sec (respectueux)")
    print("\n" + "="*70 + "\n")
    
    # Initialize scraper with conservative rate limit
    scraper = TrustpilotScraper(rate_limit=0.5)
    
    # All carriers
    carriers = ['colissimo', 'chronopost', 'dpd', 'ups', 'fedex', 'dhl']
    
    # Scrape parameters
    max_pages_per_carrier = 10  # 10 pages * ~20 avis/page * 6 carriers = ~1200 avis
    min_rating = 3  # Only 1-3 star reviews (more likely to have disputes)
    
    all_reviews = []
    
    print("🚀 Démarrage du scraping...\n")
    
    for i, carrier in enumerate(carriers, 1):
        print(f"\n[{i}/6] 🚚 Scraping {carrier.upper()}...")
        print(f"  Target: {max_pages_per_carrier} pages (~{max_pages_per_carrier * 20} reviews)")
        
        try:
            carrier_reviews = scraper.scrape(
                carriers=[carrier],
                max_pages=max_pages_per_carrier,
                min_rating=min_rating
            )
            
            all_reviews.extend(carrier_reviews)
            
            print(f"  ✅ {len(carrier_reviews)} reviews collected")
            print(f"  📊 Total so far: {len(all_reviews)} reviews")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            continue
    
    print("\n" + "="*70)
    print(f"✅ SCRAPING TERMINÉ - {len(all_reviews)} REVIEWS COLLECTÉS")
    print("="*70)
    
    # Save consolidated data
    if all_reviews:
        output_file = Path('data/scraped/trustpilot_comprehensive.json')
        scraper.save_data(all_reviews, 'trustpilot_comprehensive.json')
        
        print(f"\n💾 Données sauvegardées: {output_file}")
        
        # Quick analysis
        processor = DisputePatternExtractor()
        
        delay_count = sum(1 for r in all_reviews if r.get('patterns', {}).get('has_delay'))
        loss_count = sum(1 for r in all_reviews if r.get('patterns', {}).get('has_loss'))
        damage_count = sum(1 for r in all_reviews if r.get('patterns', {}).get('has_damage'))
        
        print("\n📊 APERÇU RAPIDE:")
        print(f"  - Retards mentionnés: {delay_count} ({delay_count/len(all_reviews)*100:.1f}%)")
        print(f"  - Pertes mentionnées: {loss_count} ({loss_count/len(all_reviews)*100:.1f}%)")
        print(f"  - Dommages mentionnés: {damage_count} ({damage_count/len(all_reviews)*100:.1f}%)")
        
        print("\n🎯 Prochaine étape: Analyser avec analyze_trustpilot_data.py")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    import time
    start_time = time.time()
    
    main()
    
    elapsed = time.time() - start_time
    print(f"\n⏱️  Temps total: {elapsed/60:.1f} minutes")
    print("\n✅ Script terminé avec succès!\n")
