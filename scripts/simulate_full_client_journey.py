"""
Simulation complete du circuit client - complement au parcours reel deja effectue
via l'UI (inscription + upload de 5 preuves reelles + OCR + email de confirmation
par preuve, deja envoyes).

Ce script complete le circuit avec les etapes qui ne passent PAS par l'UI de depot
de preuves :
  1. Un email recapitulatif "nouveaux litiges detectes" (disputes_detected).
  2. La reclamation formelle (Mise en Demeure PDF) envoyee au transporteur pour
     chacun des 5 types de litiges (claim_to_carrier), redirigee vers l'adresse
     de test pour ne rien envoyer a un vrai transporteur.
  3. Deux emails de dénouement (claim_accepted / claim_rejected) pour montrer le
     cycle de vie complet d'un dossier.

Les emails "reclamation soumise" (claim_submitted) par preuve ont deja ete
envoyes par l'application elle-meme lors de l'upload reel via l'onglet
"Depot Preuves" -> ce script ne les renvoie pas, pour eviter les doublons.
"""
import os
import sys
import time
from datetime import datetime
import logging
from dotenv import load_dotenv

sys.path.append(os.getcwd())

from src.database.database_manager import get_db_manager
from src.reports.legal_document_generator import LegalDocumentGenerator
from src.email_service.email_sender import EmailSender
from src.payments.manual_payment_manager import ManualPaymentManager
from src.config import Config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def run_full_journey():
    logger.info("=" * 80)
    logger.info("SIMULATION COMPLETE DU CIRCUIT CLIENT (complement post-upload UI)")
    logger.info("=" * 80)

    load_dotenv()
    db_manager = get_db_manager()
    legal_gen = LegalDocumentGenerator()

    sender = EmailSender(
        smtp_host=os.getenv('SMTP_HOST', 'smtp.gmail.com'),
        smtp_port=int(os.getenv('SMTP_PORT', 587)),
        smtp_user=os.getenv('SMTP_USER'),
        smtp_password=os.getenv('SMTP_PASSWORD'),
        from_email=os.getenv('SMTP_USER'),
        from_name="Refundly.AI (SIMULATION)"
    )

    client_email = os.getenv('TEST_EMAIL_RECIPIENT', 'stefmaf09@gmail.com')
    client_name = "Client Simulation (stefmaf09)"

    client = db_manager.get_client(email=client_email)
    if not client:
        client_id = db_manager.create_client(email=client_email, full_name=client_name)
        client = db_manager.get_client(email=client_email)
    client_id = client['id']
    logger.info(f"Client cible : {client_name} ({client_email}) - ID: {client_id}")

    # Les 5 memes scenarios que les 5 preuves deja televersees via l'UI reelle,
    # couvrant les 5 regles du moteur de detection (dispute_detector.py).
    scenarios = [
        {
            "rule": "express_delay",
            "carrier": "DHL Express",
            "status": "Retard Service Express",
            "type": "Late Delivery",
            "amount": 18.90,
        },
        {
            "rule": "package_lost",
            "carrier": "Chronopost",
            "status": "Colis Perdu",
            "type": "Lost/Theft",
            "amount": 250.0,
        },
        {
            "rule": "invalid_pod",
            "carrier": "Colissimo",
            "status": "Preuve de Livraison Invalide",
            "type": "Damage",
            "amount": 62.50,
        },
        {
            "rule": "standard_delay",
            "carrier": "La Poste",
            "status": "Retard Significatif Standard",
            "type": "Late Delivery",
            "amount": 9.40,
        },
        {
            "rule": "wrong_gps",
            "carrier": "UPS",
            "status": "GPS Incoherent",
            "type": "Lost/Theft",
            "amount": 45.00,
        },
    ]

    total_amount = sum(s["amount"] for s in scenarios)

    # --- 1. Email recapitulatif des litiges detectes ---------------------------
    logger.info("Etape 1 : envoi de l'email recapitulatif (disputes_detected)...")
    disputes_summary = [
        {"carrier": s["carrier"], "type": s["status"], "amount": s["amount"]}
        for s in scenarios
    ]
    ok = sender.send_disputes_detected_email(
        to_email=client_email,
        client_name=client_name,
        disputes_count=len(scenarios),
        total_amount=total_amount,
        disputes_summary=disputes_summary,
    )
    logger.info("   OK" if ok else "   ECHEC")
    time.sleep(2)

    outcomes = ["accepted", "rejected", None, None, None]  # 1er accepte, 2e refuse, reste en attente

    for scenario, outcome in zip(scenarios, outcomes):
        logger.info(f"\nScenario : {scenario['carrier']} - {scenario['status']}")

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
        logger.info(f"   Litige cree en base (ID: {claim_id}, Ref: {claim_ref})")

        # Reprend le nom de la boutique et, si le client a renseigne son IBAN
        # via l'onboarding, ses coordonnees bancaires reelles -> le PDF affiche
        # alors de vraies modalites de reglement au lieu d'un texte generique.
        bank_info = ManualPaymentManager().get_client_bank_info(client_email)
        claim_data = {
            'claim_reference': claim_ref,
            'tracking_number': tracking_number,
            'amount_requested': scenario['amount'],
            'currency': 'EUR',
            'dispute_type': scenario['status'],
            'customer_name': client_name,
            'delivery_address': '85 Rue du Commandeur, 75014 Paris',
            'carrier': scenario['carrier'],
            'company_name': client_name,
            'contact_email': os.getenv('SMTP_USER'),
        }
        if bank_info:
            claim_data['iban'] = bank_info.get('iban')
            claim_data['bic'] = bank_info.get('bic')
            claim_data['account_holder_name'] = bank_info.get('account_holder_name')
        output_dir = os.path.join(os.getcwd(), 'data', 'legal_docs', 'SIMULATION')
        os.makedirs(output_dir, exist_ok=True)
        pdf_path = legal_gen.generate_formal_notice(claim_data, lang='FR', output_dir=output_dir)
        logger.info(f"   PDF genere : {pdf_path}")

        # Reclamation formelle au transporteur, redirigee vers l'adresse de test.
        carrier_subject = f"RECLAMATION FORMELLE - {scenario['carrier']} - Suivi {tracking_number}"
        carrier_body = f"""
        Bonjour service client {scenario['carrier']},

        Veuillez trouver ci-joint une Mise en Demeure concernant le colis {tracking_number}.
        Nature du litige : {scenario['status']}
        Montant reclame : {scenario['amount']} EUR

        Cordialement,
        Bureau Juridique Refundly.AI
        """
        carrier_email_sent = sender.send_claim_to_carrier(
            carrier_email=client_email,
            claim_reference=claim_ref,
            tracking_number=tracking_number,
            subject=carrier_subject,
            body=carrier_body,
            attachments=[pdf_path]
        )
        logger.info("   Email transporteur (avec PJ) : " + ("OK" if carrier_email_sent else "ECHEC"))
        time.sleep(2)

        if outcome == "accepted":
            accepted_amount = scenario['amount']
            client_share = round(accepted_amount * 0.8, 2)
            platform_fee = round(accepted_amount * 0.2, 2)
            ok = sender.send_claim_accepted_email(
                to_email=client_email,
                client_name=client_name,
                claim_reference=claim_ref,
                carrier=scenario['carrier'],
                accepted_amount=accepted_amount,
                client_share=client_share,
                platform_fee=platform_fee,
            )
            logger.info("   Email 'reclamation acceptee' : " + ("OK" if ok else "ECHEC"))
            time.sleep(2)
        elif outcome == "rejected":
            ok = sender.send_claim_rejected_email(
                to_email=client_email,
                client_name=client_name,
                claim_reference=claim_ref,
                carrier=scenario['carrier'],
                rejection_reason="Preuve de livraison jugee conforme par le transporteur apres contre-enquete.",
            )
            logger.info("   Email 'reclamation refusee' : " + ("OK" if ok else "ECHEC"))
            time.sleep(2)

    logger.info("\n" + "=" * 80)
    logger.info("SIMULATION TERMINEE")
    logger.info(f"Verifiez la boite mail ({client_email}) pour l'ensemble des notifications.")
    logger.info("=" * 80)


if __name__ == "__main__":
    run_full_journey()
