"""
Integration tests for escalation workflow (email sending with PDF attachments).
"""

import pytest
import os
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from src.email_service.escalation_email_handler import EscalationEmailHandler


class TestEscalationEmails:
    """Tests for escalation email functionality."""
    
    @pytest.fixture
    def sample_claim(self):
        """Sample claim data for testing."""
        return {
            'id': 1,
            'claim_reference': 'CLM-TEST-2026-001',
            'carrier': 'Colissimo',
            'tracking_number': 'TEST123456789',
            'amount_requested': 150.00,
            'dispute_type': 'Colis Perdu',
            'customer_name': 'Test Client',
            'delivery_address': 'Paris, France',
            'currency': 'EUR',
            'country': 'FR',
            'submitted_at': datetime.now().isoformat()
        }
    
    @pytest.fixture
    def email_handler(self):
        """Email handler with test credentials."""
        return EscalationEmailHandler(
            smtp_user='test@example.com',
            smtp_password='test_password',
            from_email='test@example.com'
        )
    
    def test_email_handler_initialization(self, email_handler):
        """Test that email handler initializes correctly."""
        assert email_handler.smtp_user == 'test@example.com'
        assert email_handler.from_email == 'test@example.com'
        assert 'Colissimo' in email_handler.carrier_emails
    
    def test_create_subject_formal_notice_fr(self, email_handler, sample_claim):
        """Test subject creation for formal notice in French."""
        subject = email_handler._create_subject('formal_notice', sample_claim, 'FR')
        assert '⚖️' in subject
        assert 'MISE EN DEMEURE' in subject
        assert sample_claim['claim_reference'] in subject
    
    def test_create_subject_status_request_en(self, email_handler, sample_claim):
        """Test subject creation for status request in English."""
        subject = email_handler._create_subject('status_request', sample_claim, 'EN')
        assert 'Status Update Request' in subject
        assert sample_claim['claim_reference'] in subject
    
    def test_create_email_template_formal_notice(self, email_handler, sample_claim):
        """Test email template generation for formal notice."""
        html = email_handler._create_email_template('formal_notice', sample_claim, 'FR')
        
        assert 'MISE EN DEMEURE OFFICIELLE' in html
        assert sample_claim['claim_reference'] in html
        assert sample_claim['tracking_number'] in html
        # Note: carrier name is not directly in template text, it's in the metadata
        assert '150' in html  # Amount
    
    def test_create_email_template_status_request(self, email_handler, sample_claim):
        """Test email template generation for status request."""
        html = email_handler._create_email_template('status_request', sample_claim, 'FR')
        
        assert sample_claim['claim_reference'] in html
        assert sample_claim['tracking_number'] in html
        assert 'mise à jour' in html.lower()
    
    def test_create_email_template_warning(self, email_handler, sample_claim):
        """Test email template generation for warning."""
        html = email_handler._create_email_template('warning', sample_claim, 'FR')
        
        assert 'DERNIER RAPPEL' in html
        assert sample_claim['claim_reference'] in html
        assert '⚠️' in html
    
    @patch('src.email_service.escalation_email_handler.smtplib.SMTP')
    def test_send_email_with_attachment_success(self, mock_smtp, email_handler, sample_claim, tmp_path):
        """Test successful email sending with PDF attachment."""
        # Create a temporary PDF file
        pdf_path = tmp_path / "test_formal_notice.pdf"
        pdf_path.write_text("Test PDF content")
        
        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        # Send email
        result = email_handler._send_email_with_attachment(
            to_email='carrier@example.com',
            subject='Test Subject',
            html_body='<p>Test Body</p>',
            attachment_path=str(pdf_path),
            claim_ref=sample_claim['claim_reference']
        )
        
        assert result is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()
        mock_server.send_message.assert_called_once()
    
    @patch('src.email_service.escalation_email_handler.smtplib.SMTP')
    def test_send_email_with_missing_attachment(self, mock_smtp, email_handler, sample_claim):
        """Test email sending with missing PDF attachment."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        # Try to send with non-existent file
        result = email_handler._send_email_with_attachment(
            to_email='carrier@example.com',
            subject='Test Subject',
            html_body='<p>Test Body</p>',
            attachment_path='/nonexistent/file.pdf',
            claim_ref=sample_claim['claim_reference']
        )
        
        # Should fail due to missing file
        assert result is False
    
    @patch('src.email_service.escalation_email_handler.smtplib.SMTP')
    def test_send_email_smtp_error(self, mock_smtp, email_handler, sample_claim, tmp_path):
        """Test email sending with SMTP error."""
        # Create a temporary PDF file
        pdf_path = tmp_path / "test_formal_notice.pdf"
        pdf_path.write_text("Test PDF content")
        
        # Mock SMTP to raise exception
        mock_smtp.return_value.__enter__.return_value.send_message.side_effect = Exception("SMTP Error")
        
        # Send email
        result = email_handler._send_email_with_attachment(
            to_email='carrier@example.com',
            subject='Test Subject',
            html_body='<p>Test Body</p>',
            attachment_path=str(pdf_path),
            claim_ref=sample_claim['claim_reference']
        )
        
        assert result is False
    
    @patch('src.email_service.escalation_email_handler.smtplib.SMTP')
    def test_send_formal_notice_email(self, mock_smtp, email_handler, sample_claim, tmp_path):
        """Test sending formal notice email (full workflow)."""
        # Create a temporary PDF file
        pdf_path = tmp_path / "formal_notice.pdf"
        pdf_path.write_text("Formal Notice PDF")
        
        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        # Send formal notice
        result = email_handler.send_formal_notice_email(
            claim=sample_claim,
            pdf_path=str(pdf_path),
            lang='FR'
        )
        
        assert result is True
        mock_server.send_message.assert_called_once()
    
    @patch('src.email_service.escalation_email_handler.smtplib.SMTP')
    def test_send_status_request_email(self, mock_smtp, email_handler, sample_claim):
        """Test sending status request email."""
        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        # Send status request
        result = email_handler.send_status_request_email(
            claim=sample_claim,
            lang='FR'
        )
        
        assert result is True
        mock_server.send_message.assert_called_once()
    
    @patch('src.email_service.escalation_email_handler.smtplib.SMTP')
    def test_send_warning_email(self, mock_smtp, email_handler, sample_claim):
        """Test sending warning email."""
        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        # Send warning
        result = email_handler.send_warning_email(
            claim=sample_claim,
            lang='FR'
        )
        
        assert result is True
        mock_server.send_message.assert_called_once()
    
    def test_email_templates_multilingual(self, email_handler, sample_claim):
        """Test that email templates work for all supported languages."""
        languages = ['FR', 'EN', 'DE', 'IT', 'ES']
        
        for lang in languages:
            # Test subject
            subject = email_handler._create_subject('formal_notice', sample_claim, lang)
            assert len(subject) > 0
            assert sample_claim['claim_reference'] in subject
            
            # Test template
            html = email_handler._create_email_template('formal_notice', sample_claim, lang)
            assert len(html) > 100  # Template should be substantial
            assert sample_claim['claim_reference'] in html
    
    def test_email_handler_without_credentials(self):
        """Test that email handler fails gracefully without credentials."""
        handler = EscalationEmailHandler(
            smtp_user=None,
            smtp_password=None
        )
        
        result = handler._send_email_with_attachment(
            to_email='test@example.com',
            subject='Test',
            html_body='<p>Test</p>'
        )
        
        assert result is False
