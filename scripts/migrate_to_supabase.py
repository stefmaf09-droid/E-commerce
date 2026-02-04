import sqlite3
import psycopg2
from psycopg2 import extras
import os

# Configuration (Assurez-vous que les variables sont correctes ou remplacez-les)
SQLITE_DB = "data/recours_ecommerce.db"
POSTGRES_URL = "postgresql://postgres:Siobhane5607%21Mafoudia250983%21@db.lrvqbgirvwytkmmmwjsx.supabase.co:5432/postgres"

def migrate_data():
    if not os.path.exists(SQLITE_DB):
        print(f"❌ Base SQLite introuvable à {SQLITE_DB}")
        return

    print("🔌 Connexion aux bases de données...")
    try:
        sqlite_conn = sqlite3.connect(SQLITE_DB)
        sqlite_conn.row_factory = sqlite3.Row
        sqlite_cur = sqlite_conn.cursor()

        pg_conn = psycopg2.connect(POSTGRES_URL)
        pg_cur = pg_conn.cursor()

        # Liste des tables à migrer dans l'ordre des dépendances
        tables = ['clients', 'stores', 'claims', 'disputes', 'payments', 'notifications']

        for table in tables:
            print(f"📦 Migration de la table: {table}...")
            
            # Lire depuis SQLite
            sqlite_cur.execute(f"SELECT * FROM {table}")
            rows = sqlite_cur.fetchall()
            
            if not rows:
                print(f"  ℹ️ Table {table} vide, passage à la suivante.")
                continue

            # Préparer l'insertion PostgreSQL
            columns = rows[0].keys()
            placeholders = ", ".join(["%s"] * len(columns))
            insert_query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"

            inserted_count = 0
            for row in rows:
                try:
                    pg_cur.execute(insert_query, tuple(row))
                    inserted_count += 1
                except Exception as e:
                    print(f"  ⚠️ Erreur sur une ligne de {table}: {e}")
            
            pg_conn.commit()
            print(f"  ✅ {inserted_count} lignes migrées pour {table}.")

        print("\n✨ Migration terminée avec succès !")
        
    except Exception as e:
        print(f"❌ Erreur pendant la migration : {e}")
    finally:
        if 'sqlite_conn' in locals(): sqlite_conn.close()
        if 'pg_conn' in locals(): pg_conn.close()

if __name__ == "__main__":
    migrate_data()
