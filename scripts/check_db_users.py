import sqlite3, os, sys

for db_path in ["data/recours_ecommerce.db", "data/test_recours_ecommerce.db"]:
    if os.path.exists(db_path):
        print(f"\nDB: {db_path}")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        try:
            cur.execute("SELECT id, email, full_name, password_hash FROM clients LIMIT 20")
            rows = cur.fetchall()
            for r in rows:
                d = dict(r)
                pwd = d.get("password_hash") or ""
                has_pwd = "OUI (" + str(len(pwd)) + " chars)" if pwd else "NON"
                print("  [{}] {} | {} | pwd={}".format(d["id"], d["email"], d.get("full_name", ""), has_pwd))
        except Exception as e:
            print("  Erreur:", e)
        conn.close()
