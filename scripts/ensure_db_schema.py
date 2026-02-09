
import sqlite3
import os

db_paths = [
    'd:/Recours_Ecommerce/data/test_recours_ecommerce.db',
    'd:/Recours_Ecommerce/data/recours_ecommerce.db'
]

table_sql = """
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_email) REFERENCES clients(email)
);
"""

for path in db_paths:
    if os.path.exists(path):
        try:
            conn = sqlite3.connect(path)
            conn.execute(table_sql)
            conn.commit()
            conn.close()
            print(f"Successfully updated {path}")
        except Exception as e:
            print(f"Error updating {path}: {e}")
    else:
        print(f"Database not found at {path}")
