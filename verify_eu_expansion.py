
import sys
import os

# Add root to path
sys.path.append(os.getcwd())

from src.reports.legal_document_generator import LegalDocumentGenerator

def verify_eu_expansion():
    print("=== 🧪 VÉRIFICATION EXPANSION EUROPE (IT & ES) ===")
    
    gen = LegalDocumentGenerator()
    
    # 1. Test Italy (IT)
    print("\n--- 🇮🇹 Test Italy (IT) ---")
    claim_it = {
        'claim_reference': 'CLM-IT-001',
        'carrier': 'Poste Italiane',
        'tracking_number': 'IT123456',
        'amount_requested': 120.00,
        'dispute_type': 'Pacco Smarrito',
        'customer_name': 'Negozio Milano',
        'delivery_address': 'Via Roma, Milano, Italia',
        'currency': 'EUR'
    }
    path_it = gen.generate_formal_notice(claim_it, lang='IT')
    if os.path.exists(path_it):
        print(f"✅ Document IT généré : {path_it}")
    
    # 2. Test Spain (ES)
    print("\n--- 🇪🇸 Test Spain (ES) ---")
    claim_es = {
        'claim_reference': 'CLM-ES-001',
        'carrier': 'Correos',
        'tracking_number': 'ES987654',
        'amount_requested': 75.50,
        'dispute_type': 'Paquete Dañado',
        'customer_name': 'Tienda Madrid',
        'delivery_address': 'Calle Mayor, Madrid, España',
        'currency': 'EUR'
    }
    path_es = gen.generate_formal_notice(claim_es, lang='ES')
    if os.path.exists(path_es):
        print(f"✅ Document ES généré : {path_es}")

    print("\n=== ✨ TOUTES LES VÉRIFICATIONS EUROPE SONT TERMINÉES ===")

if __name__ == "__main__":
    verify_eu_expansion()
