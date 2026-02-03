import os
import stripe
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class StripeManager:
    """Gestionnaire des opérations Stripe Connect."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with API key from env or argument."""
        self.api_key = api_key or os.getenv("STRIPE_SECRET_KEY")
        if self.api_key:
            stripe.api_key = self.api_key
        
        self.client_id = os.getenv("STRIPE_CLIENT_ID")
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    def create_connect_account(self, email: str, country: str = "FR") -> str:
        """
        Crée un compte connecté Stripe (Express).
        Supporte désormais les pays APAC (HK, SG) et occidentaux.
        """
        try:
            account = stripe.Account.create(
                type="express",
                country=country,
                email=email,
                capabilities={
                    "transfers": {"requested": True},
                },
                settings={
                    "payouts": {
                        "schedule": {"interval": "manual"}
                    }
                }
            )
            logger.info(f"Stripe Connect account created for {email}: {account.id}")
            return account.id
        except Exception as e:
            logger.error(f"Error creating Stripe account: {e}")
            raise

    def generate_onboarding_link(self, account_id: str, refresh_url: str, return_url: str) -> str:
        """Génère un lien d'onboarding pour le compte connecté."""
        try:
            account_link = stripe.AccountLink.create(
                account=account_id,
                refresh_url=refresh_url,
                return_url=return_url,
                type="account_onboarding",
            )
            return account_link.url
        except Exception as e:
            logger.error(f"Error generating onboarding link: {e}")
            raise

    from src.utils.resilience import CircuitBreaker
    
    @CircuitBreaker(failure_threshold=3, recovery_timeout=60)
    def create_payout_transfer(self, destination_account_id: str, amount: float, 
                               client_commission_rate: float = 20.0,
                               currency: str = "eur", claim_ref: str = "") -> str:
        """
        Transfère les fonds vers le compte connecté du marchand.
        La part du marchand est (100 - commission_rate)%.
        """
        try:
            # Calcul de la part marchand (ex: 80% si commission=20%)
            merchant_share_percent = (100.0 - client_commission_rate) / 100.0
            amount_cents = int(amount * merchant_share_percent * 100)
            
            transfer = stripe.Transfer.create(
                amount=amount_cents,
                currency=currency,
                destination=destination_account_id,
                description=f"Reversement litige {claim_ref} ({100-client_commission_rate:.0f}%)",
                metadata={"claim_reference": claim_ref}
            )
            logger.info(f"Transfer successful: {transfer.id}")
            return transfer.id
        except Exception as e:
            logger.error(f"Error during transfer: {e}")
            raise

    def get_account_status(self, account_id: str) -> Dict[str, Any]:
        """Récupère le statut d'onboarding et les capacités du compte."""
        try:
            account = stripe.Account.retrieve(account_id)
            return {
                "details_submitted": account.details_submitted,
                "charges_enabled": account.charges_enabled,
                "payouts_enabled": account.payouts_enabled,
                "requirements": account.requirements.currently_due
            }
        except Exception as e:
            logger.error(f"Error retrieving account status: {e}")
            raise
