import os
import sys
from email.message import EmailMessage
from email.policy import default

# Path setup
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

from src.scrapers.ocr_processor import OCRProcessor

def create_sample_eml(file_path):
    msg = EmailMessage()
    msg['Subject'] = "Rejet de réclamation - Signature non conforme"
    msg['From'] = "support@carrier.com"
    msg['To'] = "merchant@shop.fr"
    msg.set_content("Nous rejetons votre réclamation car la signature ne correspond pas au bordereau.")
    
    # Add a dummy attachment
    msg.add_attachment(
        b"fake image data", 
        maintype='image',
        subtype='png',
        filename='evidence_photo.png'
    )
    
    with open(file_path, 'wb') as f:
        f.write(msg.as_bytes(policy=default))
    return file_path

def test_eml_parsing():
    processor = OCRProcessor()
    test_eml = os.path.join(root_dir, 'data', 'test_sample.eml')
    os.makedirs(os.path.dirname(test_eml), exist_ok=True)
    
    create_sample_eml(test_eml)
    
    try:
        print(f"Testing EML parsing on: {test_eml}")
        text, attachments = processor.extract_all_from_file(test_eml, "test_sample.eml")
        
        print(f"Extracted Text: {text.strip()}")
        print(f"Attachments found: {len(attachments)}")
        
        assert "signature ne correspond pas" in text
        assert len(attachments) == 1
        assert attachments[0]['filename'] == 'evidence_photo.png'
        
        # Test Analysis
        analysis = processor.analyze_rejection_text(text)
        print(f"Analysis Result: {analysis['label_fr']}")
        assert analysis['reason_key'] == 'bad_signature'
        
        print("✅ EML Parsing Test PASSED")
    finally:
        if os.path.exists(test_eml):
            os.remove(test_eml)

if __name__ == "__main__":
    test_eml_parsing()
