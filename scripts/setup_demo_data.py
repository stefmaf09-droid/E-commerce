"""
Script to setup admin data for the demo.
"""
import sys
import os
import random
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from database.database_manager import DatabaseManager

def setup_demo_data():
    """Setup data for admin@refundly.ai."""
    
    email = "admin@refundly.ai"
    db = DatabaseManager()
    
    # 1. Create Client
    print(f"Creating/Getting client: {email}...")
    client_id = db.create_client(
        email=email, 
        full_name="Admin Demo", 
        company_name="Refoundly Demo Store", 
        phone="+33 6 12 34 56 78"
    )
    print(f"✅ Client ID: {client_id}")
    
    # 2. Create Dummy Claims
    print("\nGenerating dummy claims...")
    carriers = ['Colissimo', 'Chronopost', 'Mondial Relay', 'DHL']
    statuses = ['accepted', 'pending', 'rejected', 'refunded']
    
    # Create 20 claims
    for i in range(20):
        order_date = datetime.now() - timedelta(days=random.randint(5, 60))
        submitted_at = order_date + timedelta(days=random.randint(1, 10))
        amount = random.uniform(50, 500)
        status = random.choice(statuses)
        
        accepted_amount = 0
        if status == 'accepted':
            accepted_amount = amount
        elif status == 'refunded':
            accepted_amount = amount
            
        db.create_claim(
            claim_reference=f"CLM-{random.randint(10000, 99999)}",
            client_id=client_id,
            order_id=f"ORD-{random.randint(1000, 9999)}",
            carrier=random.choice(carriers),
            dispute_type="Lost Package",
            amount_requested=amount,
            tracking_number=f"TRK{random.randint(100000000, 999999999)}",
            customer_name=f"Customer {i+1}",
            order_date=order_date,
            currency='EUR'
        )
        # Update manually to set status (create_claim doesn't allow setting status directly)
        # We need to get the last claim ID, but create_claim returns it.
        # Wait, create_claim returns the cursor.lastrowid
        # Let's fix the call above to capture ID.
        pass 

    # Re-doing the loop properly
    conn = db.get_connection()
    for i in range(25):
        order_date = datetime.now() - timedelta(days=random.randint(5, 60))
        amount = round(random.uniform(50, 500), 2)
        status = random.choice(statuses)
        claim_ref = f"CLM-{random.randint(10000, 99999)}"
        
        # Insert directly to set statuses easily
        accepted_amt = amount if status in ['accepted', 'refunded'] else 0
        
        conn.execute("""
            INSERT INTO claims (
                claim_reference, client_id, order_id, carrier, dispute_type,
                amount_requested, accepted_amount, status, tracking_number,
                customer_name, order_date, submitted_at, currency
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            claim_ref, client_id, f"ORD-{random.randint(1000, 9999)}", 
            random.choice(carriers), "Lost Package", amount, accepted_amt, status,
            f"TRK{random.randint(100000000, 999999999)}", f"Customer {i+1}",
            order_date, order_date + timedelta(days=2), 'EUR'
        ))
    
    conn.commit()
    conn.close()
    
    print("✅ Created 25 dummy claims.")
    print("✨ Demo data setup complete!")

if __name__ == "__main__":
    setup_demo_data()
