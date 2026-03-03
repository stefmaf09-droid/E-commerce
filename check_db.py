import sqlite3
import os

db_path = r'data\recours_ecommerce.db'
print('DB exists:', os.path.exists(db_path), '|', os.path.abspath(db_path))
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

print('\n=== DISTRIBUTION STATUTS ===')
rows = conn.execute(
    "SELECT status, COUNT(*) n, "
    "SUM(CASE WHEN follow_up_level=0 OR follow_up_level IS NULL THEN 1 ELSE 0 END) sans_relance "
    "FROM claims GROUP BY status ORDER BY n DESC"
).fetchall()
for r in rows:
    print(dict(r))

print('\n=== REJECTED (detail) ===')
rows = conn.execute(
    "SELECT claim_reference, status, follow_up_level, last_follow_up_at, created_at, ai_reason_key "
    "FROM claims WHERE status='rejected' ORDER BY created_at"
).fetchall()
for r in rows:
    print(dict(r))

print('\n=== CLM-41625 ===')
r = conn.execute(
    "SELECT claim_reference, status, follow_up_level, last_follow_up_at, "
    "created_at, ai_reason_key, carrier, tracking_number "
    "FROM claims WHERE claim_reference='CLM-41625'"
).fetchone()
if r:
    print(dict(r))

print('\n=== CLM-26366 ===')
r = conn.execute(
    "SELECT claim_reference, status, follow_up_level, last_follow_up_at, "
    "created_at, ai_reason_key, carrier, tracking_number "
    "FROM claims WHERE claim_reference='CLM-26366'"
).fetchone()
if r:
    print(dict(r))

print('\n=== ATTACHMENTS CLM-41625 ===')
rows = conn.execute(
    "SELECT id, attachment_filename, mime_type, created_at "
    "FROM email_attachments WHERE claim_reference='CLM-41625'"
).fetchall()
for r in rows:
    print(dict(r))

conn.close()
print('\nDone.')
