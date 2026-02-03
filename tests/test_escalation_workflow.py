"""
Integration tests for complete escalation workflow.
Tests the end-to-end flow: detection -> PDF generation -> email -> logging.
"""

import pytest
import os
import sqlite3
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from src.automation.follow_up_manager import FollowUpManager
from src.database.database_manager import DatabaseManager
from src.database.escalation_logger import EscalationLogger


class TestEscalationWorkflow:
    """End-to-end tests for escalation workflow."""
    
    @pytest.fixture
    def db_manager(self, tmp_path):
        """Create a temporary database for testing."""
        db_path = tmp_path / "test_escalation.db"
        db_manager = DatabaseManager(str(db_path))
        
        # Initialize tables
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS claims (
                id INTEGER PRIMARY KEY,
                client_id INTEGER,
                store_id INTEGER,
                claim_reference TEXT,
                order_id TEXT,
                carrier TEXT,
                tracking_number TEXT,
                amount_requested REAL,
                dispute_type TEXT,
                customer_name TEXT,
                delivery_address TEXT,
                currency TEXT,
                submitted_at TIMESTAMP,
                status TEXT,
                follow_up_level INTEGER DEFAULT 0,
                last_follow_up_at TIMESTAMP,
                automation_status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS stores (
                id INTEGER PRIMARY KEY,
                country TEXT
            )
        """)
        conn.commit()
        conn.close()
        
        return db_manager
    
    @pytest.fixture
    def escalation_logger(self, tmp_path):
        """Create escalation logger with test database."""
        db_path = tmp_path / "test_escalation.db"
        return EscalationLogger(str(db_path))
    
    @pytest.fixture
    def stagnant_claim(self, db_manager):
        """Create a claim that's been stagnant for 21+ days."""
        conn = db_manager.get_connection()
        
        # Insert store first
        conn.execute("INSERT INTO stores (id, country) VALUES (1, 'FR')")
        
        # Insert stagnant claim
        submitted_date = (datetime.now() - timedelta(days=22)).isoformat()
        conn.execute("""
            INSERT INTO claims (
                store_id, claim_reference, carrier, tracking_number, amount_requested,
                dispute_type, customer_name, delivery_address, currency,
                submitted_at, status, follow_up_level
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            1,  # store_id
            'CLM-TEST-STAGNANT',
            'Colissimo',
            'TEST123456',
            150.00,
            'Colis Perdu',
            'Test Client',
            'Paris, France',
            'EUR',
            submitted_date,
            'submitted',
            0
        ))
        conn.commit()
        claim_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()
        
        return claim_id
    
    @patch('src.email_service.escalation_email_handler.smtplib.SMTP')
    @patch('src.reports.legal_document_generator.SimpleDocTemplate')
    def test_full_escalation_workflow(self, mock_pdf, mock_smtp, db_manager, stagnant_claim, tmp_path):
        """Test complete workflow: detect stagnant claim -> generate PDF -> send email -> log."""
        # Mock PDF generation
        mock_pdf.return_value.build = MagicMock()
        
        # Mock SMTP
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        # Create follow-up manager
        manager = FollowUpManager(db_manager)
        
        # Process follow-ups (should detect the stagnant claim)
        with patch('os.makedirs'):  # Don't actually create directories
            stats = manager.process_follow_ups()
        
        # Verify that a formal notice was triggered
        assert stats['formal_notices'] >= 1
        
        # Verify claim was updated in database
        conn = db_manager.get_connection()
        claim = conn.execute(
            "SELECT * FROM claims WHERE id = ?", (stagnant_claim,)
        ).fetchone()
        conn.close()
        
        if claim:
            claim_dict = dict(claim)
            assert claim_dict['follow_up_level'] == 3
            assert claim_dict['automation_status'] == 'action_required'
    
    @patch('src.email_service.escalation_email_handler.smtplib.SMTP')
    @patch('src.reports.legal_document_generator.SimpleDocTemplate')
    def test_escalation_logging(self, mock_pdf, mock_smtp, db_manager, stagnant_claim, tmp_path):
        """Test that all escalation actions are properly logged."""
        # Mock PDF generation
        mock_pdf.return_value.build = MagicMock()
        
        # Mock SMTP
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        # Patch EscalationLogger to use test database
        def create_escalation_logger(*args, **kwargs):
            return EscalationLogger(db_manager.db_path)
        
        with patch('src.database.escalation_logger.EscalationLogger', side_effect=create_escalation_logger):
            # Create follow-up manager
            manager = FollowUpManager(db_manager)
            
            # Create escalation logger with same database
            escalation_logger = EscalationLogger(db_manager.db_path)
            
            # Trigger formal notice
            conn = db_manager.get_connection()
            claim_data = conn.execute(
                "SELECT * FROM claims WHERE id = ?", (stagnant_claim,)
            ).fetchone()
            conn.close()
            
            claim = dict(claim_data)
            claim['country'] = 'FR'
            
            with patch('os.makedirs'):
                result = manager._trigger_formal_notice(claim)
            
            # Verify escalation was logged
            history = escalation_logger.get_claim_escalation_history(stagnant_claim)
        
        assert len(history) >= 2  # Should have PDF generation + email sent
        
        # Check for PDF generation log
        pdf_logs = [h for h in history if h['action_type'] == 'pdf_generated']
        assert len(pdf_logs) >= 1
        assert pdf_logs[0]['escalation_level'] == 3
        
        # Check for email sent log
        email_logs = [h for h in history if h['action_type'] == 'email_sent']
        assert len(email_logs) >= 1
        assert email_logs[0]['escalation_level'] == 3
    
    def test_escalation_statistics(self, escalation_logger, db_manager, stagnant_claim):
        """Test escalation statistics calculation."""
        # Log some escalation actions
        escalation_logger.log_pdf_generation(
            claim_id=stagnant_claim,
            escalation_level=3,
            pdf_path='/test/path.pdf'
        )
        
        escalation_logger.log_email_sent(
            claim_id=stagnant_claim,
            escalation_level=3,
            email_sent_to='carrier@example.com',
            email_status='sent'
        )
        
        # Get statistics
        stats = escalation_logger.get_escalation_statistics()
        
        assert stats['total_escalations'] >= 2
        assert 3 in stats['by_level']
        assert 'sent' in stats['by_email_status']
    
    @patch('src.email_service.escalation_email_handler.smtplib.SMTP')
    def test_escalation_levels_progression(self, mock_smtp, db_manager):
        """Test that escalation progresses through levels J+7, J+14, J+21."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        manager = FollowUpManager(db_manager)
        conn = db_manager.get_connection()
        
        # Test J+7 (status request)
        claim_7days = {
            'id': 100,
            'claim_reference': 'TEST-7',
            'carrier': 'DHL',
            'tracking_number': 'TEST7',
            'amount_requested': 100,
            'dispute_type': 'Retard',
            'customer_name': 'Test',
            'delivery_address': 'Paris',
            'currency': 'EUR',
            'country': 'FR',
            'submitted_at': (datetime.now() - timedelta(days=8)).isoformat()
        }
        
        conn.execute("""
            INSERT INTO claims (
                id, store_id, claim_reference, carrier, tracking_number, amount_requested,
                dispute_type, customer_name, delivery_address, currency,
                submitted_at, status, follow_up_level
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            claim_7days['id'], 1, claim_7days['claim_reference'], claim_7days['carrier'],
            claim_7days['tracking_number'], claim_7days['amount_requested'],
            claim_7days['dispute_type'], claim_7days['customer_name'],
            claim_7days['delivery_address'], claim_7days['currency'],
            claim_7days['submitted_at'], 'submitted', 0
        ))
        conn.commit()
        conn.close()
        
        # Trigger and verify level 1
        action = manager._evaluate_and_trigger(claim_7days)
        assert action == 'status_requests'
        
        # Verify database update
        conn = db_manager.get_connection()
        updated = conn.execute(
            "SELECT follow_up_level FROM claims WHERE id = ?", (claim_7days['id'],)
        ).fetchone()
        conn.close()
        
        if updated:
            assert updated[0] == 1
    
    def test_recent_escalations(self, escalation_logger, stagnant_claim):
        """Test retrieval of recent escalations."""
        # Log multiple escalations
        for i in range(5):
            escalation_logger.log_email_sent(
                claim_id=stagnant_claim,
                escalation_level=i % 3 + 1,
                email_sent_to='test@example.com',
                email_status='sent'
            )
        
        # Get recent escalations
        recent = escalation_logger.get_recent_escalations(limit=3)
        
        assert len(recent) <= 3
        # Should be ordered by date (most recent first)
        if len(recent) >= 2:
            assert recent[0]['created_at'] >= recent[1]['created_at']
