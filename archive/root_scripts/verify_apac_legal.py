
import sys
import os

# Add root to path
sys.path.append(os.getcwd())

from src.reports.legal_document_generator import LegalDocumentGenerator

def verify_apac_templates():
    print("=== 🧪 VÉRIFICATION APAC LEGAL TEMPLATES ===")
    
    gen = LegalDocumentGenerator()
    
    # 1. Test Hong Kong (EN)
    print("\n--- 🇭🇰 Test Hong Kong (EN) ---")
    claim_hk = {
        'claim_reference': 'CLM-HK-999',
        'carrier': 'SF Express',
        'tracking_number': 'SF123456789',
        'amount_requested': 2500.00,
        'dispute_type': 'Package Lost',
        'customer_name': 'Asia Tech Ltd',
        'delivery_address': 'Flat A, 15/F, Mong Kok, Hong Kong',
        'currency': 'HKD'
    }
    path_hk = gen.generate_formal_notice(claim_hk, lang='EN')
    if os.path.exists(path_hk):
        print(f"✅ Document HK généré : {path_hk}")
    
    # 2. Test Singapore (EN)
    print("\n--- 🇸🇬 Test Singapore (EN) ---")
    claim_sg = {
        'claim_reference': 'CLM-SG-888',
        'carrier': 'NinjaVan',
        'tracking_number': 'NV554433',
        'amount_requested': 150.00,
        'dispute_type': 'Damaged Goods',
        'customer_name': 'Lion City Boutique',
        'delivery_address': '10 Marina Boulevard, Singapore',
        'currency': 'SGD'
    }
    path_sg = gen.generate_formal_notice(claim_sg, lang='EN')
    if os.path.exists(path_sg):
        print(f"✅ Document SG généré : {path_sg}")

    print("\n=== ✨ TOUTES LES VÉRIFICATIONS APAC SONT TERMINÉES ===")

if __name__ == "__main__":
    verify_apac_templates()
