
from typing import Dict

class CurrencyService:
    """Service de conversion multi-devises en temps réel (simulé)."""
    
    # Taux de change spots (base EUR) - Update simulé via API en prod
    RATES = {
        'EUR': 1.0,
        'USD': 1.08,
        'GBP': 0.85,
        'HKD': 8.45,
        'SGD': 1.45,
        'AUD': 1.65,
        'CAD': 1.48
    }

    def convert_to_eur(self, amount: float, from_currency: str) -> float:
        """Convertit n'importe quelle devise en EUR."""
        rate = self.RATES.get(from_currency.upper(), 1.0)
        return round(amount / rate, 2)

    def convert_from_eur(self, amount_eur: float, to_currency: str) -> float:
        """Convertit de l'EUR vers une devise étrangère."""
        rate = self.RATES.get(to_currency.upper(), 1.0)
        return round(amount_eur * rate, 2)

    def get_display_price(self, amount_eur: float, target_currency: str) -> str:
        """Retourne le prix formaté dans la devise cible."""
        converted = self.convert_from_eur(amount_eur, target_currency)
        from src.utils.i18n import format_currency
        return format_currency(converted, target_currency)
