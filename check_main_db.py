import sqlite3
import os

db_path = os.path.join('database', 'main.db')
print(f"Checking database at: {db_path}")

try:
    if not os.path.exists(db_path):
        print("❌ Database file does not exist!")
    else:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n=== Tables ===")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        for table in tables:
            print(f"- {table[0]}")
            
            # Check row count
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"  Rows: {count}")

        # Check for admin client
        print("\n=== Checking Admin Client ===")
        cursor.execute("SELECT * FROM clients WHERE email='admin@refundly.ai'")
        admin = cursor.fetchone()
        if admin:
            print(f"✅ Admin found: ID {admin[0]}")
            
            # Check claims for admin
            cursor.execute("SELECT COUNT(*) FROM claims WHERE client_id=?", (admin[0],))
            claims_count = cursor.fetchone()[0]
            print(f"   Claims linked: {claims_count}")
        else:
            print("❌ Admin 'admin@refundly.ai' NOT found in main.db")

        conn.close()
except Exception as e:
    print(f"Error: {e}")
