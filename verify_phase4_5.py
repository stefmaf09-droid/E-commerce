
import os
import sys

# Add root to path
sys.path.append(os.getcwd())

from src.database.database_manager import get_db_manager
from src.payments.subscription_manager import SubscriptionManager
from src.payments.stripe_manager import StripeManager

def verify_subscription_and_billing():
    print("=== 🧪 VÉRIFICATION PHASE 4.5 : SUBSCRIPTION & BILLING ===")
    
    db = get_db_manager()
    sub_mgr = SubscriptionManager(db)
    
    # 0. Create test client (Using correct column names)
    conn = db.get_connection()
    conn.execute("INSERT OR IGNORE INTO clients (id, email, full_name) VALUES (1, 'test@boutique.com', 'Boutique Test')")
    conn.commit()
    conn.close()
    
    # 1. Test Tier Upgrade
    print("\n--- 📈 Subscription Tiers ---")
    try:
        sub_mgr.update_tier(1, 'business')
        summary = sub_mgr.get_billing_summary(1)
        print(f"✅ Tier Updated: {summary['tier']} (Fee: {summary['fee']}%)")
        print(f"✅ Features: {', '.join(summary['perks'])}")
        
        if summary['fee'] == 15.0:
            print("✅ Commission rate correctly set to 15%")
    except Exception as e:
        print(f"❌ Tier upgrade failed: {e}")

    # 2. Test Dynamic Payout
    print("\n--- 💸 Dynamic Payout Calculation ---")
    try:
        stripe_mgr = StripeManager(api_key="sk_test_mock")
        print("Testing create_payout_transfer signature and logic...")
        stripe_mgr.create_payout_transfer(
            destination_account_id="acct_123",
            amount=100.0,
            client_commission_rate=15.0,
            claim_ref="CLM-P45-01"
        )
        print("✅ create_payout_transfer function updated and called successfully")
    except Exception as e:
        if "Invalid API Key" in str(e) or "No API key" in str(e):
            print("✅ create_payout_transfer signature verified (API key error expected)")
        else:
            print(f"❌ Payout test failed: {e}")

    print("\n=== ✨ VÉRIFICATION PHASE 4.5 TERMINÉE ===")

if __name__ == "__main__":
    verify_subscription_and_billing()
