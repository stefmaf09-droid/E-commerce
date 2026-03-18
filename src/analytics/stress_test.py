import time
import pandas as pd
import numpy as np
import logging

from dispute_detector import DisputeDetectionEngine

logger = logging.getLogger(__name__)

class StressTestEngine:
    """Moteur de test de charge extrême pour valider la performance du système."""
    
    def __init__(self):
        self.detector = DisputeDetectionEngine()

    def generate_stress_data(self, num_orders: int = 10000) -> pd.DataFrame:
        """Génère un dataset massif de commandes simulées."""
        print(f"📦 Génération de {num_orders:,} commandes de test...")
        
        carriers = ['Colissimo', 'Chronopost', 'UPS', 'DHL', 'FedEx', 'GLS', 'Mondial Relay']
        services = ['Standard', 'Express', 'Premium']
        statuses = ['Delivered', 'Delivered_Late', 'Lost', 'Pending']
        
        data = {
            'order_id': [f"STRESS-{i}" for i in range(num_orders)],
            'carrier': np.random.choice(carriers, num_orders),
            'service': np.random.choice(services, num_orders),
            'delay_days': np.random.randint(0, 15, num_orders),
            'status': np.random.choice(statuses, num_orders),
            'pod_valid': np.random.choice([True, False], num_orders, p=[0.9, 0.1]),
            'shipping_cost': np.random.uniform(5.0, 45.0, num_orders),
            'product_value': np.random.uniform(20.0, 500.0, num_orders),
            'order_date': ['2026-01-01'] * num_orders,
            'has_pod': [True] * num_orders,
            'pod_gps_match': [True] * num_orders
        }
        
        return pd.DataFrame(data)

    def run_benchmark(self, num_orders: int = 10000):
        """Lance l'analyse et mesure le temps de traitement."""
        df = self.generate_stress_data(num_orders)
        
        print(f"🤖 Lancement de l'analyse IA sur {num_orders:,} commandes...")
        start_time = time.time()
        
        results = []
        for _, row in df.iterrows():
            results.append(self.detector.analyze_order(row))
            
        end_time = time.time()
        duration = end_time - start_time
        
        orders_per_second = num_orders / duration
        
        print("\n" + "="*40)
        print("📊 RÉSULTATS DU STRESS TEST")
        print("="*40)
        print(f"⏱️  Temps total : {duration:.2f} secondes")
        print(f"⚡ Vitesse : {orders_per_second:.1f} commandes / seconde")
        print(f"📈 Capacité théorique : {orders_per_second * 3600 * 24:,.0f} commandes / jour")
        print("="*40)
        
        # Analyse des résultats
        results_df = pd.DataFrame(results)
        disputes_found = results_df[results_df['has_dispute'] == True]
        print(f"🎯 Litiges détectés : {len(disputes_found):,} ({len(disputes_found)/num_orders*100:.1f}%)")
        print(f"💰 Potentiel financier : {disputes_found['total_recoverable'].sum():,.2f} €")
        
        return {
            'duration': duration,
            'rate': orders_per_second,
            'disputes': len(disputes_found)
        }

if __name__ == "__main__":
    test_engine = StressTestEngine()
    test_engine.run_benchmark(1000) # Petit test par défaut
