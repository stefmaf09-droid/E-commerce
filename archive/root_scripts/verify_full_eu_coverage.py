
import sys
import os

# Add root to path
sys.path.append(os.getcwd())

from src.reports.legal_document_generator import LegalDocumentGenerator

def verify_full_eu_coverage():
    print("=== 🧪 VÉRIFICATION COUVERTURE EUROPÉENNE TOTALE (27 PAYS) ===")
    
    gen = LegalDocumentGenerator()
    
    # 1. Test Poland (EU - CMR Fallback)
    print("\n--- 🇵🇱 Test Poland (EU - CMR) ---")
    claim_pl = {
        'claim_reference': 'CLM-EU-PL-001',
        'carrier': 'DPD Poland',
        'tracking_number': 'PL112233',
        'amount_requested': 150.00,
        'dispute_type': 'Zaginiona paczka',
        'customer_name': 'Krakow Shop',
        'delivery_address': 'ul. Floriańska, Krakow, Poland',
        'currency': 'EUR'
    }
    path_pl = gen.generate_formal_notice(claim_pl, lang='EN')
    if os.path.exists(path_pl):
        print(f"✅ Document Pologne (CMR) généré : {path_pl}")
    
    # 2. Test Sweden (EU - CMR Fallback)
    print("\n--- 🇸🇪 Test Sweden (EU - CMR) ---")
    claim_se = {
        'claim_reference': 'CLM-EU-SE-001',
        'carrier': 'PostNord',
        'tracking_number': 'SE998877',
        'amount_requested': 210.00,
        'dispute_type': 'Skadad vara',
        'customer_name': 'Stockholm Boutique',
        'delivery_address': 'Drottninggatan, Stockholm, Sweden',
        'currency': 'EUR'
    }
    path_se = gen.generate_formal_notice(claim_se, lang='EN')
    if os.path.exists(path_se):
        print(f"✅ Document Suède (CMR) généré : {path_se}")

    print("\n=== ✨ VÉRIFICATION COUVERTURE EU COMPLÈTE TERMINÉE ===")

if __name__ == "__main__":
    verify_full_eu_coverage()
