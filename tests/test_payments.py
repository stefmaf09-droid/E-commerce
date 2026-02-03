import pytest
import stripe
from unittest.mock import MagicMock, patch
from src.payments.payment_processor import PaymentProcessor

class TestPaymentProcessor:
    
    @pytest.fixture
    def processor(self):
        return PaymentProcessor()
    
    @patch('stripe.Account.create')
    @patch('stripe.AccountLink.create')
    def test_create_connected_account(self, mock_link, mock_account, processor):
        # Mock Stripe responses
        mock_account.return_value = MagicMock(id='acct_123')
        mock_link.return_value = MagicMock(url='https://stripe.com/onboard/123')
        
        # Test with mock key to ensure it doesn't return early due to missing key
        with patch('stripe.api_key', 'sk_test_mock'):
            result = processor.create_connected_account('client@test.com')
        
        assert result['success'] is True
        assert result['account_id'] == 'acct_123'
        assert result['onboarding_url'] == 'https://stripe.com/onboard/123'

    def test_commission_calculation(self, processor):
        # Base commission is 20%
        amount = 100.0
        client_share = amount * (1 - processor.commission_rate)
        platform_fee = amount * processor.commission_rate
        
        assert client_share == 80.0
        assert platform_fee == 20.0

    @patch('stripe.Transfer.create')
    def test_process_recovery_payment(self, mock_transfer, processor):
        # Mock transfer response
        mock_transfer.return_value = MagicMock(
            id='tr_123',
            created=1643110000
        )
        
        with patch('stripe.api_key', 'sk_test_mock'):
            result = processor.process_recovery_payment(
                amount=100.0,
                client_stripe_account_id='acct_client',
                claim_reference='CLM-456'
            )
            
        assert result['success'] is True
        assert result['client_received'] == 80.0
        assert result['platform_fee'] == 20.0
        assert result['transfer_id'] == 'tr_123'
        
        # Verify Stripe was called with correct cents
        mock_transfer.assert_called_once()
        args, kwargs = mock_transfer.call_args
        assert kwargs['amount'] == 8000 # 80.00 euros in cents
        assert kwargs['destination'] == 'acct_client'

    @patch('stripe.Balance.retrieve')
    def test_get_account_balance(self, mock_balance, processor):
        # Mock balance response
        mock_balance.return_value = MagicMock(
            available=[{'amount': 5000, 'currency': 'eur'}],
            pending=[{'amount': 12000, 'currency': 'eur'}]
        )
        
        result = processor.get_account_balance('acct_123')
        
        assert result['available'] == 50.0
        assert result['pending'] == 120.0
        assert result['currency'] == 'eur'
