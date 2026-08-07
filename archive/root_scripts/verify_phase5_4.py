
import os
import sys

# Add root to path
sys.path.append(os.getcwd())

from src.auth.security_manager import SecurityManager

def verify_phase5_4():
    print("=== 🧪 VÉRIFICATION PHASE 5.4 : BANKING GRADE SECURITY ===")
    
    sec_mgr = SecurityManager()
    
    # 1. Log an action
    print("\n--- 📝 Logging Audit Action ---")
    sec_mgr.log_action(
        user_id=1, 
        user_type='admin', 
        action='payout_triggered', 
        resource_type='payment', 
        resource_id=123,
        metadata={'ip': '127.0.0.1', 'ua': 'TestRunner'}
    )
    print("✅ Action logged successfully.")
    
    # 2. Retrieve Audit Trail
    print("\n--- 🔍 Checking Audit Trail ---")
    trail = sec_mgr.get_audit_trail(limit=5)
    if trail:
        found = False
        for log in trail:
            if log['action'] == 'payout_triggered':
                print(f"✅ Found log: {log['action']} at {log['created_at']}")
                found = True
                break
        if not found:
            print("❌ Log not found in trail.")
    else:
        print("❌ Audit trail empty.")

    # 3. Check UI
    print("\n--- 🖼️ UI Integration (Grep) ---")
    with open('admin_control_tower.py', 'r', encoding='utf-8') as f:
        if "Journaux d'Audit" in f.read():
            print("✅ Admin Control Tower UI found.")

    print("\n=== ✨ VÉRIFICATION PHASE 5.4 TERMINÉE ===")

if __name__ == "__main__":
    verify_phase5_4()
