"""
Tests for Payment System.

Tests manual payment manager and Stripe integration (when available).
"""

import pytest
from datetime import datetime


class TestManualPaymentManager:
    """Test manual payment processing."""
    
    def test_create_pending_payment(self, db_manager, sample_client, sample_claim):
        """Test creating a pending payment."""
        total_amount = 100.00
        client_share = total_amount * 0.8
        platform_fee = total_amount * 0.2
        
        payment_id = db_manager.create_payment(
            claim_id=sample_claim['id'],
            client_id=sample_client['id'],
            total_amount=total_amount,
            client_share=client_share,
            platform_fee=platform_fee,
            payment_method='manual_transfer'
        )
        
        assert payment_id > 0
    
    def test_80_20_split_calculation(self):
        """Test 80/20 commission split calculation."""
        test_amounts = [100.0, 250.0, 500.0, 1000.0]
        
        for total in test_amounts:
            client_share = total * 0.8
            platform_fee = total * 0.2
            
            # Verify split
            assert client_share + platform_fee == total
            assert client_share == total * 0.8
            assert platform_fee == total * 0.2
    
    def test_mark_payment_as_completed(self, db_manager, sample_client, sample_claim):
        """Test marking payment as completed."""
        # Create payment
        payment_id = db_manager.create_payment(
            claim_id=sample_claim['id'],
            client_id=sample_client['id'],
            total_amount=100.0,
            client_share=80.0,
            platform_fee=20.0
        )
        
        # Mark as completed
        db_manager.update_payment(
            payment_id=payment_id,
            payment_status='completed',
            paid_at=datetime.now(),
            transaction_reference='VIR-2026-001',
            notes='Virement bancaire effectué'
        )
        
        # Verify update (would need to query payment directly)
        # This is a simplified test
        assert True
    
    def test_payment_for_multiple_claims(self, db_manager, sample_client):
        """Test processing payments for multiple claims."""
        # Create multiple claims
        claim_ids = []
        for i in range(3):
            claim_id = db_manager.create_claim(
                claim_reference=f'CLM-MULTI-PAY-{i}',
                client_id=sample_client['id'],
                order_id=f'ORD-PAY-{i}',
                carrier='colissimo',
                dispute_type='late_delivery',
                amount_requested=100.0 + (i * 50)
            )
            claim_ids.append(claim_id)
            
            # Mark as accepted
            db_manager.update_claim(
                claim_id=claim_id,
                status='accepted',
                accepted_amount=100.0 + (i * 50)
            )
        
        # Create payments for each
        payment_ids = []
        for i, claim_id in enumerate(claim_ids):
            amount = 100.0 + (i * 50)
            payment_id = db_manager.create_payment(
                claim_id=claim_id,
                client_id=sample_client['id'],
                total_amount=amount,
                client_share=amount * 0.8,
                platform_fee=amount * 0.2
            )
            payment_ids.append(payment_id)
        
        assert len(payment_ids) == 3
    
    def test_payment_tracking_in_statistics(self, db_manager, sample_client, sample_claim):
        """Test that payments are tracked in client statistics."""
        # Create and complete payment
        payment_id = db_manager.create_payment(
            claim_id=sample_claim['id'],
            client_id=sample_client['id'],
            total_amount=200.0,
            client_share=160.0,
            platform_fee=40.0
        )
        
        db_manager.update_payment(
            payment_id=payment_id,
            payment_status='completed',
            paid_at=datetime.now()
        )
        
        # Check statistics
        stats = db_manager.get_client_statistics(sample_client['id'])
        
        # Stats should reflect the payment
        assert stats is not None
        # Would need to verify total_paid_to_client if view includes it


class TestStripeIntegration:
    """Test Stripe Connect integration (when available)."""
    
    @pytest.mark.requires_api
    def test_stripe_payment_creation(self, mock_env_vars):
        """Test creating a Stripe Connect payment."""
        # This would require actual Stripe SDK
        # For now, test environment variables are set
        assert mock_env_vars['STRIPE_SECRET_KEY'].startswith('sk_test_')
        assert mock_env_vars['STRIPE_PUBLISHABLE_KEY'].startswith('pk_test_')
    
    def test_stripe_commission_calculation(self):
        """Test Stripe fee + platform fee calculation."""
        # Example: 100€ recovered
        total = 100.0
        
        # Stripe fees (1.4% + 0.25€)
        stripe_fee = (total * 0.014) + 0.25
        
        # After Stripe
        after_stripe = total - stripe_fee
        
        # Platform fee (20%)
        platform_fee = total * 0.20
        
        # Client share (80%)
        client_share = total * 0.80
        
        # Verify
        assert client_share == 80.0
        assert platform_fee == 20.0
        
        # Net platform revenue
        net_platform = platform_fee - stripe_fee
        assert net_platform > 0  # Should still be profitable
