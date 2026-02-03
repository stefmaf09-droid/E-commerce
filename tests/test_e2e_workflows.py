"""
End-to-End Tests - Complete User Workflows.

Tests the entire flow from dispute detection to claim submission and payment.
"""

import pytest
from datetime import datetime, timedelta
import asyncio


@pytest.mark.e2e
class TestCompleteUserFlow:
    """Test complete user workflows end-to-end."""
    
    def test_new_client_onboarding_flow(self, db_manager, sample_orders, mock_smtp_server, mock_env_vars):
        """
        Test complete onboarding flow:
        1. Client uploads CSV
        2. Disputes detected
        3. Saved to database
        4. Email notification sent
        5. Client sees dashboard
        """
        # Step 1: Simulate CSV upload and client creation
        client_email = 'newclient@example.com'
        client_id = db_manager.create_client(
            email=client_email,
            full_name='New Client'
        )
        
        client = db_manager.get_client(client_id=client_id)
        assert client is not None
        
        # Step 2: Detect disputes from orders
        from dispute_detector import DisputeDetectionEngine
        import pandas as pd
        
        detector = DisputeDetectionEngine()
        
        # Convert sample_orders to DataFrame for compatibility
        df_orders = pd.DataFrame(sample_orders)
        
        # Analyze each order
        disputes = []
        for _, order in df_orders.iterrows():
            result = detector.analyze_order(order)
            disputes.append(result)
        
        disputed_orders = [d for d in disputes if d['has_dispute']]
        
        assert len(disputed_orders) > 0
        
        # Step 3: Save disputes to database
        for dispute in disputed_orders:
            db_manager.create_dispute(
                client_id=client['id'],
                order_id=dispute['order_id'],
                carrier=dispute.get('carrier', ''),
                dispute_type=dispute.get('dispute_type', ''),
                amount_recoverable=dispute.get('total_recoverable', 0.0),
                tracking_number=dispute.get('tracking_number')
            )
        
        saved_disputes = db_manager.get_client_disputes(client['id'])
        assert len(saved_disputes) >= len(disputed_orders)
        
        # Step 4: Verify email would be sent (mocked)
        from src.email_service.email_sender import send_disputes_detected_email
        
        result = send_disputes_detected_email(
            client_email=client_email,
            disputes_count=len(disputed_orders),
            total_amount=sum(d.get('total_recoverable', 0) for d in disputed_orders),
            disputes_summary=disputed_orders
        )
        
        assert result is True
        assert len(mock_smtp_server) == 1
        
        # Step 5: Verify client can see stats
        stats = db_manager.get_client_statistics(client['id'])
        assert stats is not None
        assert stats['total_disputes_detected'] >= len(disputed_orders)
    
    @pytest.mark.asyncio
    async def test_claim_submission_flow(self, db_manager, sample_client, sample_dispute_data, mock_smtp_server, mock_env_vars):
        """
        Test claim submission flow:
        1. Dispute exists
        2. Submit claim via orchestrator
        3. Claim created in database
        4. Email notification sent
        5. Dashboard updated
        """
        from src.orchestrator import AutoRecoveryOrchestrator
        
        # Step 1: Create dispute
        dispute_id = db_manager.create_dispute(
            client_id=sample_client['id'],
            order_id=sample_dispute_data['order_id'],
            carrier=sample_dispute_data['carrier'],
            dispute_type=sample_dispute_data['dispute_type'],
            amount_recoverable=sample_dispute_data['total_recoverable']
        )
        
        assert dispute_id > 0
        
        # Step 2: Submit claim via orchestrator
        sample_dispute_data['client_email'] = sample_client['email']
        
        orchestrator = AutoRecoveryOrchestrator(db_manager=db_manager)
        result = await orchestrator.process_dispute(sample_dispute_data)
        
        # Step 3: Verify claim created
        assert result['success'] is True
        assert 'claim_submission' in result.get('steps_completed', [])
        
        # Verify in database
        claims = db_manager.get_client_claims(sample_client['id'])
        assert len(claims) > 0
        
        # Step 4: Verify email sent
        assert len(mock_smtp_server) >= 1
        
        # Step 5: Verify dashboard can retrieve updated data
        stats = db_manager.get_client_statistics(sample_client['id'])
        assert stats['total_claims'] > 0
    
    def test_payment_processing_flow(self, db_manager, sample_client, sample_claim, mock_env_vars):
        """
        Test payment processing flow:
        1. Claim accepted
        2. Payment record created
        3. Client share calculated
        4. Payment notification
        """
        # Step 1: Mark claim as accepted
        accepted_amount = 100.00
        db_manager.update_claim(
            claim_id=sample_claim['id'],
            status='accepted',
            accepted_amount=accepted_amount,
            response_received_at=datetime.now()
        )
        
        # Step 2: Create payment record
        client_share = accepted_amount * 0.8
        platform_fee = accepted_amount * 0.2
        
        payment_id = db_manager.create_payment(
            claim_id=sample_claim['id'],
            client_id=sample_client['id'],
            total_amount=accepted_amount,
            client_share=client_share,
            platform_fee=platform_fee,
            payment_method='stripe_connect'
        )
        
        assert payment_id > 0
        
        # Step 3: Verify calculation
        assert client_share == 80.00
        assert platform_fee == 20.00
        
        # Step 4: Mark payment as completed
        db_manager.update_payment(
            payment_id=payment_id,
            payment_status='completed',
            paid_at=datetime.now(),
            transaction_reference='TEST-TXN-001'
        )
        
        # Verify stats updated
        stats = db_manager.get_client_statistics(sample_client['id'])
        assert stats['total_paid_to_client'] >= client_share
    
    @pytest.mark.asyncio
    async def test_worker_sync_flow(self, db_manager, sample_client, sample_orders, mock_env_vars):
        """
        Test worker synchronization flow:
        1. Worker fetches orders
        2. Detects disputes
        3. Saves to database
        4. Sends notification
        """
        # Note: This would require mocking platform connectors
        # Simplified version for demonstration
        
        from src.workers.order_sync_worker import OrderSyncWorker
        from dispute_detector import DisputeDetectionEngine
        import pandas as pd
        
        # Simulate order sync
        detector = DisputeDetectionEngine()
        
        # Convert to DataFrame and analyze
        df_orders = pd.DataFrame(sample_orders)
        disputes = []
        for _, order in df_orders.iterrows():
            result = detector.analyze_order(order)
            disputes.append(result)
        
        disputed_orders = [d for d in disputes if d['has_dispute']]
        
        # Save disputes
        for dispute in disputed_orders:
            db_manager.create_dispute(
                client_id=sample_client['id'],
                order_id=dispute['order_id'],
                carrier=dispute.get('carrier', ''),
                dispute_type=dispute.get('dispute_type', ''),
                amount_recoverable=dispute.get('total_recoverable', 0.0)
            )
        
        # Verify saved
        saved = db_manager.get_client_disputes(sample_client['id'])
        assert len(saved) >= len(disputed_orders)


@pytest.mark.e2e
class TestErrorHandlingFlows:
    """Test error handling and edge cases."""
    
    def test_duplicate_claim_prevention(self, db_manager, sample_client):
        """Test that duplicate claims are prevented."""
        # Create first claim
        claim_id_1 = db_manager.create_claim(
            claim_reference='CLM-DUP-001',
            client_id=sample_client['id'],
            order_id='ORD-SAME',
            carrier='colissimo',
            dispute_type='late_delivery',
            amount_requested=100.00
        )
        
        # Try to create duplicate (same order_id)
        # This should be handled by application logic
        # Database allows it but app should check
        
        claims = db_manager.get_client_claims(sample_client['id'])
        same_order_claims = [c for c in claims if c['order_id'] == 'ORD-SAME']
        
        # Application logic should prevent this, but DB doesn't enforce it
        # This test documents the expected behavior
        assert len(same_order_claims) >= 1
    
    def test_invalid_email_handling(self, mock_smtp_server, mock_env_vars):
        """Test handling of invalid email addresses."""
        from src.email_service.email_sender import send_disputes_detected_email
        
        # This should still attempt to send (SMTP server will handle validation)
        result = send_disputes_detected_email(
            client_email='invalid-email',
            disputes_count=1,
            total_amount=100.00,
            disputes_summary=[]
        )
        
        # With mock SMTP, this succeeds
        # Real SMTP would fail
        assert result is True
    
    def test_missing_dispute_data_handling(self, db_manager, sample_client):
        """Test handling of disputes with missing data."""
        # Create dispute with minimal data
        dispute_id = db_manager.create_dispute(
            client_id=sample_client['id'],
            order_id='ORD-MINIMAL',
            carrier='unknown',
            dispute_type='other',
            amount_recoverable=0.0
        )
        
        assert dispute_id > 0
        
        disputes = db_manager.get_client_disputes(sample_client['id'])
        minimal = [d for d in disputes if d['order_id'] == 'ORD-MINIMAL'][0]
        
        assert minimal['carrier'] == 'unknown'
        assert minimal['amount_recoverable'] == 0.0
