"""Test rapide de connexion Supabase."""
import psycopg2

URL = "postgresql://postgres:Siobhane5607!Mafoudia250983!@db.lrvqbgirvwytkmmmwjsx.supabase.co:5432/postgres?sslmode=require"

try:
    conn = psycopg2.connect(URL, connect_timeout=10)
    cur = conn.cursor()
    cur.execute("SELECT version()")
    version = cur.fetchone()[0]
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name")
    tables = [r[0] for r in cur.fetchall()]
    conn.close()
    print(f"✅ Supabase OK !")
    print(f"   Version : {version[:60]}")
    print(f"   Tables  : {tables if tables else '(aucune — base vide)'}")
except Exception as e:
    print(f"❌ Erreur : {e}")
