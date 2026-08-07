import sqlite3

conn = sqlite3.connect('data/recours_ecommerce.db')
cursor = conn.cursor()

cursor.execute("SELECT id, email, first_name, last_name FROM clients LIMIT 10")
clients = cursor.fetchall()

print("=== Clients in Database ===")
for client in clients:
    print(f"ID: {client[0]}, Email: {client[1]}, Name: {client[2]} {client[3]}")

conn.close()
