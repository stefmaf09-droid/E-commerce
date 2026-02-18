import sys
import os
import unittest

# Add project root to path
sys.path.append(os.getcwd())

from src.reports.legal_document_generator import LegalDocumentGenerator
from src.utils.i18n import get_i18n_text

class TestLegalGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = LegalDocumentGenerator()

    def test_determine_applicable_law(self):
        # 1. New York Address
        key = self.generator._determine_applicable_law("123 Broadway, New York, NY 10001, USA")
        self.assertEqual(key, 'legal_law_ny')
        
        # 2. California Address
        key = self.generator._determine_applicable_law("456 Market St, San Francisco, CA 94103")
        self.assertEqual(key, 'legal_law_ca')
        
        # 3. UK Address
        key = self.generator._determine_applicable_law("10 Downing Street, London, UK")
        self.assertEqual(key, 'legal_law_uk')
        
        # 4. French Address (EU)
        key = self.generator._determine_applicable_law("1 avenue des Champs-Élysées, 75008 Paris, FRANCE")
        self.assertEqual(key, 'legal_law_eu_cmr')
        
        # 5. Berlin Address (EU)
        key = self.generator._determine_applicable_law("Alexanderplatz 1, 10178 Berlin, GERMANY")
        self.assertEqual(key, 'legal_law_eu_cmr')
        
        # 6. Unknown/Standard
        key = self.generator._determine_applicable_law("Unknown Place")
        self.assertEqual(key, 'legal_body_law')

    def test_i18n_fallback_and_translation(self):
        # 1. Check NY Law in French (Should be present)
        text_ny_fr = get_i18n_text('legal_law_ny', 'FR')
        self.assertIn("État de New York", text_ny_fr)
        
        # 2. Check Texas Law in French (Missing in FR, should fallback to EN)
        # Assuming we didn't add 'legal_law_tx' to FR dict explicitly in the previous step
        text_tx_fr = get_i18n_text('legal_law_tx', 'FR')
        self.assertIn("Texas Deceptive Trade Practices", text_tx_fr) # English text
        
        # 3. Check Unknown Key (Should return key)
        self.assertEqual(get_i18n_text('non_existent_key', 'FR'), 'non_existent_key')

if __name__ == '__main__':
    unittest.main()
