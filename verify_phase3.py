
import os
import sys
import logging
from datetime import datetime

# Add root to path
sys.path.append(os.getcwd())

from src.database.database_manager import get_db_manager
from src.payments.stripe_manager import StripeManager
from src.api.stripe_webhook_handler import StripeWebhookHandler
from src.integrations.gorgias_connector import GorgiasConnector
from src.analytics.risk_check_service import RiskCheckService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Phase3Verify")

def test_stripe_integration():
    print("\n--- 💳 Testing Stripe Integration ---")
    try:
        # We don't have real keys here, so we test class instantiation and mock logic
        manager = StripeManager(api_key="sk_test_mock")
        print("✅ StripeManager instantiated")
        
        handler = StripeWebhookHandler()
        print("✅ StripeWebhookHandler instantiated")
    except Exception as e:
        print(f"❌ Stripe test failed: {e}")

def test_sav_integration():
    print("\n--- 🔌 Testing SAV Integration ---")
    try:
        connector = GorgiasConnector(api_key="mock", domain="test", email="admin@test.com")
        detection = connector.analyze_ticket_for_dispute("Mon colis est arrivé cassé, je suis très déçu.")
        print(f"✅ Auto-detection logic: {detection}")
        if detection == 'damage':
            print("✅ Dispute type correctly identified: damage")
        else:
            print(f"❌ Unexpected detection: {detection}")
    except Exception as e:
        print(f"❌ SAV test failed: {e}")

def test_fraud_module():
    print("\n--- 🛡️ Testing Anti-Fraud Module ---")
    try:
        service = RiskCheckService()
        # Report a fake fraudster
        service.report_fraud('email', 'fraudster@evil.com', 'Test report', 1)
        
        # Check risk
        result = service.check_order_risk({'customer_email': 'fraudster@evil.com'})
        print(f"✅ Risk check result: {result['risk_level']} (Score: {result['risk_score']})")
        if result['risk_score'] > 0:
            print("✅ Fraudster correctly identified")
        else:
            print("❌ Fraudster missed")
    except Exception as e:
        print(f"❌ Fraud test failed: {e}")

def verify_all():
    print("=== 🧪 VÉRIFICATION PHASE 3 : SCALE & AUTOMATISATION ===")
    test_stripe_integration()
    test_sav_integration()
    test_fraud_module()
    print("\n=== ✨ TOUTES LES VÉRIFICATIONS SONT TERMINÉES ===")

if __name__ == "__main__":
    verify_all()
