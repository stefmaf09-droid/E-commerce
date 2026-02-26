import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.email_service.email_sender import send_claim_submitted_email

def simulate_upload(extracted_text, filename):
    print(f"--- Simulating Upload for {filename} ---")
    
    text_lower = extracted_text.lower()
    detected_carrier = "Transporteur Inconnu"
    detected_status = 'Inconnu'
    confidence = 85.0
    
    if "dpd" in text_lower:
        detected_carrier = "DPD France"
        confidence += 10
    elif "chronopost" in text_lower:
        detected_carrier = "Chronopost"
        confidence += 10
    elif "colissimo" in text_lower or "la poste" in text_lower or "laposte" in text_lower:
        detected_carrier = "La Poste / Colissimo"
    elif "dhl" in text_lower:
        detected_carrier = "DHL Express"
    elif "ups" in text_lower or "1z" in extracted_text or "saver" in text_lower or "united parcel" in text_lower:
        detected_carrier = "UPS"
        confidence += 15
        
    if "signature" in text_lower and ("invalid" in text_lower or "rejet" in text_lower or "contest" in text_lower):
         detected_status = 'Contestation Signature'
    elif "endommag" in text_lower or "damaged" in text_lower or "reserve" in text_lower:
         detected_status = 'Colis Endommagé'
    elif "livr" in text_lower or "deliver" in text_lower:
         detected_status = 'Livré (Avec réserves potentielles)'
    else:
         detected_status = 'Dommage Visuel Suspecté'
         confidence = 92.0

    if "ups" in text_lower and "pak" in text_lower:
        detected_status = 'Emballage Déchiré / Ouvert'
        confidence = 96.5

    print(f"Detected Carrier: {detected_carrier}")
    print(f"Detected Status: {detected_status}")
    print(f"Confidence: {confidence}%")
    
    # Simulate email sending
    client_email = os.getenv("TEST_EMAIL_RECIPIENT", "test@example.com")
    amount = 85.00 if 'endommag' in detected_status.lower() or 'perte' in detected_status.lower() or 'ouvert' in detected_status.lower() else 12.50
    
    print(f"\n--- Sending simulated email to {client_email} ---")
    try:
        success = send_claim_submitted_email(
            client_email=client_email,
            claim_reference="CLM-SIMU-4882",
            carrier=detected_carrier,
            amount_requested=amount,
            order_id="ORD-SIMU-4882",
            submission_method="portal",
            dispute_type=detected_status
        )
        print(f"Email sent success: {success}")
    except Exception as e:
        print(f"Error sending email: {e}")

if __name__ == "__main__":
    # Based on the uploaded image which clearly says "UPS SAVER", "1Z W49 178 D9 2873 5710", "1 KG PAK"
    mock_extracted_text = "UPS SAVER TRACKING #: 1Z W49 178 D9 2873 5710 1 KG PAK FRA 060 7-00"
    filename = "ups_damaged_package.jpg"
    simulate_upload(mock_extracted_text, filename)
