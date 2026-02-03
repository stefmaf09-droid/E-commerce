"""
Tests for Database Manager.

Tests CRUD operations, transactions, and data integrity.
"""

import pytest
from datetime import datetime, timedelta


class TestDatabaseManager:
    """Test DatabaseManager class."""
    
    def test_database_initialization(self, temp_db):
        """Test database is properly initialized."""
        from src.database import DatabaseManager
        
        db = DatabaseManager(db_path=temp_db)
        conn = db.get_connection()
        
        # Check tables exist
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = [
            'clients', 'stores', 'claims', 'disputes',
            'payments', 'notifications', 'activity_logs', 'system_settings'
        ]
        
        for table in expected_tables:
            assert table in tables, f"Table {table} not found"
        
        conn.close()
    
    def test_create_client(self, db_manager):
        """Test creating a client."""
        client_id = db_manager.create_client(
            email='new@example.com',
            full_name='New User',
            company_name='New Company'
        )
        
        assert client_id > 0
        
        # Verify client was created
        client = db_manager.get_client(client_id=client_id)
        assert client is not None
        assert client['email'] == 'new@example.com'
        assert client['full_name'] == 'New User'
        assert client['is_active'] == 1
    
    def test_create_duplicate_client(self, db_manager, sample_client):
        """Test creating duplicate client returns existing ID."""
        # Try to create same client again
        client_id = db_manager.create_client(
            email=sample_client['email'],
            full_name='Different Name'
        )
        
        # Should return existing client ID
        assert client_id == sample_client['id']
    
    def test_update_client(self, db_manager, sample_client):
        """Test updating client information."""
        db_manager.update_client(
            client_id=sample_client['id'],
            full_name='Updated Name',
            phone='+33698765432'
        )
        
        updated = db_manager.get_client(client_id=sample_client['id'])
        assert updated['full_name'] == 'Updated Name'
        assert updated['phone'] == '+33698765432'
    
    def test_create_claim(self, db_manager, sample_client):
        """Test creating a claim."""
        claim_id = db_manager.create_claim(
            claim_reference='CLM-2026-001',
            client_id=sample_client['id'],
            order_id='ORD-999',
            carrier='dhl',
            dispute_type='lost',
            amount_requested=200.00,
            tracking_number='DHL999888777'
        )
        
        assert claim_id > 0
        
        claim = db_manager.get_claim(claim_id=claim_id)
        assert claim['claim_reference'] == 'CLM-2026-001'
        assert claim['carrier'] == 'dhl'
        assert claim['status'] == 'pending'
        assert claim['amount_requested'] == 200.00
    
    def test_update_claim_status(self, db_manager, sample_claim):
        """Test updating claim status."""
        now = datetime.now()
        
        db_manager.update_claim(
            claim_id=sample_claim['id'],
            status='submitted',
            submitted_at=now,
            automation_status='automated'
        )
        
        updated = db_manager.get_claim(claim_id=sample_claim['id'])
        assert updated['status'] == 'submitted'
        assert updated['automation_status'] == 'automated'
        assert updated['submitted_at'] is not None
    
    def test_get_client_claims(self, db_manager, sample_client):
        """Test retrieving all claims for a client."""
        # Create multiple claims
        for i in range(3):
            db_manager.create_claim(
                claim_reference=f'CLM-MULTI-{i}',
                client_id=sample_client['id'],
                order_id=f'ORD-MULTI-{i}',
                carrier='colissimo',
                dispute_type='late_delivery',
                amount_requested=100.0 + i * 50
            )
        
        claims = db_manager.get_client_claims(sample_client['id'])
        assert len(claims) >= 3
    
    def test_get_client_claims_by_status(self, db_manager, sample_client):
        """Test filtering claims by status."""
        # Create pending claim
        pending_id = db_manager.create_claim(
            claim_reference='CLM-PENDING',
            client_id=sample_client['id'],
            order_id='ORD-P',
            carrier='ups',
            dispute_type='damaged',
            amount_requested=150.00
        )
        
        # Create submitted claim
        submitted_id = db_manager.create_claim(
            claim_reference='CLM-SUBMITTED',
            client_id=sample_client['id'],
            order_id='ORD-S',
            carrier='ups',
            dispute_type='damaged',
            amount_requested=200.00
        )
        db_manager.update_claim(claim_id=submitted_id, status='submitted')
        
        # Get only submitted
        submitted_claims = db_manager.get_client_claims(
            sample_client['id'],
            status='submitted'
        )
        
        assert len(submitted_claims) >= 1
        assert all(c['status'] == 'submitted' for c in submitted_claims)
    
    def test_create_dispute(self, db_manager, sample_client):
        """Test creating a dispute."""
        dispute_id = db_manager.create_dispute(
            client_id=sample_client['id'],
            order_id='ORD-DISPUTE-001',
            carrier='chronopost',
            dispute_type='late_delivery',
            amount_recoverable=175.00,
            tracking_number='CH123456789'
        )
        
        assert dispute_id > 0
        
        disputes = db_manager.get_client_disputes(sample_client['id'])
        assert len(disputes) >= 1
        
        dispute = disputes[0]
        assert dispute['carrier'] == 'chronopost'
        assert dispute['is_claimed'] == 0
    
    def test_mark_dispute_claimed(self, db_manager, sample_client, sample_claim):
        """Test marking dispute as claimed."""
        dispute_id = db_manager.create_dispute(
            client_id=sample_client['id'],
            order_id='ORD-TO-CLAIM',
            carrier='dhl',
            dispute_type='lost',
            amount_recoverable=300.00
        )
        
        db_manager.mark_dispute_claimed(
            dispute_id=dispute_id,
            claim_id=sample_claim['id']
        )
        
        unclaimed = db_manager.get_client_disputes(
            sample_client['id'],
            is_claimed=False
        )
        claimed = db_manager.get_client_disputes(
            sample_client['id'],
            is_claimed=True
        )
        
        # The marked one should be in claimed
        assert any(d['id'] == dispute_id for d in claimed)
    
    def test_create_payment(self, db_manager, sample_claim, sample_client):
        """Test creating a payment record."""
        total = 100.0
        client_share = total * 0.8
        platform_fee = total * 0.2
        
        payment_id = db_manager.create_payment(
            claim_id=sample_claim['id'],
            client_id=sample_client['id'],
            total_amount=total,
            client_share=client_share,
            platform_fee=platform_fee,
            payment_method='stripe_connect'
        )
        
        assert payment_id > 0
    
    def test_log_notification(self, db_manager, sample_client):
        """Test logging a notification."""
        notif_id = db_manager.log_notification(
            client_id=sample_client['id'],
            notification_type='claim_submitted',
            subject='Test notification',
            sent_to=sample_client['email'],
            status='sent'
        )
        
        assert notif_id > 0
    
    def test_log_activity(self, db_manager, sample_client):
        """Test logging activity."""
        db_manager.log_activity(
            action='test_action',
            client_id=sample_client['id'],
            resource_type='claim',
            resource_id=1,
            details={'test': 'data'},
            ip_address='127.0.0.1'
        )
        
        # If we get here without exception, logging worked
        assert True
    
    def test_get_client_statistics(self, db_manager, sample_client, sample_claim):
        """Test retrieving client statistics."""
        stats = db_manager.get_client_statistics(sample_client['id'])
        
        assert stats is not None
        assert 'total_claims' in stats
        assert 'total_requested' in stats
        assert stats['client_id'] == sample_client['id']
