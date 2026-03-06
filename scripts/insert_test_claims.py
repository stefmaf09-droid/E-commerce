import os
import sys
from dotenv import load_dotenv

# Add project root to path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, 'src'))

load_dotenv(os.path.join(root_dir, '.env'))

from src.database.database_manager import DatabaseManager

def create_test_claims():
    # Use Supabase (Test) database explicitly
    test_db_url = os.getenv('DATABASE_URL')
    print(f"Connecting to Test DB: {test_db_url[:20]}...")
    
    db = DatabaseManager()
    
    # We need the client_id for stephenrouxel22@orange.fr
    client = db.get_client("stephenrouxel22@orange.fr")
    if not client:
        print("Test client not found in DB. Creating...")
        client_id = db.create_client("stephenrouxel22@orange.fr", "Stephen Test")
    else:
        client_id = client['id']
        
    print(f"Using client_id: {client_id}")
    
    test_claims = [
        {
            "claim_reference": "REF-TEST-001",
            "order_id": "CMD-12345",
            "carrier": "Colissimo",
            "dispute_type": "lost",
            "amount_requested": 125.50,
            "status": "processing"
        },
        {
            "claim_reference": "REF-TEST-002",
            "order_id": "CMD-12346",
            "carrier": "Chronopost",
            "dispute_type": "delay",
            "amount_requested": 150.00,
            "status": "accepted",
            "accepted_amount": 150.00
        },
        {
            "claim_reference": "REF-TEST-003",
            "order_id": "CMD-12347",
            "carrier": "Mondial Relay",
            "dispute_type": "damaged",
            "amount_requested": 85.00,
            "status": "rejected",
            "rejection_reason": "Le poids mesuré en agence ne correspond pas."
        }
    ]
    
    for claim_data in test_claims:
        existing = db.get_claim(claim_reference=claim_data["claim_reference"])
        if existing:
            print(f"Claim {claim_data['claim_reference']} already exists. Updating...")
            db.update_claim(existing['id'], 
                status=claim_data['status'],
                accepted_amount=claim_data.get('accepted_amount'),
                rejection_reason=claim_data.get('rejection_reason')
            )
        else:
            db.create_claim(
                claim_reference=claim_data["claim_reference"],
                client_id=client_id,
                order_id=claim_data["order_id"],
                carrier=claim_data["carrier"],
                dispute_type=claim_data["dispute_type"],
                amount_requested=claim_data["amount_requested"],
                tracking_number=f"TRK-{claim_data['order_id']}"
            )
            
            # Update additional fields
            new_claim = db.get_claim(claim_reference=claim_data["claim_reference"])
            db.update_claim(new_claim['id'], 
                status=claim_data['status'],
                accepted_amount=claim_data.get('accepted_amount'),
                rejection_reason=claim_data.get('rejection_reason')
            )
            print(f"Created claim {claim_data['claim_reference']}")

if __name__ == "__main__":
    create_test_claims()
