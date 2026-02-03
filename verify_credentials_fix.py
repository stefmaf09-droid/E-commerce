
import sys
import os
sys.path.insert(0, os.getcwd())

from src.auth.credentials_manager import CredentialsManager
import logging

logging.basicConfig(level=logging.INFO)

def test_fix():
    print("Testing CredentialsManager Fix...")
    manager = CredentialsManager()
    
    # Check if get_all_stores exists
    if hasattr(manager, 'get_all_stores'):
        print("✅ get_all_stores method found.")
    else:
        print("❌ get_all_stores method MISSING.")
        return
    
    # Test multi-store
    email = "fix_test@example.com"
    manager.store_credentials(email, 'shopify', {'shop_url': 'test1.com'}, 'Store 1')
    manager.store_credentials(email, 'woocommerce', {'shop_url': 'test2.com'}, 'Store 2')
    
    stores = manager.get_all_stores(email)
    print(f"Found {len(stores)} stores for {email}:")
    for s in stores:
        print(f"  - {s['store_name']} ({s['platform']})")
    
    if len(stores) >= 2:
        print("✅ Multi-store retrieval working.")
    else:
        print("❌ Multi-store retrieval failed.")

if __name__ == "__main__":
    test_fix()
