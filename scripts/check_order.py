"""Vérification live de la commande #7820676813 dans toutes les DBs disponibles."""
import sys, os, sqlite3, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ORDER_ID = "7820676813"
SEARCH_TERMS = [ORDER_ID, ORDER_ID[-8:], ORDER_ID[-10:]]

results = []

# 1. SQLite
for db_path in ["data/recours_ecommerce.db", "data/test_recours_ecommerce.db", "database/passwords.db"]:
    if not os.path.exists(db_path):
        continue
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        # Get tables
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cur.fetchall()]
        for table in tables:
            for term in SEARCH_TERMS:
                try:
                    cur.execute(f"SELECT * FROM {table} WHERE CAST(rowid AS TEXT) LIKE ? OR CAST(* AS TEXT) LIKE ?", (f"%{term}%", f"%{term}%"))
                except Exception:
                    pass
                # Try column-based search
                cur.execute(f"PRAGMA table_info({table})")
                cols = [c[1] for c in cur.fetchall()]
                text_cols = [c for c in cols if any(k in c.lower() for k in ['id','ref','order','claim','tracking','number'])]
                for col in text_cols:
                    try:
                        cur.execute(f"SELECT * FROM {table} WHERE CAST({col} AS TEXT) LIKE ?", (f"%{term}%",))
                        rows = cur.fetchall()
                        for row in rows:
                            results.append({"db": db_path, "table": table, "col": col, "term": term, "data": dict(row)})
                    except Exception:
                        pass
        conn.close()
    except Exception as e:
        print(f"  Err {db_path}: {e}")

# 2. Try PostgreSQL via Supabase if env vars available
try:
    import os
    db_url = os.environ.get("DATABASE_URL") or os.environ.get("SUPABASE_DB_URL")
    if db_url:
        import psycopg2
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        for term in SEARCH_TERMS:
            cur.execute("SELECT * FROM claims WHERE order_id ILIKE %s OR claim_reference ILIKE %s LIMIT 5", (f"%{term}%", f"%{term}%"))
            rows = cur.fetchall()
            for row in rows:
                results.append({"db": "postgres", "data": str(row)})
        conn.close()
except Exception as e:
    print(f"  Postgres: {e}")

# Report
if results:
    print(f"\n✅ {len(results)} résultat(s) trouvé(s) pour commande {ORDER_ID}:")
    for r in results:
        print(f"\n  DB={r['db']} | Table={r.get('table','')} | Col={r.get('col','')}")
        data = r.get('data', {})
        for k, v in (data.items() if isinstance(data, dict) else []):
            if v:
                print(f"    {k}: {v}")
else:
    print(f"\n❌ Commande {ORDER_ID} introuvable en base locale.")
    print("\n  Tentative Colissimo live tracking...")
    # Try live tracking
    try:
        import requests
        url = f"https://www.laposte.fr/outils/suivre-vos-envois?code={ORDER_ID}"
        r = requests.get(url, timeout=8)
        print(f"  LaPoste status: {r.status_code}")
    except Exception as e:
        print(f"  LaPoste: {e}")
