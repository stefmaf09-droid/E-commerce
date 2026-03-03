"""
Test des scrapers transporteurs: Colissimo, Chronopost, DPD, GLS.
Teste la connectivite réseau et la structure de réponse.
"""
import sys, logging
sys.path.insert(0, '.')
logging.basicConfig(level=logging.WARNING)

def test_carrier(name, func, tracking):
    print(f"\n{'='*55}")
    print(f"  {name} — {tracking}")
    print('='*55)
    try:
        result = func(tracking)
        if result:
            print(f"  ✅ Réponse reçue:")
            for k, v in result.items():
                if k == 'history':
                    print(f"     history: {len(v)} événements")
                elif k != 'scraped_at':
                    print(f"     {k}: {v}")
        else:
            print(f"  ⚠️  None retourné (tracking inconnu ou page vide)")
    except Exception as e:
        print(f"  ❌ Exception: {type(e).__name__}: {e}")

# ---- Colissimo ----
try:
    from src.scrapers.colissimo_scraper import ColissimoScraper
    s = ColissimoScraper()
    test_carrier("Colissimo / La Poste", s.get_pod, "6X12345678900")
except Exception as e:
    print(f"\n❌ Import Colissimo: {e}")

# ---- Chronopost ----
try:
    from src.scrapers.chronopost_scraper import ChronopostScraper
    s = ChronopostScraper()
    test_carrier("Chronopost", s.get_tracking, "XB123456789FR")
except Exception as e:
    print(f"\n❌ Import Chronopost: {e}")

# ---- DPD ----
try:
    from src.scrapers.dpd_scraper import DPDScraper
    s = DPDScraper()
    test_carrier("DPD France (JSON API)", s.get_tracking, "05281697898661")
except Exception as e:
    print(f"\n❌ Import DPD: {e}")

# ---- GLS ----
try:
    from src.scrapers.gls_scraper import GLSScraper
    s = GLSScraper()
    test_carrier("GLS (API REST publique)", s.get_tracking, "426578545280")
except Exception as e:
    print(f"\n❌ Import GLS: {e}")

print("\n\n=== FIN DES TESTS ===")
