
import sqlite3
import os

db_paths = [
    'D:/Recours_Ecommerce/data/recours_ecommerce.db',
    'D:/Recours_Ecommerce/data/test_recours_ecommerce.db'
]

for db_path in db_paths:
    print(f"Checking database at {db_path}...")
    if not os.path.exists(db_path):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Create email_attachments if missing
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS email_attachments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_email TEXT NOT NULL,
        claim_reference TEXT,
        carrier TEXT,
        email_subject TEXT,
        email_from TEXT,
        email_received_at TEXT,
        attachment_filename TEXT,
        attachment_path TEXT,
        file_size INTEGER,
        mime_type TEXT,
        ai_analysis TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    print(f"Table email_attachments checked/created in {db_path}.")

    # 2. Add columns to claims if missing
    for col in ['ai_advice', 'ai_reason_key']:
        try:
            cursor.execute(f"ALTER TABLE claims ADD COLUMN {col} TEXT")
            print(f"Added column {col} to claims in {db_path}")
        except sqlite3.OperationalError:
            print(f"Column {col} already exists in claims in {db_path}")

    # 3. Add ai_analysis to email_attachments if missing
    try:
        cursor.execute("ALTER TABLE email_attachments ADD COLUMN ai_analysis TEXT")
        print(f"Added ai_analysis to email_attachments in {db_path}")
    except sqlite3.OperationalError:
        print(f"ai_analysis already exists in email_attachments in {db_path}")

    # 4. Ensure test claim exists
    cursor.execute("SELECT id FROM clients WHERE email = 'stephenrouxel22@orange.fr'")
    client = cursor.fetchone()
    if not client:
        cursor.execute("INSERT INTO clients (email, full_name) VALUES ('stephenrouxel22@orange.fr', 'Stephen Rouxel')")
        client_id = cursor.lastrowid
    else:
        client_id = client[0]

    cursor.execute("SELECT id FROM claims WHERE claim_reference = 'CLM-20260207-SIMUL'")
    if not cursor.fetchone():
        cursor.execute('''
            INSERT INTO claims (claim_reference, client_id, order_id, carrier, dispute_type, amount_requested, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('CLM-20260207-SIMUL', client_id, 'ORD-TEST-123', 'Chronopost', 'Poids', 50.0, 'submitted'))
        print(f"Created test claim CLM-20260207-SIMUL in {db_path}")

    conn.commit()
    conn.close()

print("Database preparation complete.")
