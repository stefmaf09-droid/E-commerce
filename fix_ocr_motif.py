"""
Script pour:
1. Lier le motif 'bad_packaging' detecte par OCR au dossier CLM-41625
2. Verifier l'etat des dossiers rejected sur PostgreSQL
3. Forcer un scan du ReminderWorker pour tester
"""
import sys
sys.path.insert(0, '.')

from src.config import Config
from src.database.database_manager import DatabaseManager

# Forcer PostgreSQL via secrets.toml
db = DatabaseManager()
print(f"DB type: {db.db_type}")

conn = db.get_connection()
print("Connexion OK")

# 1. Etat des dossiers rejected sur POSTGRESQL
print("\n=== DOSSIERS REJECTED (PostgreSQL) ===")
cur = db._execute(conn,
    "SELECT claim_reference, status, follow_up_level, last_follow_up_at, "
    "created_at, ai_reason_key, carrier FROM claims WHERE status='rejected' ORDER BY created_at"
)
rejected = cur.fetchall()
for r in rejected:
    print(dict(r))

# 2. CLM-41625 et CLM-26366
print("\n=== CLM-41625 ===")
cur = db._execute(conn,
    "SELECT claim_reference, status, follow_up_level, last_follow_up_at, "
    "created_at, ai_reason_key, carrier, tracking_number FROM claims WHERE claim_reference='CLM-41625'"
)
r = cur.fetchone()
if r:
    d = dict(r)
    for k, v in d.items():
        print(f"  {k}: {v}")
    
    # Lier le motif bad_packaging si ai_reason_key est vide
    if not d.get('ai_reason_key'):
        print("\n  -> Liaison du motif 'bad_packaging' en cours...")
        db.update_claim_ai_analysis(
            'CLM-41625',
            'bad_packaging',
            "L'emballage insuffisant a ete identifie comme cause du sinistre. "
            "Une lettre de contestation basee sur les normes d'emballage UNIPROX peut etre generee.",
        )
        conn.close()
        conn = db.get_connection()
        r2 = db._execute(conn, "SELECT ai_reason_key, ai_advice FROM claims WHERE claim_reference='CLM-41625'").fetchone()
        print(f"  -> Motif mis a jour: {dict(r2)}")
    else:
        print(f"  -> Motif deja present: {d['ai_reason_key']}")
else:
    print("  CLM-41625 introuvable en base!")

# 3. Distribution complète
print("\n=== DISTRIBUTION STATUTS (PostgreSQL) ===")
cur = db._execute(conn,
    "SELECT status, COUNT(*) n, "
    "SUM(CASE WHEN follow_up_level=0 OR follow_up_level IS NULL THEN 1 ELSE 0 END) sans_relance "
    "FROM claims GROUP BY status ORDER BY n DESC"
)
for r in cur.fetchall():
    print(dict(r))

conn.close()
print("\nDone.")
