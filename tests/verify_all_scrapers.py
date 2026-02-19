"""
Test complet de tous les scrapers : Colissimo, Mondial Relay, Chronopost, DHL,
FedEx, DPD, GLS, TNT.
"""
import logging
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

logging.basicConfig(level=logging.WARNING, format='%(name)s - %(levelname)s - %(message)s')

RESULTS = []

def test(name, fn):
    print(f"\n[TEST] {name}")
    try:
        result = fn()
        status = result.get('status', '?') if isinstance(result, dict) else str(result)
        print(f"  ✅ OK — status: {status}")
        RESULTS.append((name, True, status))
    except Exception as e:
        print(f"  ❌ FAILED — {e}")
        RESULTS.append((name, False, str(e)))

print("=" * 55)
print("VÉRIFICATION DE TOUS LES SCRAPERS")
print("=" * 55)

# --- Scrapers existants ---
from src.scrapers.colissimo_scraper import ColissimoScraper
from src.scrapers.mondial_relay_scraper import MondialRelayScraper
from src.scrapers.chronopost_scraper import ChronopostScraper
from src.connectors.dhl_connector import DHLConnector

test("Colissimo", lambda: ColissimoScraper().get_pod("6A12345678901"))
test("Mondial Relay", lambda: MondialRelayScraper().get_tracking("12345678", "75000"))
test("Chronopost", lambda: ChronopostScraper().get_tracking("EE123456789FR"))
test("DHL", lambda: DHLConnector(api_key="TEST", api_secret="TEST").get_tracking("1234567890"))

# --- Nouveaux scrapers ---
from src.scrapers.fedex_scraper import FedExScraper
from src.scrapers.dpd_scraper import DPDScraper
from src.scrapers.gls_scraper import GLSScraper
from src.scrapers.tnt_scraper import TNTScraper

test("FedEx", lambda: FedExScraper().get_tracking("794644774000"))
test("DPD", lambda: DPDScraper().get_tracking("05220690201234"))
test("GLS", lambda: GLSScraper().get_tracking("55357711485"))
test("TNT", lambda: TNTScraper().get_tracking("GE461375640GB"))

# --- Résumé ---
print("\n" + "=" * 55)
print("RÉSUMÉ")
print("=" * 55)
ok = sum(1 for _, s, _ in RESULTS if s)
total = len(RESULTS)
for name, success, detail in RESULTS:
    icon = "✅" if success else "❌"
    print(f"  {icon} {name:<20} {detail[:40]}")
print(f"\n  {ok}/{total} scrapers opérationnels")
