
import sqlite3
import os

schema = """
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    company_name TEXT,
    phone TEXT,
    stripe_account_id TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS claims (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_reference TEXT UNIQUE NOT NULL,
    client_id INTEGER NOT NULL,
    store_id INTEGER,
    order_id TEXT NOT NULL,
    carrier TEXT NOT NULL,
    dispute_type TEXT NOT NULL,
    amount_requested REAL NOT NULL,
    currency TEXT DEFAULT 'EUR',
    status TEXT DEFAULT 'pending',
    submitted_at TIMESTAMP,
    response_deadline DATE,
    response_received_at TIMESTAMP,
    accepted_amount REAL,
    rejection_reason TEXT,
    payment_status TEXT DEFAULT 'unpaid',
    payment_date TIMESTAMP,
    order_date DATE,
    tracking_number TEXT,
    customer_name TEXT,
    delivery_address TEXT,
    follow_up_level INTEGER DEFAULT 0,
    last_follow_up_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
);
"""

db_path = "test_reproduce.db"
if os.path.exists(db_path):
    os.remove(db_path)

conn = sqlite3.connect(db_path)
try:
    conn.executescript(schema)
    print("Schema executed successfully")
    
    client_id = 1
    ten_days_ago = "2026-01-15T12:00:00"
    
    query = """
        INSERT INTO claims (claim_reference, client_id, order_id, carrier, dispute_type, amount_requested, status, submitted_at, follow_up_level)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = ("CLM-7-DAYS", client_id, "ORD-TEST-7", "Colissimo", "lost", 100.0, "submitted", ten_days_ago, 0)
    
    conn.execute(query, params)
    print("Insert executed successfully")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
    if os.path.exists(db_path):
        os.remove(db_path)
