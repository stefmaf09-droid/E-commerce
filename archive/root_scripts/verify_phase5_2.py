
import os
import sys

# Add root to path
sys.path.append(os.getcwd())

from src.auth.api_key_manager import APIKeyManager
from src.database.database_manager import get_db_manager

def verify_phase5_2():
    print("=== 🧪 VÉRIFICATION PHASE 5.2 : ENTERPRISE API ===")
    
    db = get_db_manager()
    key_mgr = APIKeyManager(db)
    
    # 1. Test Key Generation
    print("\n--- 🔑 API Key Management ---")
    client_id = 999
    raw_key = key_mgr.generate_key(client_id, name="Test Key")
    print(f"✅ Key Generated: {raw_key[:10]}...")
    
    # 2. Test Key Verification
    print("\n--- ✅ Key Verification ---")
    verified_id = key_mgr.verify_key(raw_key)
    if verified_id == client_id:
        print(f"✅ Verification Success: ID {verified_id} matched.")
    else:
        print(f"❌ Verification Failed. Got {verified_id}")
        
    # 3. Test Invalid Key
    print("\n--- ❌ Invalid Key check ---")
    invalid_id = key_mgr.verify_key("rk_fake_key_123")
    if invalid_id is None:
        print("✅ Correctly rejected invalid key.")
        
    # 4. Check API Router exists
    if os.path.exists('src/api/router.py'):
        print("\n✅ API Router found at 'src/api/router.py'")

    print("\n=== ✨ VÉRIFICATION PHASE 5.2 TERMINÉE ===")

if __name__ == "__main__":
    verify_phase5_2()
