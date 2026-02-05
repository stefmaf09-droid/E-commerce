"""
Script to add notification_preferences column to clients table.
Run this once to migrate the local database.
"""

import sqlite3
import os

# Path to database
db_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'main.db')

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if column already exists
    cursor.execute("PRAGMA table_info(clients)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'notification_preferences' not in columns:
        print("Adding notification_preferences column...")
        cursor.execute("""
            ALTER TABLE clients 
            ADD COLUMN notification_preferences TEXT 
            DEFAULT '{"claim_created":true,"claim_updated":true,"claim_accepted":true,"payment_received":true,"deadline_warning":true,"frequency":"immediate"}'
        """)
        conn.commit()
        print("✅ Column added successfully!")
    else:
        print("✅ Column already exists, no migration needed.")
    
    conn.close()
    print("\n✅ Database migration complete!")

except Exception as e:
    print(f"❌ Error: {e}")
