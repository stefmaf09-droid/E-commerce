"""
Script de création de données de démo — Commande Back Market #78177171
Xiaomi Redmi Note 14 4G 128Go - Noir - Débloqué
Commandée le 09/03/2026, livraison prévue 10/03/2026
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.database_manager import DatabaseManager
from datetime import datetime, date, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                       "data", "test_recours_ecommerce.db")

db = DatabaseManager(db_path=DB_PATH, db_type="sqlite")

# 1. Créer ou récupérer client
email = "marchand@backmarket-demo.fr"
client = db.get_client(email=email)
client_id = client['id'] if client else db.create_client(
    email=email,
    full_name="Sophie Martin",
    company_name="TechRefurb Pro"
)
print(f"✅ Client: {email} (id={client_id})")

# 2. Créer la réclamation Back Market
claims_to_create = [
    {
        "ref": "REF-BKM-78177171",
        "order_id": "BKM-78177171",
        "carrier": "Colissimo",
        "type": "delayed",
        "amount": 289.00,
        "tracking": "6C21020020247050",
        "status": "processing",
        "note": "Xiaomi Redmi Note 14 4G 128Go - Commande Back Market - Livraison non confirmée à la date prévue"
    },
    {
        "ref": "REF-BKM-78099342",
        "order_id": "BKM-78099342",
        "carrier": "Chronopost",
        "type": "lost",
        "amount": 156.50,
        "tracking": "CP567890123FR",
        "status": "submitted",
        "note": "iPhone 13 reconditionné - Colis perdu"
    },
    {
        "ref": "REF-BKM-77654321",
        "order_id": "BKM-77654321",
        "carrier": "Colissimo",
        "type": "damaged",
        "amount": 220.00,
        "tracking": "6C21099988877650",
        "status": "accepted",
        "note": "Samsung Galaxy S22 - Colis endommagé à la livraison",
    },
]

for c in claims_to_create:
    # Check if already exists
    existing = db.get_claim(claim_reference=c["ref"])
    if not existing:
        claim_id = db.create_claim(
            claim_reference=c["ref"],
            client_id=client_id,
            order_id=c["order_id"],
            carrier=c["carrier"],
            dispute_type=c["type"],
            amount_requested=c["amount"],
            tracking_number=c["tracking"],
            customer_name="Back Market Client",
            delivery_address="Paris, France"
        )
        # Update status
        db.update_claim(claim_id=claim_id, status=c["status"])
        if c["status"] == "accepted":
            db.update_claim(claim_id=claim_id, accepted_amount=c["amount"] * 0.9)
        print(f"  ✅ Créé: {c['ref']} ({c['carrier']}, {c['type']}, {c['amount']}€, status={c['status']})")
    else:
        print(f"  ⏭️  Existant: {c['ref']}")

print("\n✅ Données Back Market créées. Lancez l'app et connectez-vous avec :")
print(f"   Email    : {email}")
print(f"   Mot de passe : backmarket123 (si configuré)")
print(f"\n   Ou accédez directement : http://localhost:8501?token={email}&portal=true")
