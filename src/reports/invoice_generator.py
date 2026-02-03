
import pandas as pd
from datetime import datetime
from src.utils.i18n import format_currency

class InvoiceGenerator:
    """Génère des factures de commission certifiées pour les clients."""

    def generate_commission_invoice(self, client_data: dict, payments: list) -> str:
        """Génère une facture au format texte/CSV (simulant un PDF)."""
        invoice_ref = f"INV-{datetime.now().strftime('%Y%m')}-{client_data['id']}"
        
        report = []
        report.append(f"FACTURE DE COMMISSION - Refundly.ai")
        report.append(f"Référence: {invoice_ref}")
        report.append(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
        report.append("-" * 40)
        report.append(f"CLIENT: {client_data['full_name']}")
        report.append(f"EMAIL: {client_data['email']}")
        report.append("-" * 40)
        report.append(f"{'Dossier':<15} | {'Montant':>10} | {'Commission':>10}")
        
        total_comm = 0.0
        for p in payments:
            comm = p['platform_fee']
            total_comm += comm
            report.append(f"{p['claim_ref']:<15} | {p['total_amount']:>10.2f}€ | {comm:>10.2f}€")
            
        report.append("-" * 40)
        report.append(f"TOTAL TTC À PAYER: {total_comm:,.2f} €")
        report.append("-" * 40)
        report.append("Merci de votre confiance.")
        
        return "\n".join(report)
