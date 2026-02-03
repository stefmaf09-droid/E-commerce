"""
Payment Processing Module - Stripe Connect Integration.

Handles automatic payment splitting for marketplace model.
"""

import os
import stripe
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Configuration Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY', '')
STRIPE_MODE = os.getenv('STRIPE_MODE', 'test')
PLATFORM_COMMISSION_RATE = float(os.getenv('PLATFORM_COMMISSION_RATE', '0.20'))  # 20%


class PaymentProcessor:
    """Handle payments via Stripe Connect."""
    
    def __init__(self):
        """Initialize payment processor."""
        self.commission_rate = PLATFORM_COMMISSION_RATE
        
        if not stripe.api_key:
            logger.warning("⚠️ STRIPE_SECRET_KEY non configuré. Les paiements ne fonctionneront pas.")
    
    def create_connected_account(
        self, 
        client_email: str,
        client_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a Stripe Connect account for a client.
        
        Args:
            client_email: Client email address
            client_data: Optional additional client data
            
        Returns:
            Dictionary with account info and onboarding URL
        """
        if not stripe.api_key:
            return {'success': False, 'error': 'Stripe not configured'}
        
        try:
            # Create Express Connect account
            account = stripe.Account.create(
                type='express',
                country='FR',
                email=client_email,
                capabilities={
                    'transfers': {'requested': True},
                },
                business_type='individual',  # ou 'company' si entreprises
            )
            
            # Create account link for onboarding
            account_link = stripe.AccountLink.create(
                account=account.id,
                refresh_url=f'{os.getenv("BASE_URL", "http://localhost:8501")}/reauth',
                return_url=f'{os.getenv("BASE_URL", "http://localhost:8501")}/dashboard',
                type='account_onboarding',
            )
            
            logger.info(f"✅ Stripe account created for {client_email}: {account.id}")
            
            return {
                'success': True,
                'account_id': account.id,
                'onboarding_url': account_link.url,
                'client_email': client_email
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"❌ Stripe account creation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def check_account_status(self, account_id: str) -> Dict[str, Any]:
        """
        Check if a connected account is ready to receive payments.
        
        Args:
            account_id: Stripe connected account ID
            
        Returns:
            Account status information
        """
        try:
            account = stripe.Account.retrieve(account_id)
            
            # Check if charges and payouts are enabled
            charges_enabled = account.charges_enabled
            payouts_enabled = account.payouts_enabled
            
            return {
                'account_id': account_id,
                'charges_enabled': charges_enabled,
                'payouts_enabled': payouts_enabled,
                'ready': charges_enabled and payouts_enabled,
                'details_submitted': account.details_submitted,
                'email': account.email
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"❌ Failed to check account status: {e}")
            return {
                'account_id': account_id,
                'ready': False,
                'error': str(e)
            }
    
    def process_recovery_payment(
        self,
        amount: float,
        client_stripe_account_id: str,
        claim_reference: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process payment from recovered amount to client.
        
        This simulates receiving money from carrier and transferring to client.
        In reality, you'd first receive the money, then transfer.
        
        Args:
            amount: Total amount recovered (e.g., 100€)
            client_stripe_account_id: Client's Stripe Connect account ID
            claim_reference: Claim reference for tracking
            description: Optional description
            
        Returns:
            Transfer result
        """
        if not stripe.api_key:
            return {'success': False, 'error': 'Stripe not configured'}
        
        try:
            # Calculate amounts
            total_amount = amount
            client_share = total_amount * (1 - self.commission_rate)  # 80%
            platform_fee = total_amount * self.commission_rate  # 20%
            
            # Convert to cents (Stripe uses cents)
            client_amount_cents = int(client_share * 100)
            
            # Create transfer to client
            transfer = stripe.Transfer.create(
                amount=client_amount_cents,
                currency='eur',
                destination=client_stripe_account_id,
                description=description or f"Réclamation {claim_reference}",
                metadata={
                    'claim_reference': claim_reference,
                    'total_amount': str(total_amount),
                    'client_share': str(client_share),
                    'platform_fee': str(platform_fee)
                }
            )
            
            logger.info(f"✅ Transfer created: {transfer.id} - {client_share}€ to client")
            
            return {
                'success': True,
                'transfer_id': transfer.id,
                'total_amount': total_amount,
                'client_received': client_share,
                'platform_fee': platform_fee,
                'client_account': client_stripe_account_id,
                'claim_reference': claim_reference,
                'created_at': datetime.fromtimestamp(transfer.created).isoformat()
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"❌ Transfer failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_account_balance(self, account_id: str) -> Dict[str, Any]:
        """
        Get balance for a connected account.
        
        Args:
            account_id: Stripe connected account ID
            
        Returns:
            Balance information
        """
        try:
            balance = stripe.Balance.retrieve(
                stripe_account=account_id
            )
            
            # Available balance (can be withdrawn)
            available = balance.available[0] if balance.available else {'amount': 0}
            
            # Pending balance (in transit)
            pending = balance.pending[0] if balance.pending else {'amount': 0}
            
            return {
                'account_id': account_id,
                'available': available['amount'] / 100,  # Convert cents to euros
                'pending': pending['amount'] / 100,
                'currency': available.get('currency', 'eur')
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"❌ Failed to get balance: {e}")
            return {
                'account_id': account_id,
                'available': 0,
                'pending': 0,
                'error': str(e)
            }
    
    def create_payout(self, account_id: str, amount: float) -> Dict[str, Any]:
        """
        Create manual payout to connected account's bank.
        
        Args:
            account_id: Stripe connected account ID
            amount: Amount to payout
            
        Returns:
            Payout result
        """
        try:
            amount_cents = int(amount * 100)
            
            payout = stripe.Payout.create(
                amount=amount_cents,
                currency='eur',
                stripe_account=account_id
            )
            
            logger.info(f"✅ Payout created: {payout.id} - {amount}€")
            
            return {
                'success': True,
                'payout_id': payout.id,
                'amount': amount,
                'status': payout.status,
                'arrival_date': datetime.fromtimestamp(payout.arrival_date).strftime('%Y-%m-%d')
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"❌ Payout failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Convenience functions
def create_client_account(client_email: str) -> Dict[str, Any]:
    """Create Stripe Connect account for client."""
    processor = PaymentProcessor()
    return processor.create_connected_account(client_email)


def pay_client(
    amount: float,
    client_stripe_id: str,
    claim_reference: str
) -> Dict[str, Any]:
    """Process payment to client from recovered amount."""
    processor = PaymentProcessor()
    return processor.process_recovery_payment(
        amount=amount,
        client_stripe_account_id=client_stripe_id,
        claim_reference=claim_reference
    )


if __name__ == "__main__":
    # Test payment processor
    print("="*70)
    print("PAYMENT PROCESSOR - Test")
    print("="*70)
    
    processor = PaymentProcessor()
    
    print(f"\n💳 Configuration:")
    print(f"  Stripe API Key: {'✅ Configured' if stripe.api_key else '❌ Not configured'}")
    print(f"  Mode: {STRIPE_MODE}")
    print(f"  Commission Rate: {processor.commission_rate * 100}%")
    
    if not stripe.api_key:
        print("\n⚠️  Pour tester, configurez la variable d'environnement:")
        print("  export STRIPE_SECRET_KEY='sk_test_xxxxx'")
        print("\n💡 Obtenez votre clé sur:")
        print("  https://dashboard.stripe.com/test/apikeys")
    else:
        print("\n✅ Configuration OK")
        
        # Exemple de calcul
        print("\n💰 Exemple de calcul:")
        print(f"  Réclamation acceptée: 100.00€")
        print(f"  Commission plateforme ({processor.commission_rate*100}%): 20.00€")
        print(f"  Part client ({(1-processor.commission_rate)*100}%): 80.00€")
        print(f"  Frais Stripe (~1.65€): -1.65€")
        print(f"  NET pour vous: ~18.35€")
    
    print("\n" + "="*70)
    print("✅ Test Complete")
    print("="*70)
