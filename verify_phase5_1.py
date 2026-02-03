
import os
import sys

# Add root to path
sys.path.append(os.getcwd())

from src.ai.predictor import AIPredictor

def verify_phase5_1():
    print("=== 🧪 VÉRIFICATION PHASE 5.1 : PREDICTIVE INTELLIGENCE ===")
    
    predictor = AIPredictor()
    
    # 1. Test Prediction Logic
    print("\n--- 🤖 AI Predictor Logic ---")
    case = {'carrier': 'UPS', 'dispute_type': 'late_delivery', 'amount_recoverable': 150.0}
    prediction = predictor.predict_success(case)
    print(f"Case: {case['carrier']} - {case['dispute_type']}")
    print(f"✅ Success Proba: {prediction['probability']*100}%")
    print(f"✅ Predicted Days: {prediction['predicted_days']} days")
    print(f"✅ Reasoning: {prediction['reasoning']}")
    
    # 2. Test Forecasting
    print("\n--- 📈 Global Forecasting ---")
    mock_batch = [case, {'carrier': 'FedEx', 'dispute_type': 'damaged', 'amount_recoverable': 500.0}]
    forecasts = predictor.get_forecasted_cashflow(mock_batch)
    print(f"✅ Total Potential: {forecasts['total_potential_raw']}€")
    print(f"✅ Weighted Expected: {forecasts['weighted_expected_recovery']}€")
    
    # 3. Check UI integrations (grep)
    print("\n--- 🖼️ UI Integrations (Dashboard check) ---")
    with open('client_dashboard.py', 'r', encoding='utf-8') as f:
        content = f.read()
        if 'Confiance IA' in content:
            print("✅ Client Dashboard: 'Confiance IA' column found.")
            
    with open('admin_control_tower.py', 'r', encoding='utf-8') as f:
        content = f.read()
        if 'render_forecasting' in content:
            print("✅ Admin Control Tower: 'render_forecasting' function found.")

    print("\n=== ✨ VÉRIFICATION PHASE 5.1 TERMINÉE ===")

if __name__ == "__main__":
    verify_phase5_1()
