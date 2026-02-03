import sys
sys.path.insert(0, 'src')

from database.database_manager import DatabaseManager

db = DatabaseManager()
clients = db.get_all_clients()

print("=== All Clients ===")
for c in clients:
    print(f"ID: {c.get('id')}, Email: {c.get('email')}, Name: {c.get('first_name')} {c.get('last_name')}")
