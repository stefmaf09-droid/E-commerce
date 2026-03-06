import os
import sys
import psycopg2
from datetime import datetime

# Database Neon URL
NEON_URL = 'postgresql://neondb_owner:npg_fJ5tC4sdDjcx@ep-little-pond-al8y4ngw-pooler.c-3.eu-central-1.aws.neon.tech/neondb?sslmode=require'

def insert_test_data():
    try:
        conn = psycopg2.connect(NEON_URL)
        cur = conn.cursor()
        
        # Get client_id for the test email
        email = 'stephenrouxel22@orange.fr'
        cur.execute("SELECT id FROM clients WHERE email = %s", (email,))
        client = cur.fetchone()
        
        if not client:
            print(f"❌ Client {email} not found. Creating...")
            cur.execute("INSERT INTO clients (email, full_name) VALUES (%s, %s) RETURNING id", (email, "Stephen Test"))
            client_id = cur.fetchone()[0]
        else:
            client_id = client[0]
            
        print(f"Using client_id: {client_id}")
        
        test_claims = [
            ("REF-TEST-001", "CMD-12345", "Colissimo", "lost", 125.50, "processing", None, None),
            ("REF-TEST-002", "CMD-12346", "Chronopost", "delay", 150.00, "accepted", 150.00, None),
            ("REF-TEST-003", "CMD-12347", "Mondial Relay", "damaged", 85.00, "rejected", None, "Poids non conforme")
        ]
        
        for ref, order, carrier, dtype, amt, status, acc_amt, rej_msg in test_claims:
            # Check if exists
            cur.execute("SELECT id FROM claims WHERE claim_reference = %s", (ref,))
            exists = cur.fetchone()
            
            if exists:
                print(f"Updating claim {ref}...")
                cur.execute("""
                    UPDATE claims 
                    SET status = %s, accepted_amount = %s, rejection_reason = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (status, acc_amt, rej_msg, exists[0]))
            else:
                print(f"Inserting claim {ref}...")
                cur.execute("""
                    INSERT INTO claims (
                        claim_reference, client_id, order_id, carrier, 
                        dispute_type, amount_requested, status, 
                        accepted_amount, rejection_reason, tracking_number
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (ref, client_id, order, carrier, dtype, amt, status, acc_amt, rej_msg, f"TRK-{order}"))
        
        conn.commit()
        print("✅ Production Neon DB updated with test claims!")
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    insert_test_data()
