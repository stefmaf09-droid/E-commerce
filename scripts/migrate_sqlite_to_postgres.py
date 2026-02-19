#!/usr/bin/env python3
"""
Script de migration SQLite → PostgreSQL (Neon).

Lit la base SQLite locale et recrée toutes les données dans Postgres.
Exécuter UNE SEULE FOIS après avoir configuré DATABASE_URL dans .env.

Usage:
    python scripts/migrate_sqlite_to_postgres.py
"""

import os
import sys
import sqlite3
import logging
from pathlib import Path

# Load .env
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
SQLITE_PATH = Path(__file__).parent.parent / 'data' / 'recours_ecommerce.db'
SCHEMA_PATH = Path(__file__).parent.parent / 'database' / 'schema_postgres.sql'
# ─────────────────────────────────────────────────────────────────────────────


def get_sqlite_conn():
    if not SQLITE_PATH.exists():
        logger.error(f"SQLite DB not found: {SQLITE_PATH}")
        sys.exit(1)
    conn = sqlite3.connect(str(SQLITE_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def get_postgres_conn():
    try:
        import psycopg2
        from psycopg2 import extras
        db_url = os.getenv('DATABASE_URL')
        if not db_url or 'sqlite' in db_url:
            logger.error("DATABASE_URL must be a PostgreSQL URL. Check your .env file.")
            sys.exit(1)
        conn = psycopg2.connect(db_url, connect_timeout=15)
        return conn, extras
    except ImportError:
        logger.error("psycopg2 not installed. Run: pip install psycopg2-binary")
        sys.exit(1)
    except Exception as e:
        logger.error(f"PostgreSQL connection failed: {e}")
        sys.exit(1)


def apply_schema(pg_conn, extras):
    """Create tables in PostgreSQL."""
    logger.info("Applying PostgreSQL schema...")
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        schema = f.read()

    with pg_conn.cursor() as cur:
        cur.execute(schema)
    pg_conn.commit()
    logger.info("✅ Schema applied")


def migrate_table(sqlite_conn, pg_conn, extras, table: str, columns: list[str]):
    """Copy all rows from a SQLite table to PostgreSQL."""
    logger.info(f"Migrating table: {table}")
    sqlite_cursor = sqlite_conn.execute(f"SELECT {', '.join(columns)} FROM {table}")
    rows = sqlite_cursor.fetchall()

    if not rows:
        logger.info(f"   ↳ No rows to migrate in {table}")
        return 0

    placeholders = ', '.join(['%s'] * len(columns))
    col_names = ', '.join(columns)
    sql = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"

    with pg_conn.cursor() as cur:
        extras.execute_batch(cur, sql, [tuple(row) for row in rows], page_size=100)
    pg_conn.commit()

    logger.info(f"   ↳ Migrated {len(rows)} rows")
    return len(rows)


def main():
    logger.info("=" * 60)
    logger.info("Migration SQLite → PostgreSQL (Neon)")
    logger.info("=" * 60)

    sqlite_conn = get_sqlite_conn()
    pg_conn, extras = get_postgres_conn()

    try:
        # 1. Apply schema
        apply_schema(pg_conn, extras)

        # 2. Migrate each table (order matters for FK constraints)
        tables = {
            'clients': ['id', 'email', 'full_name', 'company_name', 'phone',
                        'created_at', 'updated_at', 'is_active', 'stripe_account_id',
                        'stripe_onboarding_completed', 'stripe_connect_id',
                        'stripe_onboarding_status', 'subscription_tier', 'commission_rate',
                        'notification_preferences'],
            'stores': ['id', 'client_id', 'platform', 'store_name', 'store_url',
                       'country', 'currency', 'is_active', 'created_at'],
            'claims': ['id', 'claim_reference', 'client_id', 'store_id', 'order_id',
                       'carrier', 'dispute_type', 'amount_requested', 'currency', 'status',
                       'submitted_at', 'response_deadline', 'response_received_at',
                       'accepted_amount', 'rejection_reason', 'payment_status', 'payment_date',
                       'tracking_number', 'customer_name', 'delivery_address',
                       'follow_up_level', 'last_follow_up_at', 'created_at', 'updated_at'],
            'disputes': ['id', 'client_id', 'store_id', 'order_id', 'carrier',
                         'dispute_type', 'amount_recoverable', 'currency', 'detected_at',
                         'claim_id', 'is_claimed', 'tracking_number', 'customer_name'],
            'payments': ['id', 'claim_id', 'client_id', 'total_amount', 'client_share',
                         'platform_fee', 'currency', 'payment_method', 'payment_status',
                         'transaction_reference', 'paid_at', 'notes', 'created_at'],
            'notifications': ['id', 'client_id', 'notification_type', 'subject', 'sent_to',
                              'sent_at', 'status', 'error_message', 'related_claim_id'],
            'activity_logs': ['id', 'client_id', 'action', 'resource_type', 'resource_id',
                              'ip_address', 'user_agent', 'details', 'timestamp'],
        }

        total = 0
        for table, columns in tables.items():
            try:
                # Check if table exists in SQLite
                cur = sqlite_conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
                )
                if not cur.fetchone():
                    logger.info(f"   ↳ Table {table} not found in SQLite — skipping")
                    continue
                n = migrate_table(sqlite_conn, pg_conn, extras, table, columns)
                total += n
            except Exception as e:
                logger.warning(f"Error migrating {table}: {e}")

        # 3. Reset sequences for SERIAL columns
        logger.info("Resetting PostgreSQL sequences...")
        with pg_conn.cursor() as cur:
            for table in tables:
                try:
                    cur.execute(f"""
                        SELECT setval(pg_get_serial_sequence('{table}', 'id'),
                               COALESCE(MAX(id), 0) + 1, false)
                        FROM {table}
                    """)
                except Exception:
                    pass
        pg_conn.commit()

        logger.info("=" * 60)
        logger.info(f"✅ Migration complete — {total} total rows migrated")
        logger.info("=" * 60)

    finally:
        sqlite_conn.close()
        pg_conn.close()


if __name__ == '__main__':
    main()
