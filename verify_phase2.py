
import os
import sys
import logging
from datetime import datetime

# Ajout du dossier racine au path
sys.path.append(os.getcwd())

from src.database.database_manager import DatabaseManager
from src.analytics.bypass_scorer import BypassScorer
from src.api.webhook_handler import WebhookHandler
from src.scrapers.ocr_processor import OCRProcessor
from src.reports.legal_document_generator import LegalDocumentGenerator

logging.basicConfig(level=logging.INFO)

def run_verification_phase2():
    print("=== 🧪 VÉRIFICATION PHASE 2 : IA & AUTOMATION ===")
    
    db_path = "database/verify_phase2.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    db = DatabaseManager(db_path=db_path, db_type="sqlite")

    # 1. Test Scoring IA
    print("\n[1] Testing AI Scoring...")
    client_id = db.create_client("ai_test@example.com", full_name="AI Tester")
    scorer = BypassScorer(db)
    
    # Simuler une alerte bypass
    conn = db.get_connection()
    conn.execute("INSERT INTO system_alerts (alert_type, severity, message, related_resource_type, related_resource_id) VALUES (?, ?, ?, ?, ?)",
                 ("bypass_detected", "high", "Bypass detected for test", "client", client_id))
    conn.commit()
    conn.close()
    
    risk_score = scorer.calculate_client_risk_score(client_id)
    label = scorer.get_client_trust_label(risk_score)
    print(f"✅ Risk Score: {risk_score} (Label: {label['label']})")
    
    success_prob = scorer.estimate_success_probability("Colissimo", "lost")
    print(f"✅ Success Probability (Colissimo/lost): {success_prob * 100}%")

    # 2. Test Webhooks
    print("\n[2] Testing Webhooks...")
    wh = WebhookHandler(db)
    
    # Créer un dossier à suivre
    claim_id = db.create_claim("TRK-WH-TEST", client_id, "ORD-WH", "UPS", "damaged", 100.0, tracking_number="UPS123456")
    
    payload = {
        "msg": {
            "tracking_number": "UPS123456",
            "tag": "Lost"
        }
    }
    success = wh.handle_tracking_update(payload)
    
    conn = db.get_connection()
    updated_claim = conn.execute("SELECT status, automation_status FROM claims WHERE id = ?", (claim_id,)).fetchone()
    conn.close()
    print(f"✅ Webhook Processed: {success}")
    print(f"✅ Claim Status Updated: {updated_claim[0]} / {updated_claim[1]}")

    # 3. Test OCR Analysis
    print("\n[3] Testing OCR Analysis...")
    ocr = OCRProcessor()
    rejection_text = "The carrier has verified the weight and it matches the departure record."
    analysis = ocr.analyze_rejection_text(rejection_text)
    print(f"✅ OCR Detection: {analysis['label_fr']} ({analysis['reason_key']})")
    print(f"✅ Advice: {analysis['advice_fr'][:50]}...")

    # 4. Test US State-specific Legal Docs
    print("\n[4] Testing US State-specific PDF...")
    generator = LegalDocumentGenerator()
    
    states_to_test = [
        {"ref": "CLM-NY", "addr": "123 Broadway, New York, NY 10001", "name": "NY"},
        {"ref": "CLM-CA", "addr": "456 Sunset Blvd, Los Angeles, CA 90028", "name": "CA"},
        {"ref": "CLM-TX", "addr": "789 Main St, Houston, TX 77002", "name": "TX"},
        {"ref": "CLM-FL", "addr": "101 Ocean Dr, Miami, FL 33139", "name": "FL (Fallback)"}
    ]
    
    for state in states_to_test:
        claim_data = {
            "claim_reference": state['ref'],
            "carrier": "UPS",
            "dispute_type": "Lost",
            "amount_requested": 250.0,
            "currency": "USD",
            "delivery_address": state['addr']
        }
        path = generator.generate_formal_notice(claim_data, lang='EN', output_dir="data/verify_docs")
        print(f"✅ Generated {state['name']} PDF: {os.path.basename(path)}")
        
        # Vérification sommaire du contenu (on cherche un mot clé spécifique dans le PDF si possible, mais ici on valide la création)
        if os.path.exists(path):
            print(f"   - File exists: {path}")

    print("\n=== ✨ VÉRIFICATION PHASE 2 TERMINÉE ===")

if __name__ == "__main__":
    run_verification_phase2()
