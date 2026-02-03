"""
Additional tests to improve coverage for escalation modules.
Focuses on edge cases, error paths, and uncovered scenarios.
"""

import pytest
import sqlite3
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from src.email_service.escalation_email_handler import EscalationEmailHandler
from src.database.escalation_logger import EscalationLogger, log_escalation_action
from src.automation.follow_up_manager import FollowUpManager
from src.database.database_manager import DatabaseManager


class TestEscalationEdgeCases:
    """Tests for edge cases and error paths."""
    
    @pytest.fixture
    def sample_claim(self):
        """Sample claim with unknown carrier."""
        return {
            'id': 1,
            'claim_reference': 'CLM-TEST-UNKNOWN',
            'carrier': 'UnknownCarrier',  # Not in carrier_emails dict
            'tracking_number': 'TEST999',
            'amount_requested': 100.00,
            'dispute_type': 'Test',
            'customer_name': 'Test Client',
            'delivery_address': 'Test Address',
            'currency': 'EUR',
            'country': 'FR',
            'submitted_at': datetime.now().isoformat()
        }
    
    def test_unknown_carrier_email(self, sample_claim, tmp_path):
        """Test handling of unknown carrier (lines 86-88)."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_text("test")
        
        handler = EscalationEmailHandler(
            smtp_user='test@example.com',
            smtp_password='test_pass',
            from_email='test@example.com'
        )
        
        with patch('src.email_service.escalation_email_handler.smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            # Send to unknown carrier (should fallback to from_email)
            result = handler.send_formal_notice_email(
                claim=sample_claim,
                pdf_path=str(pdf_path),
                lang='FR'
            )
            
            # Should succeed using fallback email
            assert result is True
            mock_server.send_message.assert_called_once()
    
    def test_email_template_missing_type(self):
        """Test email template with invalid type (line 306)."""
        handler = EscalationEmailHandler()
        claim = {'claim_reference': 'TEST', 'carrier': 'DHL', 'tracking_number': '123'}
        
        # Invalid email type should return empty string
        result = handler._create_email_template('invalid_type', claim, 'FR')
        assert result == ""
    
    @patch('src.email_service.escalation_email_handler.smtplib.SMTP')
    def test_email_send_file_not_found_exception(self, mock_smtp, tmp_path):
        """Test SMTP FileNotFoundError exception (lines 373-374)."""
        handler = EscalationEmailHandler(
            smtp_user='test@example.com',
            smtp_password='test123'
        )
        
        # Mock SMTP to raise FileNotFoundError
        mock_smtp.return_value.__enter__.return_value.send_message.side_effect = FileNotFoundError("File error")
        
        result = handler._send_email_with_attachment(
            to_email='test@example.com',
            subject='Test',
            html_body='<p>Test</p>',
            attachment_path='/nonexistent/file.pdf'  # Will fail early check
        )
        
        # Should return False due to file not existing
        assert result is False
    
    @patch('src.email_service.escalation_email_handler.smtplib.SMTP')
    def test_email_send_generic_exception(self, mock_smtp, tmp_path):
        """Test generic exception during email send (lines 383-384)."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_text("test content")
        
        handler = EscalationEmailHandler(
            smtp_user='test@example.com',
            smtp_password='test123'
        )
        
        # Mock to raise a generic exception
        mock_smtp.return_value.__enter__.return_value.send_message.side_effect = RuntimeError("Network error")
        
        result = handler._send_email_with_attachment(
            to_email='test@example.com',
            subject='Test',
            html_body='<p>Test</p>',
            attachment_path=str(pdf_path)
        )
        
        assert result is False


class TestEscalationLoggerEdgeCases:
    """Tests for escalation logger edge cases."""
    
    def test_table_creation_error(self, tmp_path):
        """Test error during table creation (lines 54-55)."""
        db_path = tmp_path / "readonly.db"
        
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_conn.execute.side_effect = sqlite3.OperationalError("Table error")
            mock_connect.return_value = mock_conn
            
            # Should handle error gracefully
            logger = EscalationLogger(str(db_path))
            assert logger is not None
    
    def test_log_action_database_error(self, tmp_path):
        """Test error during log action (lines 187-189)."""
        logger = EscalationLogger(str(tmp_path / "test.db"))
        
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_conn.execute.side_effect = sqlite3.OperationalError("Insert error")
            mock_connect.return_value = mock_conn
            
            # Should return -1 on error
            result = logger._log_action(
                claim_id=1,
                escalation_level=3,
                action_type='test'
            )
            assert result == -1
    
    def test_log_carrier_response(self, tmp_path):
        """Test logging carrier response (line 136)."""
        logger = EscalationLogger(str(tmp_path / "test.db"))
        
        response_details = {
            'response_type': 'acceptance',
            'amount_approved': 100.00,
            'response_date': '2026-01-31'
        }
        
        log_id = logger.log_carrier_response(
            claim_id=1,
            escalation_level=3,
            details=response_details
        )
        
        assert log_id > 0
        
        # Verify it was logged
        history = logger.get_claim_escalation_history(1)
        assert len(history) == 1
        assert history[0]['action_type'] == 'carrier_response'
        assert history[0]['details']['response_type'] == 'acceptance'
    
    def test_get_history_json_parse_error(self, tmp_path):
        """Test JSON parse error in get_history (lines 219-220)."""
        logger = EscalationLogger(str(tmp_path / "test.db"))
        
        # Insert invalid JSON manually
        conn = sqlite3.connect(str(tmp_path / "test.db"))
        conn.execute("""
            INSERT INTO escalation_log (claim_id, escalation_level, action_type, details)
            VALUES (1, 3, 'test', 'invalid json{')
        """)
        conn.commit()
        conn.close()
        
        # Should handle gracefully
        history = logger.get_claim_escalation_history(1)
        assert len(history) == 1
        # Invalid JSON should be kept as string
        assert history[0]['details'] == 'invalid json{'
    
    def test_get_recent_escalations_with_details_error(self, tmp_path):
        """Test JSON parse error in get_recent_escalations (lines 318-321)."""
        logger = EscalationLogger(str(tmp_path / "test.db"))
        
        # Create claims table for JOIN
        conn = sqlite3.connect(str(tmp_path / "test.db"))
        conn.execute("""
            CREATE TABLE claims (
                id INTEGER PRIMARY KEY,
                claim_reference TEXT,
                carrier TEXT,
                amount_requested REAL
            )
        """)
        conn.execute("INSERT INTO claims VALUES (1, 'CLM-001', 'DHL', 100.0)")
        conn.execute("""
            INSERT INTO escalation_log (claim_id, escalation_level, action_type, details)
            VALUES (1, 3, 'test', 'bad json[')
        """)
        conn.commit()
        conn.close()
        
        # Should handle invalid JSON gracefully
        recent = logger.get_recent_escalations(limit=5)
        assert len(recent) == 1
        assert recent[0]['details'] == 'bad json['
    
    def test_helper_function_log_escalation_action(self, tmp_path):
        """Test helper function (lines 340-341)."""
        # Test the standalone helper function
        with patch('src.database.escalation_logger.EscalationLogger') as mock_logger_class:
            mock_instance = MagicMock()
            mock_instance._log_action.return_value = 123
            mock_logger_class.return_value = mock_instance
            
            result = log_escalation_action(
                claim_id=1,
                escalation_level=3,
                action_type='test',
                pdf_path='/test/path.pdf'
            )
            
            assert result == 123
            mock_instance._log_action.assert_called_once()
