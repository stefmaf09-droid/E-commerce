"""
Final tests to achieve 100% coverage.
Targets specific uncovered exception paths and helper functions.
"""

import pytest
import sqlite3
from unittest.mock import patch, MagicMock
from src.email_service.escalation_email_handler import EscalationEmailHandler, send_formal_notice
from src.database.escalation_logger import EscalationLogger


class TestFinalCoverageGaps:
    """Tests targeting the last 6 uncovered lines."""
    
    
    def test_helper_function_send_formal_notice(self, tmp_path):
        """Test send_formal_notice helper function (lines 383-384)."""
        # Create a PDF file
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_text("test")
        
        claim = {
            'id': 1,
            'claim_reference': 'CLM-TEST',
            'carrier': 'DHL',
            'tracking_number': 'TEST123',
            'amount_requested': 100.0,
            'dispute_type': 'Lost',
            'customer_name': 'Client',
            'delivery_address': 'Paris',
            'currency': 'EUR'
        }
        
        # Set environment variables for SMTP
        import os
        os.environ['GMAIL_SENDER'] = 'test@example.com'
        os.environ['GMAIL_APP_PASSWORD'] = 'test123'
        
        # Call the REAL helper function (not mocked)
        with patch('src.email_service.escalation_email_handler.smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            # This will execute lines 383-384
            result = send_formal_notice(claim, str(pdf_path), 'FR')
            assert result is True
    
    @patch('src.email_service.escalation_email_handler.MIMEMultipart')
    @patch('src.email_service.escalation_email_handler.smtplib.SMTP')
    def test_email_file_not_found_in_smtp_context(self, mock_smtp, mock_mime, tmp_path):
        """Test FileNotFoundError caught in SMTP context (lines 373-374)."""
        # The PDF file exists
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_text("test content")
        
        handler = EscalationEmailHandler(
            smtp_user='test@example.com',
            smtp_password='test123'
        )
        
        # Mock MIMEMultipart to raise FileNotFoundError when attaching file
        mock_mime_instance = MagicMock()
        mock_mime.return_value = mock_mime_instance
        mock_mime_instance.attach.side_effect = FileNotFoundError("PDF file disappeared")
        
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = handler._send_email_with_attachment(
            to_email='test@example.com',
            subject='Test',
            html_body='<p>Test</p>',
            attachment_path=str(pdf_path)
        )
        
        # Should catch FileNotFoundError and return False (lines 373-374)
        assert result is False
    
    
    def test_get_history_generic_exception(self, tmp_path):
        """Test generic exception in get_claim_escalation_history (lines 224-226)."""
        # Create logger with valid DB
        db_path = tmp_path / "test.db"
        logger = EscalationLogger(str(db_path))
        
        # Mock connect within the method to force exception
        with patch('src.database.escalation_logger.sqlite3.connect') as mock_connect:
            mock_connect.side_effect = RuntimeError("Database failure")
            
            # This should trigger exception and return [] (lines 224-226)
            history = logger.get_claim_escalation_history(1)
            assert history == []
    
    def test_get_statistics_generic_exception(self, tmp_path):
        """Test generic exception in get_escalation_statistics (lines 277-279)."""
        # Create logger with valid DB
        db_path = tmp_path / "stats.db"
        logger = EscalationLogger(str(db_path))
        
        # Mock connect within the method to force exception
        with patch('src.database.escalation_logger.sqlite3.connect') as mock_connect:
            mock_connect.side_effect = IOError("Database connection lost")
            
            # This should trigger exception (lines 277-279)
            stats = logger.get_escalation_statistics()
            assert stats == {
                'total_escalations': 0,
                'by_level': {},
                'by_email_status': {},
                'success_rate': 0
            }
    
    def test_get_recent_escalations_generic_exception(self, tmp_path):
        """Test generic exception in get_recent_escalations (lines 325-327)."""
        # Create logger with valid DB
        db_path = tmp_path / "recent.db"
        logger = EscalationLogger(str(db_path))
        
        # Mock connect within the method to force exception
        with patch('src.database.escalation_logger.sqlite3.connect') as mock_connect:
            mock_connect.side_effect = PermissionError("Database access denied")
            
            # This should trigger exception (lines 325-327)
            recent = logger.get_recent_escalations()
            assert recent == []
