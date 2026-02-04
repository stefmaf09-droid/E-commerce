import os
import sqlite3
import psycopg2
import mimetypes
import logging
from typing import Dict, Any, List, Tuple
from supabase import create_client, Client

logger = logging.getLogger(__name__)

class CloudSyncManager:
    """Gère la synchronisation automatique des données et fichiers vers Supabase."""
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self.db_url = os.getenv("DATABASE_URL")
        self.local_db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'recours_ecommerce.db')
        self.local_photos_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'client_photos')
        
    def is_configured(self) -> bool:
        """Vérifie si les informations Cloud sont présentes."""
        return all([self.supabase_url, self.supabase_key, self.db_url])

    def run_full_sync(self):
        """Lance la migration complète (Schema + Base + Fichiers)."""
        if not self.is_configured():
             return False, "⚠️ Configuration Cloud manquante dans les Secrets."
             
        results = []
        
        # 0. Sync Schema (Init DB if empty)
        try:
            schema_success, schema_msg = self._init_schema()
            results.append(f"Schema: {schema_msg}")
            if not schema_success:
                return False, f"Schema Error: {schema_msg}"
        except Exception as e:
            return False, f"Schema Critical Error: {str(e)}"
        
        # 1. Sync Base de données
        try:
            db_success, db_msg = self._sync_database()
            results.append(f"DB: {db_msg}")
        except Exception as e:
            db_success = False
            results.append(f"DB Error: {str(e)}")

        # 2. Sync Fichiers
        try:
            file_success, file_msg = self._sync_files()
            results.append(f"Files: {file_msg}")
        except Exception as e:
            file_success = False
            results.append(f"Files Error: {str(e)}")
            
        return (db_success and file_success), "\n".join(results)

    def _init_schema(self) -> Tuple[bool, str]:
        """Initialise le schéma PostgreSQL si nécessaire."""
        schema_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'database', 'schema_postgres.sql')
        if not os.path.exists(schema_path):
            return False, "Fichier schema_postgres.sql introuvable."

        try:
            pg_conn = psycopg2.connect(self.db_url)
            with pg_conn.cursor() as cur:
                with open(schema_path, 'r', encoding='utf-8') as f:
                    schema_sql = f.read()
                    # Psycopg2 can execute multiple statements in one go if they are valid SQL
                    cur.execute(schema_sql)
            pg_conn.commit()
            pg_conn.close()
            return True, "Schéma vérifié/créé."
        except Exception as e:
            return False, str(e)

    def _sync_database(self) -> Tuple[bool, str]:
        if not os.path.exists(self.local_db_path):
            return False, "Base locale introuvable."

        sqlite_conn = sqlite3.connect(self.local_db_path)
        sqlite_conn.row_factory = sqlite3.Row
        sqlite_cur = sqlite_conn.cursor()

        pg_conn = psycopg2.connect(self.db_url)
        pg_cur = pg_conn.cursor()

        tables = ['clients', 'stores', 'claims', 'disputes', 'payments', 'notifications']
        total_inserted = 0

        for table in tables:
            sqlite_cur.execute(f"SELECT * FROM {table}")
            rows = sqlite_cur.fetchall()
            if not rows: continue

            columns = rows[0].keys()
            placeholders = ", ".join(["%s"] * len(columns))
            insert_query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"

            for row in rows:
                pg_cur.execute(insert_query, tuple(row))
                total_inserted += 1
        
        pg_conn.commit()
        sqlite_conn.close()
        pg_conn.close()
        
        return True, f"{total_inserted} lignes synchronisées."

    def _sync_files(self) -> Tuple[bool, str]:
        if not os.path.exists(self.local_photos_path):
            return True, "Aucune photo à synchroniser."

        supabase: Client = create_client(self.supabase_url, self.supabase_key)
        bucket_name = "evidence"
        count = 0

        for claim_id in os.listdir(self.local_photos_path):
            claim_dir = os.path.join(self.local_photos_path, claim_id)
            if not os.path.isdir(claim_dir): continue

            for filename in os.listdir(claim_dir):
                file_path = os.path.join(claim_dir, filename)
                storage_path = f"{claim_id}/{filename}"
                
                with open(file_path, 'rb') as f:
                    try:
                        mime, _ = mimetypes.guess_type(file_path)
                        supabase.storage.from_(bucket_name).upload(
                            path=storage_path,
                            file=f.read(),
                            file_options={"upsert": "true", "content-type": mime or "application/octet-stream"}
                        )
                        count += 1
                    except Exception:
                        pass # Ignore duplicates or minor errors during bulk
        
        return True, f"{count} fichiers uploadés."
