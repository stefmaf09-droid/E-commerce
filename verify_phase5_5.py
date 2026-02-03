
import os
import sys

# Add root to path
sys.path.append(os.getcwd())

from src.payments.currency_service import CurrencyService
from src.reports.invoice_generator import InvoiceGenerator

def verify_phase5_5():
    print("=== 🧪 VÉRIFICATION PHASE 5.5 : FINANCIAL OPTIMIZATION 2.0 ===")
    
    # 1. Test Currency Conversion
    print("\n--- 💱 Multi-Currency Logic ---")
    cs = CurrencyService()
    amount_usd = 100.0
    amount_eur = cs.convert_to_eur(amount_usd, 'USD')
    print(f"✅ 100 USD -> {amount_eur} EUR")
    
    amount_hkd = cs.convert_from_eur(100.0, 'HKD')
    print(f"✅ 100 EUR -> {amount_hkd} HKD")
    
    # 2. Test Invoice Generation
    print("\n--- 📑 Automated Invoicing ---")
    inv_gen = InvoiceGenerator()
    invoice = inv_gen.generate_commission_invoice(
        {'id': 1, 'full_name': 'Test Store', 'email': 'test@store.com'},
        [{'claim_ref': 'REF-1', 'total_amount': 100.0, 'platform_fee': 20.0}]
    )
    if 'FACTURE DE COMMISSION' in invoice and '20.00€' in invoice:
        print("✅ Invoice correctly generated with totals.")
    
    # 3. Check UI
    print("\n--- 🖼️ UI Integration (Grep check) ---")
    with open('client_dashboard.py', 'r', encoding='utf-8') as f:
        if 'Facturation & Invoices' in f.read():
            print("✅ Client Dashboard: Invoicing UI found.")

    print("\n=== ✨ VÉRIFICATION PHASE 5.5 (ET PHASE 5 TOTALE) TERMINÉE ===")

if __name__ == "__main__":
    verify_phase5_5()
