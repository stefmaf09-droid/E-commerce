"""
Tests for Email Notifications.

Tests email sending with mock SMTP and template rendering.
"""

import pytest
import os


class TestEmailTemplates:
    """Test email template generation."""
    
    def test_template_disputes_detected(self):
        """Test disputes detected template generation."""
        from src.email_service.email_templates import template_disputes_detected
        
        html = template_disputes_detected(
            client_name='Jean Dupont',
            disputes_count=3,
            total_amount=450.00,
            disputes_summary=[
                {'order_id': 'ORD-001', 'carrier': 'Colissimo', 
                 'dispute_type': 'late_delivery', 'total_recoverable': 150.0},
                {'order_id': 'ORD-002', 'carrier': 'Chronopost', 
                 'dispute_type': 'lost', 'total_recoverable': 200.0},
                {'order_id': 'ORD-003', 'carrier': 'DHL', 
                 'dispute_type': 'damaged', 'total_recoverable': 100.0}
            ]
        )
        
        assert 'Jean Dupont' in html
        assert '3' in html
        assert '450' in html
        assert 'Colissimo' in html
        assert 'ORD-001' in html
    
    def test_template_claim_submitted(self):
        """Test claim submitted template generation."""
        from src.email_service.email_templates import template_claim_submitted
        
        html = template_claim_submitted(
            client_name='Marie Martin',
            claim_reference='CLM-2026-001',
            carrier='colissimo',
            amount_requested=150.00,
            order_id='ORD-123',
            submission_method='api'
        )
        
        assert 'Marie Martin' in html
        assert 'CLM-2026-001' in html
        assert '150' in html
        assert 'ORD-123' in html
    
    def test_template_claim_accepted(self):
        """Test claim accepted template generation."""
        from src.email_service.email_templates import template_claim_accepted
        
        html = template_claim_accepted(
            client_name='Test User',
            claim_reference='CLM-2026-002',
            carrier='chronopost',
            accepted_amount=200.00,
            client_share=160.00,
            platform_fee=40.00
        )
        
        assert 'Test User' in html
        assert 'CLM-2026-002' in html
        assert '200' in html
        assert '160' in html  # Client share
        assert '40' in html   # Platform fee
    
    def test_template_claim_rejected(self):
        """Test claim rejected template generation."""
        from src.email_service.email_templates import template_claim_rejected
        
        html = template_claim_rejected(
            client_name='Test User',
            claim_reference='CLM-2026-003',
            carrier='ups',
            rejection_reason='POD signature valide'
        )
        
        assert 'Test User' in html
        assert 'CLM-2026-003' in html
        assert 'POD signature valide' in html


class TestEmailSender:
    """Test EmailSender class."""
    
    def test_send_disputes_detected_email(self, mock_smtp_server, mock_env_vars):
        """Test sending disputes detected email."""
        from src.email_service.email_sender import EmailSender
        
        sender = EmailSender(
            smtp_user=mock_env_vars['GMAIL_SENDER'],
            smtp_password=mock_env_vars['GMAIL_APP_PASSWORD'],
            from_email=mock_env_vars['GMAIL_SENDER']
        )
        
        result = sender.send_disputes_detected_email(
            to_email='client@example.com',
            client_name='Test Client',
            disputes_count=2,
            total_amount=300.00,
            disputes_summary=[]
        )
        
        assert result is True
        assert len(mock_smtp_server) == 1
        
        email = mock_smtp_server[0]
        assert email['to'] == 'client@example.com'
        assert '2' in email['subject']
        assert '300' in email['subject']
    
    def test_send_claim_submitted_email(self, mock_smtp_server, mock_env_vars):
        """Test sending claim submitted email."""
        from src.email_service.email_sender import EmailSender
        
        sender = EmailSender(
            smtp_user=mock_env_vars['GMAIL_SENDER'],
            smtp_password=mock_env_vars['GMAIL_APP_PASSWORD'],
            from_email=mock_env_vars['GMAIL_SENDER']
        )
        
        result = sender.send_claim_submitted_email(
            to_email='client@example.com',
            client_name='Test Client',
            claim_reference='CLM-TEST-001',
            carrier='colissimo',
            amount_requested=150.00,
            order_id='ORD-123',
            submission_method='api'
        )
        
        assert result is True
        assert len(mock_smtp_server) == 1
        
        email = mock_smtp_server[0]
        assert 'CLM-TEST-001' in email['subject']
    
    def test_send_claim_accepted_email(self, mock_smtp_server, mock_env_vars):
        """Test sending claim accepted email."""
        from src.email_service.email_sender import EmailSender
        
        sender = EmailSender(
            smtp_user=mock_env_vars['GMAIL_SENDER'],
            smtp_password=mock_env_vars['GMAIL_APP_PASSWORD'],
            from_email=mock_env_vars['GMAIL_SENDER']
        )
        
        result = sender.send_claim_accepted_email(
            to_email='client@example.com',
            client_name='Test Client',
            claim_reference='CLM-TEST-002',
            carrier='chronopost',
            accepted_amount=200.00,
            client_share=160.00,
            platform_fee=40.00
        )
        
        assert result is True
        assert len(mock_smtp_server) == 1
        
        email = mock_smtp_server[0]
        assert email['to'] == 'client@example.com'
        assert '160' in email['subject']  # Client share amount
    
    def test_send_claim_rejected_email(self, mock_smtp_server, mock_env_vars):
        """Test sending claim rejected email."""
        from src.email_service.email_sender import EmailSender
        
        sender = EmailSender(
            smtp_user=mock_env_vars['GMAIL_SENDER'],
            smtp_password=mock_env_vars['GMAIL_APP_PASSWORD'],
            from_email=mock_env_vars['GMAIL_SENDER']
        )
        
        result = sender.send_claim_rejected_email(
            to_email='client@example.com',
            client_name='Test Client',
            claim_reference='CLM-TEST-003',
            carrier='ups',
            rejection_reason='Test rejection reason'
        )
        
        assert result is True
        assert len(mock_smtp_server) == 1


class TestEmailHelperFunctions:
    """Test email helper functions."""
    
    def test_send_disputes_detected_email_helper(self, mock_smtp_server, mock_env_vars):
        """Test send_disputes_detected_email helper function."""
        from src.email_service.email_sender import send_disputes_detected_email
        
        result = send_disputes_detected_email(
            client_email='test@example.com',
            disputes_count=1,
            total_amount=100.00,
            disputes_summary=[]
        )
        
        assert result is True
        assert len(mock_smtp_server) == 1
    
    def test_send_claim_submitted_email_helper(self, mock_smtp_server, mock_env_vars):
        """Test send_claim_submitted_email helper function."""
        from src.email_service.email_sender import send_claim_submitted_email
        
        result = send_claim_submitted_email(
            client_email='test@example.com',
            claim_reference='CLM-HELP-001',
            carrier='colissimo',
            amount_requested=150.00,
            order_id='ORD-999',
            submission_method='portal'
        )
        
        assert result is True
        assert len(mock_smtp_server) == 1
