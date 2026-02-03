
import os
import sys

# Add root to path
sys.path.append(os.getcwd())

from src.integrations.singpost_connector import SingPostConnector
from src.integrations.hkpost_connector import HKPostConnector
from src.ai.predictor import AIPredictor

def verify_phase6_3():
    print("=== 🧪 VÉRIFICATION PHASE 6.3 : APAC CARRIER CONNECTORS ===")
    
    # 1. Test Connectors instantiation
    print("\n--- 🌐 APAC Connectors ---")
    sp = SingPostConnector(credentials={})
    hk = HKPostConnector(credentials={})
    print(f"✅ SingPost Connector: {sp.platform_name}")
    print(f"✅ HK Post Connector: {hk.platform_name}")
    
    # 2. Test Rules
    print("\n--- ⚖️ Local Regulations Check ---")
    sg_rules = sp.get_sg_specific_rules()
    print(f"✅ SG PDPA Masking: {sg_rules['mask_nric']}")
    print(f"✅ HK Customs Advice: {hk.get_hk_customs_advice()[:30]}...")

    # 3. Test AI Predictor for new carriers
    print("\n--- 🤖 AI Predictor (APAC update) ---")
    predictor = AIPredictor()
    pred_sp = predictor.predict_success({'carrier': 'SingPost', 'dispute_type': 'lost'})
    pred_hk = predictor.predict_success({'carrier': 'HK Post', 'dispute_type': 'late_delivery'})
    print(f"✅ SingPost Success Proba: {pred_sp['probability']*100}%")
    print(f"✅ HK Post Success Proba: {pred_hk['probability']*100}%")

    print("\n=== ✨ VÉRIFICATION PHASE 6.3 TERMINÉE ===")

if __name__ == "__main__":
    verify_phase6_3()
