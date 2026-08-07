
import os
import sys
import pandas as pd

# Add root to path
sys.path.append(os.getcwd())

from src.analytics.carrier_benchmark import CarrierBenchmarkService

def verify_phase5_3():
    print("=== 🧪 VÉRIFICATION PHASE 5.3 : SMART BENCHMARKING ===")
    
    svc = CarrierBenchmarkService()
    
    # 1. Test Leaderboard
    print("\n--- 📊 Market Leaderboard ---")
    df = svc.get_market_leaderboard()
    print(f"Top Carrier: {df.iloc[0]['carrier']} (Score: {df.iloc[0]['reliability_score']}%)")
    print(f"Bottom Carrier: {df.iloc[-1]['carrier']} (Score: {df.iloc[-1]['reliability_score']}%)")
    
    # 2. Test Recommendation
    print("\n--- 💡 Route Recommendation ---")
    rec = svc.get_route_recommendation('DE')
    print(f"✅ Recommendation for DE: {rec['best']}")
    print(f"✅ Reasoning: {rec['reason']}")

    # 3. Check UI integrations
    print("\n--- 🖼️ UI Integrations (Grep check) ---")
    with open('client_dashboard.py', 'r', encoding='utf-8') as f:
        if 'Market Insights' in f.read():
            print("✅ Client Dashboard: 'Market Insights' UI found.")
            
    with open('admin_control_tower.py', 'r', encoding='utf-8') as f:
        if 'CarrierBenchmarkService' in f.read():
            print("✅ Admin Control Tower: Benchmark logic found.")

    print("\n=== ✨ VÉRIFICATION PHASE 5.3 TERMINÉE ===")

if __name__ == "__main__":
    verify_phase5_3()
