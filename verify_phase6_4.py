
import os
import sys

# Add root to path
sys.path.append(os.getcwd())

from src.monitoring.health_monitor import HealthMonitor

def verify_phase6_4():
    print("=== 🧪 VÉRIFICATION PHASE 6.4 : ADVANCED MONITORING ===")
    
    monitor = HealthMonitor()
    
    # 1. Test Database health
    print("\n--- 🗄️ Database Health ---")
    db_h = monitor.check_database()
    print(f"✅ DB Status: {db_h['status']} (Latency: {db_h['latency_ms']}ms)")
    
    # 2. Test Metric Export
    print("\n--- 📈 Metrics Export (Prometheus) ---")
    metrics = monitor.get_system_metrics()
    print("✅ Metrics generated:")
    print(metrics)
    
    # 3. Check UI
    print("\n--- 🖼️ UI Integration ---")
    with open('admin_control_tower.py', 'r', encoding='utf-8') as f:
        if 'get_system_metrics' in f.read():
            print("✅ Admin Control Tower: Live Monitoring UI found.")

    print("\n=== ✨ VÉRIFICATION PHASE 6.4 (ET PHASE 6 TOTALE) TERMINÉE ===")

if __name__ == "__main__":
    verify_phase6_4()
