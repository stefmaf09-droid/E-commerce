"""
One-time migration: copy existing local SQLite manual-payments data
(database/manual_payments.db) into the production Postgres/Supabase
database.

Why this is needed
-------------------
ManualPaymentManager used to be hardcoded to a local SQLite file, ignoring
DATABASE_TYPE. Now that it follows DATABASE_TYPE like the rest of the app
(see src/payments/manual_payment_manager.py), any client IBAN or pending/paid
manual payment that only exists in the old local SQLite file needs those
rows copied into Postgres once, otherwise the money-recovery flow can no
longer see them after this change ships (the Mise en Demeure letters would
silently fall back to "contact us for bank details" instead of showing the
client's real IBAN, and pending payouts would look like they never existed).

This script is:
- Read-only on the SQLite side (never modifies or deletes the local file).
- Idempotent / safe to re-run: existing bank info in Postgres is updated in
  place (ON CONFLICT DO UPDATE on client_email); existing payments are
  matched by claim_reference and skipped rather than duplicated (the
  manual_payments table has no natural unique constraint of its own, same
  situation as sync_status in the passwords/credentials migration).

Usage (from the project root, with DATABASE_TYPE=postgres and DATABASE_URL
already configured, e.g. via .env / Streamlit secrets):

    python scripts/migrate_manual_payments_to_postgres.py --dry-run
    python scripts/migrate_manual_payments_to_postgres.py
"""
import argparse
import os
import sqlite3
import sys

from dotenv import load_dotenv

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)
load_dotenv(os.path.join(root_dir, '.env'))

from src.config import Config  # noqa: E402


def migrate(manual_payments_db_path: str, dry_run: bool = False):
    db_type = (Config.get('DATABASE_TYPE', 'sqlite') or 'sqlite').lower()
    if db_type != 'postgres':
        print(f"DATABASE_TYPE is '{db_type}', not 'postgres' — nothing to migrate to. Aborting.")
        return 1

    if not os.path.exists(manual_payments_db_path):
        print(f"No local file at {manual_payments_db_path} — nothing to migrate.")
        return 0

    from src.database.database_manager import create_postgres_connection

    pg_url = Config.get_database_url()
    pg_conn = create_postgres_connection(pg_url)
    pg_cur = pg_conn.cursor()

    # Make sure the target tables exist (same DDL as ManualPaymentManager's
    # Postgres branch).
    pg_cur.execute("""
        CREATE TABLE IF NOT EXISTS client_bank_info (
            client_email TEXT PRIMARY KEY,
            iban TEXT NOT NULL,
            bic TEXT,
            account_holder_name TEXT,
            bank_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    pg_cur.execute("""
        CREATE TABLE IF NOT EXISTS manual_payments (
            id SERIAL PRIMARY KEY,
            claim_reference TEXT NOT NULL,
            client_email TEXT NOT NULL,
            total_amount REAL NOT NULL,
            client_share REAL NOT NULL,
            platform_fee REAL NOT NULL,
            payment_status TEXT DEFAULT 'pending',
            payment_date TIMESTAMP,
            payment_method TEXT,
            transaction_reference TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    pg_conn.commit()

    sq_conn = sqlite3.connect(manual_payments_db_path)
    sq_conn.row_factory = sqlite3.Row

    # ---- 1. client_bank_info ---------------------------------------------
    bank_migrated = 0
    bank_rows = sq_conn.execute("SELECT * FROM client_bank_info").fetchall()
    for row in bank_rows:
        masked_iban = row['iban'][:4] + '...' + row['iban'][-4:] if row['iban'] and len(row['iban']) > 8 else '(iban)'
        print(f"  [bank_info] {row['client_email']} — {masked_iban}"
              + (" (dry-run)" if dry_run else ""))
        if not dry_run:
            pg_cur.execute("""
                INSERT INTO client_bank_info
                    (client_email, iban, bic, account_holder_name, bank_name, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (client_email) DO UPDATE
                SET iban = EXCLUDED.iban,
                    bic = EXCLUDED.bic,
                    account_holder_name = EXCLUDED.account_holder_name,
                    bank_name = EXCLUDED.bank_name,
                    updated_at = EXCLUDED.updated_at
            """, (row['client_email'], row['iban'], row['bic'], row['account_holder_name'],
                  row['bank_name'], row['created_at'], row['updated_at']))
        bank_migrated += 1

    if not dry_run:
        pg_conn.commit()

    # ---- 2. manual_payments (dedup by claim_reference) ---------------------
    payment_rows = sq_conn.execute("SELECT * FROM manual_payments").fetchall()
    sq_conn.close()

    pg_cur.execute("SELECT DISTINCT claim_reference FROM manual_payments")
    existing_refs = {r[0] for r in pg_cur.fetchall()}

    payments_migrated = 0
    payments_skipped = 0
    for row in payment_rows:
        if row['claim_reference'] in existing_refs:
            payments_skipped += 1
            continue
        print(f"  [payment] {row['claim_reference']} — {row['client_share']}EUR to "
              f"{row['client_email']} (status={row['payment_status']})"
              + (" (dry-run)" if dry_run else ""))
        if not dry_run:
            pg_cur.execute("""
                INSERT INTO manual_payments
                    (claim_reference, client_email, total_amount, client_share, platform_fee,
                     payment_status, payment_date, payment_method, transaction_reference, notes,
                     created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (row['claim_reference'], row['client_email'], row['total_amount'],
                  row['client_share'], row['platform_fee'], row['payment_status'],
                  row['payment_date'], row['payment_method'], row['transaction_reference'],
                  row['notes'], row['created_at'], row['updated_at']))
            existing_refs.add(row['claim_reference'])
        payments_migrated += 1

    if not dry_run:
        pg_conn.commit()
    pg_conn.close()

    print(f"\nSummary: {bank_migrated} bank info row(s), {payments_migrated} payment row(s) "
          f"{'would be ' if dry_run else ''}migrated to Postgres "
          f"({payments_skipped} payment row(s) already present, skipped).")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manual-payments-db", default=os.path.join(root_dir, "database", "manual_payments.db"))
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing to Postgres")
    args = parser.parse_args()

    sys.exit(migrate(args.manual_payments_db, dry_run=args.dry_run))
