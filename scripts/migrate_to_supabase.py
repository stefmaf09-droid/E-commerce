import sqlite3
import psycopg2
from psycopg2 import extras
import os
from supabase import create_client, Client
import mimetypes

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

        print("\n✨ Migration de la base de données terminée.")

        # --- PHASE 2 : Migration des Fichiers (Storage) ---
        print("\n📁 Migration des fichiers vers Supabase Storage...")
        SUPABASE_URL = "https://lrvqbgirvwytkmmmwjsx.supabase.co"
        SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxydnFiZ2lydnd5dGttbW13anN4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MDIwODY4OCwiZXhwIjoyMDg1Nzg0Njg4fQ.qEGlbLr04Z_-k5oPoIfxRfoi09T0FLNpGsw63wqh584"
        
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        bucket_name = "evidence"
        evidence_root = "data/client_photos"

        if os.path.exists(evidence_root):
            for claim_id in os.listdir(evidence_root):
                claim_path = os.path.join(evidence_root, claim_id)
                if os.path.isdir(claim_path):
                    for filename in os.listdir(claim_path):
                        file_path = os.path.join(claim_path, filename)
                        if os.path.isfile(file_path):
                            storage_path = f"{claim_id}/{filename}"
                            print(f"  ☁️ Uploading {storage_path}...")
                            
                            with open(file_path, 'rb') as f:
                                try:
                                    mime, _ = mimetypes.guess_type(file_path)
                                    supabase.storage.from_(bucket_name).upload(
                                        path=storage_path,
                                        file=f.read(),
                                        file_options={"upsert": "true", "content-type": mime or "application/octet-stream"}
                                    )
                                    print(f"    ✅ Terminé.")
                                except Exception as e:
                                    if "already exists" in str(e).lower():
                                        print(f"    ℹ️ Déjà présent.")
                                    else:
                                        print(f"    ⚠️ Erreur : {e}")
        else:
            print("ℹ️ Aucun dossier de photos trouvé localement.")

        print("\n✨ Migration complète terminée avec succès !")
        
    except Exception as e:
        print(f"❌ Erreur pendant la migration : {e}")
    finally:
        if 'sqlite_conn' in locals(): sqlite_conn.close()
        if 'pg_conn' in locals(): pg_conn.close()

if __name__ == "__main__":
    migrate_data()
