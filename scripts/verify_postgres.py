#!/usr/bin/env python3
"""
Script de vérification de la connexion PostgreSQL.

Teste la connexion Neon et affiche les tables créées.

Usage:
    python scripts/verify_postgres.py
"""

import os
import sys
from pathlib import Path

# Load .env
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')


def main():
    print("=" * 60)
    print("Vérification PostgreSQL (Neon)")
    print("=" * 60)

    db_url = os.getenv('DATABASE_URL', '')
    if not db_url or 'sqlite' in db_url:
        print("❌ DATABASE_URL n'est pas configuré en PostgreSQL.")
        print("   Vérifiez votre fichier .env → DATABASE_URL=postgresql://...")
        sys.exit(1)

    print(f"→ URL : {db_url[:60]}...")

    try:
        import psycopg2
    except ImportError:
        print("❌ psycopg2 non installé. Lancez : pip install psycopg2-binary")
        sys.exit(1)

    try:
        conn = psycopg2.connect(db_url, connect_timeout=10)
        print("✅ Connexion PostgreSQL réussie !")
    except Exception as e:
        print(f"❌ Connexion échouée : {e}")
        sys.exit(1)

    try:
        with conn.cursor() as cur:
            # List tables
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            tables = [row[0] for row in cur.fetchall()]

        if tables:
            print(f"\n📋 Tables présentes ({len(tables)}) :")
            for t in tables:
                with conn.cursor() as cur:
                    cur.execute(f"SELECT COUNT(*) FROM {t}")
                    count = cur.fetchone()[0]
                print(f"   ✓ {t:<30} ({count} lignes)")
        else:
            print("\n⚠️  Aucune table trouvée — exécutez d'abord le script de migration.")
            print("   python scripts/migrate_sqlite_to_postgres.py")

    finally:
        conn.close()

    print("\n" + "=" * 60)
    print("✅ Vérification terminée")
    print("=" * 60)


if __name__ == '__main__':
    main()
