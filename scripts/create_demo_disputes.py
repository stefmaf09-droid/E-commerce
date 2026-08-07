"""Create demo disputes and claims for testing."""
import sys
import os
from datetime import datetime, timedelta
import random

sys.path.insert(0, 'src')

from database.database_manager import DatabaseManager

# Force SQLite database
db = DatabaseManager(db_path='data/test_recours_ecommerce.db', db_type='sqlite')

def create_demo_disputes(email: str, num_disputes: int = 10):
    """Create demo disputes for a client."""
    print(f"🔍 Looking for client: {email}")
    client = db.get_client(email=email)
    
    if not client:
        print(f"❌ Client not found: {email}")
        print("\n💡 Creating client...")
        client_id = db.create_client(email, company_name=f"Test Company for {email}")
        print(f"✅ Client created with ID: {client_id}")
    else:
        client_id = client['id']
        print(f"✅ Client found with ID: {client_id}")
    
    carriers = ['Chronopost', 'UPS', 'DHL', 'FedEx', 'Colissimo', 'DPD', 'GLS']
    dispute_types = ['lost', 'damaged', 'late']
    statuses = ['pending', 'submitted', 'accepted', 'rejected', 'under_review']
    
    print(f"\n📦 Creating {num_disputes} demo disputes...")
    
    for i in range(1, num_disputes + 1):
        base_date = datetime.now() - timedelta(days=random.randint(1, 60))
        
        claim_ref = f"CLM-{random.randint(10000, 99999)}"
        carrier = random.choice(carriers)
        dispute_type = random.choice(dispute_types)
        amount = round(random.uniform(30, 350), 2)
        status = random.choice(statuses)
        
        try:
            claim_id = db.create_claim(
                client_id=client_id,
                claim_reference=claim_ref,
                order_id=f"ORD-{random.randint(1000, 9999)}",
                carrier=carrier,
                dispute_type=dispute_type,
                amount_requested=amount,
                currency='EUR',
                tracking_number=f"TRK{random.randint(100000000, 999999999)}",
                customer_name=f"Client Test {i}",
                delivery_address=f"{i} Rue de Demo, 7500{random.randint(1,8)} Paris",
                order_date=(base_date - timedelta(days=random.randint(5, 15))).isoformat()
            )
            
            # Update status
            payment_status = 'paid' if status == 'accepted' else 'unpaid'
            accepted_amount = amount if status == 'accepted' else None
            
            db.update_claim(
                claim_id,
                status=status,
                payment_status=payment_status,
                accepted_amount=accepted_amount,
                submitted_at=base_date.isoformat()
            )
            
            dispute_emoji = {
                'lost': '📦❌',
                'damaged': '📦💥', 
                'late': '📦⏰'
            }
            
            status_emoji = {
                'pending': '⏳',
                'submitted': '✉️',
                'accepted': '✅',
                'rejected': '❌',
                'under_review': '🔍'
            }
            
            print(f"   {dispute_emoji.get(dispute_type, '📦')} {status_emoji.get(status, '•')} {claim_ref}: {carrier} | {dispute_type} | {amount}€ | {status}")
            
        except Exception as e:
            print(f"   ⚠️ Erreur pour {claim_ref}: {e}")
    
    print(f"\n{'='*60}")
    print("✨ Litiges créés avec succès !")
    print(f"{'='*60}")
    print(f"Client: {email}")
    print(f"Nombre de litiges: {num_disputes}")
    print(f"URL: http://localhost:8501")
    print(f"{'='*60}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        email = sys.argv[1]
        num = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    else:
        email = input("📧 Email du client: ")
        num = 10
    
    create_demo_disputes(email, num)
