"""
Script pour créer des données de test pour la démo du chatbot.
"""
import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.database_manager import get_db_manager
from datetime import datetime, timedelta
import random

def create_demo_data():
    """Crée un compte de démo avec plusieurs réclamations pour tester le chatbot."""
    db = get_db_manager()
    
    # Email de test
    demo_email = "chatbot.demo@refundly.ai"
    
    # Vérifier si le client existe déjà
    existing_client = db.get_client(email=demo_email)
    
    if existing_client:
        print(f"✅ Client {demo_email} existe déjà (ID: {existing_client['id']})")
        client_id = existing_client['id']
    else:
        # Créer le client
        client = db.create_client(
            email=demo_email,
            full_name="Démo Chatbot",
            company_name="Refundly Demo Store",
            phone="+33612345678"
        )
        client_id = client['id']
        print(f"✅ Client créé : {demo_email} (ID: {client_id})")
    
    # Créer des réclamations variées
    carriers = ["Colissimo", "Chronopost", "UPS", "DHL", "FedEx"]
    dispute_types = ["lost", "damaged", "late_delivery", "invalid_pod"]
    statuses = ["pending", "submitted", "under_review", "accepted", "rejected"]
    
    claims_data = [
        {
            "carrier": "Colissimo",
            "dispute_type": "lost",
            "amount": 125.50,
            "status": "accepted",
            "order_id": "ORDER-2024-001"
        },
        {
            "carrier": "Chronopost", 
            "dispute_type": "damaged",
            "amount": 89.00,
            "status": "accepted",
            "order_id": "ORDER-2024-002"
        },
        {
            "carrier": "UPS",
            "dispute_type": "late_delivery",
            "amount": 215.75,
            "status": "pending",
            "order_id": "ORDER-2024-003"
        },
        {
            "carrier": "DHL",
            "dispute_type": "lost",
            "amount": 450.00,
            "status": "under_review",
            "order_id": "ORDER-2024-004"
        },
        {
            "carrier": "Colissimo",
            "dispute_type": "invalid_pod",
            "amount": 67.30,
            "status": "accepted",
            "order_id": "ORDER-2024-005"
        },
        {
            "carrier": "FedEx",
            "dispute_type": "lost",
            "amount": 198.90,
            "status": "rejected",
            "order_id": "ORDER-2024-006"
        },
    ]
    
    print("\n📦 Création des réclamations...")
    created_count = 0
    
    for idx, claim_data in enumerate(claims_data, 1):
        # Générer référence
        date_str = datetime.now().strftime("%Y%m%d")
        claim_ref = f"CLM-{date_str}-{idx:03d}"
        
        # Vérifier si existe déjà
        existing = db.get_claim(claim_reference=claim_ref)
        if existing:
            print(f"  ⏭️  {claim_ref} existe déjà")
            continue
        
        # Créer la réclamation
        claim = db.create_claim(
            claim_reference=claim_ref,
            client_id=client_id,
            order_id=claim_data["order_id"],
            carrier=claim_data["carrier"],
            dispute_type=claim_data["dispute_type"],
            amount_requested=claim_data["amount"],
            status=claim_data["status"],
            tracking_number=f"TRACK{random.randint(100000, 999999)}"
        )
        
        # Simuler dates et montants pour les acceptées
        if claim_data["status"] == "accepted":
            db.update_claim(
                claim['id'],
                accepted_amount=claim_data["amount"],
                payment_status="paid",
                payment_date=(datetime.now() - timedelta(days=random.randint(1, 30))).isoformat()
            )
        
        print(f"  ✅ {claim_ref} - {claim_data['carrier']} - {claim_data['amount']} EUR ({claim_data['status']})")
        created_count += 1
    
    print(f"\n✅ {created_count} réclamation(s) créée(s)")
    print(f"\n🔐 Credentials pour la démo:")
    print(f"   Email: {demo_email}")
    print(f"   Mot de passe: demo123")
    print(f"\n🚀 Lancez l'application et connectez-vous avec ces identifiants !")

if __name__ == "__main__":
    create_demo_data()
