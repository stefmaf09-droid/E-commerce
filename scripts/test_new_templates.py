import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.notifications.email_sender import (
    EmailSender,
    send_claim_submitted_email,
    send_claim_accepted_email,
    send_claim_rejected_email,
    send_disputes_detected_email
)
from src.database.email_template_manager import EmailTemplateManager

# Load env variables
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(env_path)

def send_test_emails():
    # Retrieve configuration from .env
    smtp_host = os.getenv('SMTP_HOST', 'smtp.orange.fr')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    smtp_user = os.getenv('SMTP_USER')
    smtp_password = os.getenv('SMTP_PASSWORD')
    
    recipient = os.getenv('TEST_EMAIL_RECIPIENT', smtp_user)
    
    if not smtp_user or not smtp_password:
        print("❌ Identifiants SMTP manquants dans le fichier .env")
        return
        
    print(f"📧 Envoi des emails de test à {recipient} depuis {smtp_user}...")
    
    # Send 1: Claim Created
    print("1/4 Envoi: Nouvelle réclamation soumise...")
    success1 = send_claim_submitted_email(
        client_email=recipient,
        claim_reference="REF-TEST-001",
        carrier="Colissimo",
        amount_requested=125.50,
        order_id="CMD-12345",
        submission_method="api",
        dispute_type="Colis perdu"
    )
    print(f"   Résultat: {'✅ Succès' if success1 else '❌ Échec'}")
    
    # Send 2: Claim Accepted
    print("2/4 Envoi: Réclamation acceptée...")
    success2 = send_claim_accepted_email(
        client_email=recipient,
        claim_reference="REF-TEST-002",
        carrier="Chronopost",
        accepted_amount=150.00,
        client_share=120.00,
        platform_fee=30.00
    )
    print(f"   Résultat: {'✅ Succès' if success2 else '❌ Échec'}")
    
    # Send 3: Claim Rejected
    print("3/4 Envoi: Réclamation refusée...")
    success3 = send_claim_rejected_email(
        client_email=recipient,
        claim_reference="REF-TEST-003",
        carrier="Mondial Relay",
        rejection_reason="Le poids mesuré en agence (1.2kg) ne correspond pas au poids déclaré sur le bordereau d'expédition (0.8kg). Conformément aux conditions générales de vente, l'indemnisation est refusée en cas de fausse déclaration."
    )
    print(f"   Résultat: {'✅ Succès' if success3 else '❌ Échec'}")
    
    # Send 4: Disputes Detected
    print("4/4 Envoi: Nouveaux litiges détectés...")
    disputes = [
        {"order_id": "CMD-001", "carrier": "Colissimo", "dispute_type": "Retard de livraison", "total_recoverable": 15.0},
        {"order_id": "CMD-002", "carrier": "DHL", "dispute_type": "Colis perdu", "total_recoverable": 85.50},
        {"order_id": "CMD-003", "carrier": "Chronopost", "dispute_type": "Avarie de transport", "total_recoverable": 45.0}
    ]
    success4 = send_disputes_detected_email(
        client_email=recipient,
        disputes_count=12,
        total_amount=320.50,
        disputes_summary=disputes
    )
    print(f"   Résultat: {'✅ Succès' if success4 else '❌ Échec'}")
    
    print("\\n🎉 Tests terminés. Veuillez vérifier votre boîte mail.")

if __name__ == "__main__":
    send_test_emails()
