import sys
import os
import json
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

# Add src to path
sys.path.append(os.getcwd())

from src.automation.claim_automation import ClaimAutomation

class TestClaimPDF(unittest.TestCase):
    
    def setUp(self):
        self.automation = ClaimAutomation()
        # Mock Email to avoid sending
        self.automation.email_sender = MagicMock()
        self.automation.email_sender.send_claim_to_carrier.return_value = True
        
        # Test Data
        self.test_order_id = "ORD-PDF-TEST-001"
        self.test_carrier = "Colissimo"
        self.test_claim_data = {
            'text': "Claim text body.",
            'amount': 75.50,
            'photos': []
        }

    def test_pdf_creation_and_attachment(self):
        """Test that PDF is created and added to attachments."""
        result = self.automation.submit_claim_to_carrier(
            self.test_order_id,
            self.test_carrier,
            self.test_claim_data
        )
        
        self.assertTrue(result['success'])
        
        # Check if email sender was called
        self.automation.email_sender.send_claim_to_carrier.assert_called_once()
        call_args = self.automation.email_sender.send_claim_to_carrier.call_args[1]
        attachments = call_args['attachments']
        
        # Verify attachments list contains a PDF
        pdf_attachment = next((f for f in attachments if f.endswith('.pdf')), None)
        self.assertIsNotNone(pdf_attachment, "PDF file missing from attachments")
        
        # Verify file actually exists on disk
        self.assertTrue(os.path.exists(pdf_attachment), f"PDF file not found at {pdf_attachment}")
        
        # Cleanup
        try:
            os.remove(pdf_attachment)
        except:
            pass

if __name__ == '__main__':
    unittest.main()
