"""
Script pour ajouter des magasins de test pour démonstration multi-store.
"""

import sys
sys.path.insert(0, 'src')

import sqlite3
import json
from cryptography.fernet import Fernet
from pathlib import Path

# Charger la clé encryption
key_file = Path("config/.secret_key")
with open(key_file, 'rb') as f:
    key = f.read()

cipher = Fernet(key)

# Connecter à la DB
conn = sqlite3.connect("database/credentials.db")
cursor = conn.cursor()

email = 'stephenrouxel22@orange.fr'

# Magasin 2 - WooCommerce
creds2 = {
    'shop_url': 'boutique-deco.com',
    'api_key': 'woo_demo_key',
    'api_secret': 'woo_demo_secret'
}
encrypted2 = cipher.encrypt(json.dumps(creds2).encode())

cursor.execute("""
    INSERT OR REPLACE INTO credentials 
    (client_id, platform, store_name, credentials_encrypted, updated_at)
    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
""", (email, 'woocommerce', 'Boutique Déco Lyon', encrypted2))

# Magasin 3 - PrestaShop  
creds3 = {
    'shop_url': 'electro-shop.fr',
    'api_key': 'ps_demo_key'
}
encrypted3 = cipher.encrypt(json.dumps(creds3).encode())

cursor.execute("""
    INSERT OR REPLACE INTO credentials 
    (client_id, platform, store_name, credentials_encrypted, updated_at)
    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
""", (email, 'prestashop', 'Électro Marseille', encrypted3))

conn.commit()
conn.close()

print("✅ 2 nouveaux magasins ajoutés !")
print(f"   - Boutique Déco Lyon (WooCommerce)")
print(f"   - Électro Marseille (PrestaShop)")
print()
print("🔄 Rafraîchissez le dashboard pour voir le sélecteur !")
