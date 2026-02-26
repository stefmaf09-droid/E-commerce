
import os
import sys
import time
from datetime import datetime
import logging
from dotenv import load_dotenv

# Add root to path
sys.path.append(os.getcwd())

from src.database.database_manager import get_db_manager
from src.scrapers.ocr_processor import OCRProcessor
from src.reports.legal_document_generator import LegalDocumentGenerator
from src.email_service.email_sender import EmailSender
from src.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_comprehensive_test():
    logger.info("=" * 80)
    logger.info("🚀 STARTING COMPREHENSIVE CLIENT JOURNEY TEST")
    logger.info("=" * 80)

    # 1. Load Config & Credentials
    load_dotenv()
    db_manager = get_db_manager()
    ocr = OCRProcessor()
    legal_gen = LegalDocumentGenerator()
    
    # Email Sender Configuration from .env
    sender = EmailSender(
        smtp_host=os.getenv('SMTP_HOST', 'smtp.gmail.com'),
        smtp_port=int(os.getenv('SMTP_PORT', 587)),
        smtp_user=os.getenv('SMTP_USER'),
        smtp_password=os.getenv('SMTP_PASSWORD'),
        from_email=os.getenv('SMTP_USER'),
        from_name="Agent IA Recouvrement (TEST)"
    )

    client_email = os.getenv('TEST_EMAIL_RECIPIENT', 'stephenrouxel22@orange.fr')
    client_name = "Stephen Rouxel (TEST)"

    # Ensure client exists in DB
    client = db_manager.get_client(email=client_email)
    if not client:
        client_id = db_manager.create_client(email=client_email, full_name=client_name)
    else:
        client_id = client['id']
    
    db_manager.update_client(client_id, subscription_tier='platinum')
    
    # Reload client data
    client = db_manager.get_client(email=client_email)
    client_id = client['id']
    logger.info(f"✅ Client test configuré : {client_name} ({client_email}) - ID: {client_id}")

    # SCENARIOS
    scenarios = [
        {
            "carrier": "Colissimo",
            "filename": "preuve_colis_dommage_colissimo.jpg",
            "status": "Colis Endommagé",
            "type": "Damage",
            "amount": 45.0
        },
        {
            "carrier": "UPS",
            "filename": "screenshot_tracking_ups_late.png",
            "status": "En retard",
            "type": "Late Delivery",
            "amount": 12.50
        },
        {
            "carrier": "DHL",
            "filename": "rejet_signature_dhl.pdf",
            "status": "Contestation Signature",
            "type": "Lost/Theft",
            "amount": 250.0
        }
    ]

    for scenario in scenarios:
        logger.info(f"\n🔹 TEST SCENARIO : {scenario['carrier']} - {scenario['status']}")
        
        # 2. Simulate OCR Analysis
        logger.info(f"Step 2: Simulation de l'analyse OCR pour {scenario['filename']}...")
        # Mock extracted text based on filename as OCRProcessor.simulate_ocr_on_file does
        extracted_text = ocr.simulate_ocr_on_file(scenario['filename'])
        logger.info(f"   [OCR Result] : {extracted_text[:100]}...")

        # 3. Create Dispute in Database
        logger.info(f"Step 3: Création du litige en base de données...")
        tracking_number = f"TRK-{scenario['carrier'][:3].upper()}-{int(time.time()) % 10000}"
        claim_ref = f"CLM-{tracking_number[-4:]}"
        
        claim_id = db_manager.create_dispute(
            client_id=client_id,
            order_id=f"ORD-{int(time.time()) % 1000}",
            carrier=scenario['carrier'],
            dispute_type=scenario['type'],
            amount_recoverable=scenario['amount'],
            tracking_number=tracking_number,
            order_date=datetime.now().strftime("%Y-%m-%d"),
            expected_delivery_date=datetime.now().strftime("%Y-%m-%d"),
            success_probability=85,
            predicted_days_to_recovery=14
        )
        logger.info(f"   ✅ Litige créé avec ID : {claim_id} (Ref: {claim_ref})")

        # 4. Generate "Mise en Demeure" PDF
        logger.info(f"Step 4: Génération de la Mise en Demeure (PDF)...")
        claim_data = {
            'claim_reference': claim_ref,
            'tracking_number': tracking_number,
            'amount_requested': scenario['amount'],
            'currency': 'EUR',
            'dispute_type': scenario['status'],
            'customer_name': client_name,
            'delivery_address': '85 Rue du Commandeur, 75014 Paris',
            'carrier': scenario['carrier']
        }
        
        output_dir = os.path.join(os.getcwd(), 'data', 'legal_docs', 'TEST')
        os.makedirs(output_dir, exist_ok=True)
        pdf_path = legal_gen.generate_formal_notice(claim_data, lang='FR', output_dir=output_dir)
        logger.info(f"   ✅ PDF généré : {pdf_path}")

        # 5. Send Notification Email to Client
        logger.info(f"Step 5: Envoi de la notification au client ({client_email})...")
        email_sent = sender.send_claim_submitted_email(
            to_email=client_email,
            client_name=client_name,
            claim_reference=claim_ref,
            carrier=scenario['carrier'],
            amount_requested=scenario['amount'],
            order_id=f"ORD-{int(time.time()) % 1000}",
            submission_method="Portal/Hybrid AI",
            dispute_type=scenario['status']
        )
        if email_sent:
            logger.info("   ✅ Email de notification client envoyé.")
        else:
            logger.warning("   ❌ Échec de l'envoi de l'email client (Voir logs SMTP).")

        # 6. Send Formal Claim to Carrier (Simulated Carrier Email)
        logger.info(f"Step 6: Envoi de la réclamation formelle au transporteur (Simulation)...")
        test_carrier_email = client_email # Redirecting to self for testing
        carrier_subject = f"RÉCLAMATION FORMELLE - {scenario['carrier']} - Suivi {tracking_number}"
        carrier_body = f"""
        Bonjour service client {scenario['carrier']},
        
        Veuillez trouver ci-joint une Mise en Demeure concernant le colis {tracking_number}.
        Nature du litige : {scenario['status']}
        Montant réclamé : {scenario['amount']} EUR
        
        Cordialement,
        Bureau Juridique Recours E-commerce
        """
        
        carrier_email_sent = sender.send_claim_to_carrier(
            carrier_email=test_carrier_email,
            claim_reference=claim_ref,
            tracking_number=tracking_number,
            subject=carrier_subject,
            body=carrier_body,
            attachments=[pdf_path]
        )
        if carrier_email_sent:
            logger.info(f"   ✅ Réclamation envoyée au transporteur ({test_carrier_email}) avec PJ.")
        else:
            logger.warning("   ❌ Échec de l'envoi au transporteur.")

        time.sleep(2) # Prevent SMTP spamming too fast

    logger.info("\n" + "=" * 80)
    logger.info("✅ TEST COMPLET TERMINÉ")
    logger.info(f"Vérifiez votre boîte mail ({client_email}) pour les notifications et réclamations.")
    logger.info("=" * 80)

if __name__ == "__main__":
    run_comprehensive_test()
