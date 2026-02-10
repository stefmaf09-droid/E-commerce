
import sys
import os

# Path Setup
root_dir = r"d:\Recours_Ecommerce"
sys.path.insert(0, os.path.join(root_dir, 'src'))

from src.ai.appeal_generator import AppealGenerator

def test_appeal_generation():
    print("Testing AppealGenerator...")
    generator = AppealGenerator()
    
    test_cases = [
        {
            'reason': 'bad_signature',
            'data': {
                'tracking_number': '1Z99999999999',
                'claim_reference': 'CLM-2024-TEST-01',
                'recipient_name': 'M. Martin',
                'client_name': 'Shop & Co',
                'amount_requested': 150.50,
                'client_email': 'contact@shop.com'
            }
        },
        {
            'reason': 'weight_match',
            'data': {
                'tracking_number': 'FR12345678',
                'claim_reference': 'CLM-2024-TEST-02',
                'client_name': 'Shop & Co',
                'amount_requested': 50.00
            }
        }
    ]
    
    for case in test_cases:
        print(f"\n--- Testing Reason: {case['reason']} ---")
        try:
            result = generator.generate(case['data'], case['reason'])
            print("✅ Generation Successful")
            print(f"Preview (first 200 chars):\n{result[:200]}...")
        except Exception as e:
            print(f"❌ Generation Failed: {e}")

if __name__ == "__main__":
    test_appeal_generation()
