"""Create demo account in SQLite database."""
import sys
import os

sys.path.insert(0, 'src')

from database.database_manager import DatabaseManager
from auth.password_manager import set_client_password

# Force SQLite database
db = DatabaseManager(db_path='data/test_recours_ecommerce.db', db_type='sqlite')

email = 'demo@refundly.ai'
password = 'Demo123!'

print(f"🔍 Checking if {email} exists in SQLite...")
client = db.get_client(email=email)

if client:
    print(f"✅ Client already exists with ID: {client['id']}")
    client_id = client['id']
else:
    print("Creating new client...")
    client_id = db.create_client(email, company_name='Refundly Demo SAS')
    print(f"✅ Client created with ID: {client_id}")

# Set/update password
print("\n🔐 Setting password...")
set_client_password(email, password)
print("✅ Password set successfully!")

print(f"\n{'='*60}")
print("✨ Demo account ready in SQLite!")
print(f"{'='*60}")
print(f"Email: {email}")
print(f"Password: {password}")
print(f"URL: http://localhost:8501")
print(f"{'='*60}")
