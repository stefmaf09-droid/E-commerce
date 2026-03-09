import psycopg2
import uuid
import random
from datetime import datetime, timedelta

NEON_URL = 'postgresql://neondb_owner:npg_fJ5tC4sdDjcx@ep-little-pond-al8y4ngw-pooler.c-3.eu-central-1.aws.neon.tech/neondb?sslmode=require'

def generate_mock_data():
    try:
        conn = psycopg2.connect(NEON_URL)
        cur = conn.cursor()
        
        email = 'stephenrouxel22@orange.fr'
        cur.execute("SELECT id FROM clients WHERE email = %s", (email,))
        client = cur.fetchone()
        if not client:
            cur.execute("INSERT INTO clients (email, full_name) VALUES (%s, %s) RETURNING id", (email, "Stephen Test Admin"))
            client_id = cur.fetchone()[0]
        else:
            client_id = client[0]

        carriers = ['Chronopost', 'Colissimo', 'Mondial Relay', 'DHL', 'UPS', 'FedEx']
        dispute_types = ['lost_package', 'delayed_delivery', 'damaged_package', 'invalid_pod']
        statuses = ['pending', 'processing', 'under_review', 'accepted', 'rejected', 'resolved']

        claims = []
        for i in range(1, 31): # 30 test claims
            c_ref = f"REF-DEMO-{str(uuid.uuid4())[:8].upper()}"
            carrier = random.choice(carriers)
            d_type = random.choice(dispute_types)
            status = random.choice(statuses)
            amount = round(random.uniform(20.0, 300.0), 2)
            acc_amt = amount if status in ('accepted', 'resolved') else None
            rej_reason = "Le colis été livré correctement" if status == 'rejected' else None
            
            # Always have a few specific claims for each carrier to guarantee they show up
            claims.append((c_ref, client_id, f"CMD-D-{i}", carrier, d_type, amount, status, acc_amt, rej_reason, f"TRK-{carrier[:3]}-{i}"))

        # Guarantee at least one Chronopost claim exists!
        claims.append(("REF-CHRONO-GUARANTEE", client_id, "CMD-CHRONO", "Chronopost", "delayed_delivery", 100.0, "processing", None, None, "TRK-CHRONO-999"))

        inserted = 0
        for data in claims:
            cur.execute("SELECT id FROM claims WHERE claim_reference = %s", (data[0],))
            if not cur.fetchone():
                cur.execute("""
                    INSERT INTO claims (claim_reference, client_id, order_id, carrier, dispute_type, amount_requested, status, accepted_amount, rejection_reason, tracking_number)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, data)
                inserted += 1
                
        conn.commit()
        print(f"✅ Successfully inserted {inserted} mock claims into Neon DB for {email}.")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    generate_mock_data()
