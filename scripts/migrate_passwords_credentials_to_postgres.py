"""
One-time migration: copy existing local SQLite password/credentials data
(database/passwords.db, database/credentials.db) into the production
Postgres/Supabase database.

Why this is needed
-------------------
PasswordManager and CredentialsManager used to be hardcoded to local SQLite
files, ignoring DATABASE_TYPE. Now that they follow DATABASE_TYPE like the
rest of the app (see src/auth/password_manager.py, src/auth/credentials_manager.py),
any account whose password/credentials only exist in the old local SQLite
files needs those rows copied into Postgres once, otherwise it can no
longer log in / its store connectors stop working after this change ships.

This script is:
- Read-only on the SQLite side (never modifies or deletes the local files).
- Idempotent / safe to re-run: existing rows in Postgres are updated in
  place (ON CONFLICT DO UPDATE) rather than duplicated.
- Supports --dry-run to preview what would be migrated without writing.

Usage (from the project root, with DATABASE_TYPE=postgres and DATABASE_URL
already configured, e.g. via .env / Streamlit secrets):

    python scripts/migrate_passwords_credentials_to_postgres.py --dry-run
    python scripts/migrate_passwords_credentials_to_postgres.py
"""
import argparse
import os
import sqlite3
import sys

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

from src.config import Config  # noqa: E402


def migrate(passwords_db_path: str, credentials_db_path: str, dry_run: bool = False):
    db_type = (Config.get('DATABASE_TYPE', 'sqlite') or 'sqlite').lower()
    if db_type != 'postgres':
        print(f"DATABASE_TYPE is '{db_type}', not 'postgres' — nothing to migrate to. Aborting.")
        return 1

    from src.database.database_manager import create_postgres_connection

    pg_url = Config.get_database_url()
    pg_conn = create_postgres_connection(pg_url)
    pg_cur = pg_conn.cursor()

    # Make sure the target tables exist (same DDL as PasswordManager/CredentialsManager).
    pg_cur.execute("""
        CREATE TABLE IF NOT EXISTS client_passwords (
            client_email TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'client',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    pg_cur.execute("""
        CREATE TABLE IF NOT EXISTS credentials (
            id SERIAL PRIMARY KEY,
            client_id TEXT NOT NULL,
            platform TEXT NOT NULL,
            store_name TEXT,
            credentials_encrypted BYTEA NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(client_id, platform, store_name)
        )
    """)
    pg_cur.execute("""
        CREATE TABLE IF NOT EXISTS sync_status (
            id SERIAL PRIMARY KEY,
            credential_id INTEGER NOT NULL,
            last_sync TIMESTAMP,
            last_order_id TEXT,
            status TEXT DEFAULT 'active',
            FOREIGN KEY (credential_id) REFERENCES credentials(id)
        )
    """)
    pg_conn.commit()

    # ---- 1. client_passwords -------------------------------------------------
    pw_migrated = 0
    if os.path.exists(passwords_db_path):
        sq_conn = sqlite3.connect(passwords_db_path)
        sq_conn.row_factory = sqlite3.Row
        rows = sq_conn.execute("SELECT * FROM client_passwords").fetchall()
        sq_conn.close()

        for row in rows:
            print(f"  [passwords] {row['client_email']} (role={row['role']})"
                  + (" (dry-run)" if dry_run else ""))
            if not dry_run:
                pg_cur.execute("""
                    INSERT INTO client_passwords
                        (client_email, password_hash, role, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (client_email) DO UPDATE
                    SET password_hash = EXCLUDED.password_hash,
                        role = EXCLUDED.role,
                        updated_at = EXCLUDED.updated_at
                """, (row['client_email'], row['password_hash'], row['role'],
                      row['created_at'], row['updated_at']))
            pw_migrated += 1
    else:
        print(f"  (no local file at {passwords_db_path}, skipping)")

    if not dry_run:
        pg_conn.commit()

    # ---- 2. credentials + sync_status -----------------------------------------
    cred_migrated = 0
    if os.path.exists(credentials_db_path):
        sq_conn = sqlite3.connect(credentials_db_path)
        sq_conn.row_factory = sqlite3.Row
        cred_rows = sq_conn.execute("SELECT * FROM credentials").fetchall()
        sync_rows = sq_conn.execute("SELECT * FROM sync_status").fetchall()
        sq_conn.close()

        old_id_to_new_id = {}

        for row in cred_rows:
            print(f"  [credentials] client={row['client_id']} platform={row['platform']} "
                  f"store={row['store_name']}" + (" (dry-run)" if dry_run else ""))
            if not dry_run:
                pg_cur.execute("""
                    INSERT INTO credentials
                        (client_id, platform, store_name, credentials_encrypted, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (client_id, platform, store_name) DO UPDATE
                    SET credentials_encrypted = EXCLUDED.credentials_encrypted,
                        updated_at = EXCLUDED.updated_at
                    RETURNING id
                """, (row['client_id'], row['platform'], row['store_name'],
                      row['credentials_encrypted'], row['created_at'], row['updated_at']))
                new_id = pg_cur.fetchone()[0]
                old_id_to_new_id[row['id']] = new_id
            cred_migrated += 1

        if not dry_run:
            pg_conn.commit()

            # Only carry over sync_status rows that don't already exist for
            # that credential (avoids piling up duplicates on re-runs, since
            # sync_status has no unique constraint of its own).
            pg_cur.execute("SELECT DISTINCT credential_id FROM sync_status")
            existing_sync_credential_ids = {r[0] for r in pg_cur.fetchall()}

            for row in sync_rows:
                new_credential_id = old_id_to_new_id.get(row['credential_id'])
                if new_credential_id is None or new_credential_id in existing_sync_credential_ids:
                    continue
                pg_cur.execute("""
                    INSERT INTO sync_status
                        (credential_id, last_sync, last_order_id, status)
                    VALUES (%s, %s, %s, %s)
                """, (new_credential_id, row['last_sync'], row['last_order_id'], row['status']))
                existing_sync_credential_ids.add(new_credential_id)

            pg_conn.commit()
    else:
        print(f"  (no local file at {credentials_db_path}, skipping)")

    pg_conn.close()

    print(f"\nSummary: {pw_migrated} password row(s), {cred_migrated} credential row(s) "
          f"{'would be ' if dry_run else ''}migrated to Postgres.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--passwords-db", default=os.path.join(root_dir, "database", "passwords.db"))
    parser.add_argument("--credentials-db", default=os.path.join(root_dir, "database", "credentials.db"))
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing to Postgres")
    args = parser.parse_args()

    sys.exit(migrate(args.passwords_db, args.credentials_db, dry_run=args.dry_run))
