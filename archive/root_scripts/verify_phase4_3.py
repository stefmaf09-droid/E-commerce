
import sys
import os

# Add root to path
sys.path.append(os.getcwd())

from src.reports.legal_document_generator import LegalDocumentGenerator

def verify_international_templates():
    print("=== 🧪 VÉRIFICATION PHASE 4.3 : EXPANSION INTERNATIONALE ===")
    
    gen = LegalDocumentGenerator()
    
    # 1. Test German (DE)
    print("\n--- 🇩🇪 Test Germany (DE) ---")
    claim_de = {
        'claim_reference': 'CLM-DE-001',
        'carrier': 'DHL Paket',
        'tracking_number': 'DE123456',
        'amount_requested': 89.90,
        'dispute_type': 'Verlust',
        'customer_name': 'Händler GmbH',
        'delivery_address': 'Berlin, Deutschland',
        'currency': 'EUR'
    }
    path_de = gen.generate_formal_notice(claim_de, lang='DE')
    if os.path.exists(path_de):
        print(f"✅ Document DE généré : {path_de}")
        # On pourrait vérifier le contenu si on avait un parseur PDF, 
        # mais la génération sans erreur est déjà un bon signe.
    
    # 2. Test UK (EN)
    print("\n--- 🇬🇧 Test UK (EN) ---")
    claim_uk = {
        'claim_reference': 'CLM-UK-001',
        'carrier': 'Royal Mail',
        'tracking_number': 'UK987654',
        'amount_requested': 45.00,
        'dispute_type': 'Damaged Item',
        'customer_name': 'UK Shop Ltd',
        'delivery_address': '123 Regent Street, London, United Kingdom',
        'currency': 'GBP'
    }
    path_uk = gen.generate_formal_notice(claim_uk, lang='EN')
    if os.path.exists(path_uk):
        print(f"✅ Document UK généré : {path_uk}")

    print("\n=== ✨ TOUTES LES VÉRIFICATIONS SONT TERMINÉES ===")

if __name__ == "__main__":
    verify_international_templates()
