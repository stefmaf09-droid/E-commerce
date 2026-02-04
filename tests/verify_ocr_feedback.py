
import unittest
import os
import json
import sys
import shutil

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scrapers.ocr_processor import OCRProcessor

class TestOCRFeedback(unittest.TestCase):
    
    def test_save_correction(self):
        print("\n--- Testing OCR Feedback Loop ---")
        
        # Setup
        processor = OCRProcessor()
        test_text = "Refus pour signature non conforme."
        corrected_reason = "bad_signature"
        user_comment = "La signature est illisible"
        
        # Execute
        success = processor.save_correction(test_text, corrected_reason, user_comment)
        self.assertTrue(success, "save_correction should return True")
        
        # Verify File
        feedback_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'ocr_feedback.json')
        self.assertTrue(os.path.exists(feedback_file), "Feedback file should exist")
        
        # Verify Content
        with open(feedback_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        last_entry = data[-1]
        self.assertEqual(last_entry['corrected_reason_key'], corrected_reason)
        self.assertEqual(last_entry['user_feedback'], user_comment)
        self.assertIn(test_text, last_entry['original_text_snippet'])
        
        print(f"✅ Feedback saved correctly to {feedback_file}")

if __name__ == '__main__':
    unittest.main()
