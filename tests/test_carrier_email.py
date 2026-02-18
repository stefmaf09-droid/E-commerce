import sys
import os
import json
import unittest
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.append(os.getcwd())

from src.automation.claim_automation import ClaimAutomation

class TestCarrierEmailSubmission(unittest.TestCase):
    
    def setUp(self):
        self.automation = ClaimAutomation()
        # Mock the EmailSender to avoid real sending
        self.automation.email_sender = MagicMock()
        self.automation.email_sender.send_claim_to_carrier.return_value = True
        
        # Test Data
        self.test_order_id = "ORD-TEST-EMAIL"
        self.test_carrier = "Colissimo"
        self.test_claim_data = {
            'text': "Ceci est un test de réclamation.",
            'amount': 50.0,
            'photos': ['data/photo1.jpg']
        }

    def test_config_load(self):
        """Verify carrier config is loaded."""
        self.assertIn("colissimo", self.automation.carrier_config)
        self.assertEqual(self.automation.carrier_config['colissimo']['email'], "service.client@colissimo.fr")

    def test_submission_flow(self):
        """Test the submission flow works and calls email sender."""
        result = self.automation.submit_claim_to_carrier(
            self.test_order_id,
            self.test_carrier,
            self.test_claim_data
        )
        
        # 1. Check result success
        self.assertTrue(result['success'])
        self.assertIn("Réclamation envoyée à Colissimo", result['message'])
        
        # 2. Verify EmailSender was called with correct parameters
        self.automation.email_sender.send_claim_to_carrier.assert_called_once()
        
        call_args = self.automation.email_sender.send_claim_to_carrier.call_args[1]
        self.assertEqual(call_args['carrier_email'], "service.client@colissimo.fr")
        self.assertIn("TRK-ORD-TEST-EMAIL", call_args['subject'])
        self.assertEqual(call_args['body'], self.test_claim_data['text'])
        self.assertEqual(call_args['attachments'], self.test_claim_data['photos'])

    @patch('src.automation.claim_automation.json.dump')
    def test_fallback_on_failure(self, mock_json_dump):
        """Test that we return fallback error if email fails."""
        self.automation.email_sender.send_claim_to_carrier.return_value = False
        
        result = self.automation.submit_claim_to_carrier(
            self.test_order_id,
            self.test_carrier,
            self.test_claim_data
        )
        
        self.assertFalse(result['success'])
        self.assertIn("Erreur lors de l'envoi email", result['message'])

if __name__ == '__main__':
    unittest.main()
