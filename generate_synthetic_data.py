"""
Générateur de Données Synthétiques pour Agent de Recouvrement Logistique
========================================================================

Génère un dataset réaliste de 5000 commandes e-commerce avec litiges transporteurs
pour prototyper le moteur de détection et de recouvrement.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import json

# Configuration des seeds pour reproductibilité
np.random.seed(42)
random.seed(42)

class SyntheticDataGenerator:
    """Générateur de données synthétiques réalistes pour e-commerce."""
    
    def __init__(self, num_orders=5000):
        self.num_orders = num_orders
        self.start_date = datetime(2025, 10, 1)
        self.end_date = datetime(2026, 1, 15)
        
        # Transporteurs français avec leurs caractéristiques
        self.carriers = {
            'Chronopost': {'on_time_rate': 0.85, 'lost_rate': 0.02, 'avg_delay': 1.5},
            'Colissimo': {'on_time_rate': 0.80, 'lost_rate': 0.03, 'avg_delay': 2.0},
            'Mondial Relay': {'on_time_rate': 0.75, 'lost_rate': 0.04, 'avg_delay': 2.5},
            'UPS': {'on_time_rate': 0.88, 'lost_rate': 0.015, 'avg_delay': 1.2},
            'DHL': {'on_time_rate': 0.90, 'lost_rate': 0.01, 'avg_delay': 1.0},
            'La Poste': {'on_time_rate': 0.78, 'lost_rate': 0.035, 'avg_delay': 2.2},
        }
        
        # Services de livraison
        self.services = {
            'Standard': {'promised_days': 5, 'cost': 5.90},
            'Express': {'promised_days': 2, 'cost': 12.90},
            'Premium': {'promised_days': 1, 'cost': 18.90},
        }
        
        # Produits types avec valeurs moyennes
        self.products = {
            'Vêtement': {'avg_price': 45, 'std': 20},
            'Cosmétique': {'avg_price': 35, 'std': 15},
            'High-Tech': {'avg_price': 150, 'std': 80},
            'Livre': {'avg_price': 20, 'std': 10},
            'Chaussure': {'avg_price': 65, 'std': 30},
        }
        
        # Villes françaises (distribution réaliste)
        self.cities = [
            'Paris', 'Lyon', 'Marseille', 'Toulouse', 'Nice', 'Nantes', 
            'Strasbourg', 'Montpellier', 'Bordeaux', 'Lille', 'Rennes', 
            'Reims', 'Le Havre', 'Saint-Étienne', 'Toulon', 'Grenoble'
        ]
        
    def generate_order_date(self):
        """Génère une date de commande aléatoire."""
        delta = self.end_date - self.start_date
        random_days = random.randint(0, delta.days)
        return self.start_date + timedelta(days=random_days)
    
    def generate_delivery_status(self, carrier, service, order_date):
        """Génère un statut de livraison réaliste avec anomalies potentielles."""
        carrier_info = self.carriers[carrier]
        service_info = self.services[service]
        
        # Date de livraison promise
        promised_delivery = order_date + timedelta(days=service_info['promised_days'])
        
        # Simulation du comportement réel
        rand = random.random()
        
        if rand < carrier_info['on_time_rate']:
            # Livraison à temps
            actual_delivery = promised_delivery - timedelta(hours=random.randint(0, 24))
            status = 'Delivered'
            delay_days = 0
            issue = None
            
        elif rand < carrier_info['on_time_rate'] + carrier_info['lost_rate']:
            # Colis perdu
            actual_delivery = None
            status = 'Lost'
            delay_days = random.randint(7, 21)
            issue = 'Package_Lost'
            
        else:
            # Livraison en retard
            delay_days = int(np.random.exponential(carrier_info['avg_delay'])) + 1
            actual_delivery = promised_delivery + timedelta(days=delay_days)
            status = 'Delivered_Late'
            issue = 'Delayed_Delivery'
        
        return {
            'status': status,
            'promised_date': promised_delivery,
            'actual_date': actual_delivery,
            'delay_days': delay_days,
            'issue': issue
        }
    
    def generate_pod_quality(self, status):
        """Génère la qualité de la preuve de livraison (POD)."""
        if status == 'Lost':
            return {
                'has_pod': False,
                'photo_quality': None,
                'gps_match': None,
                'signature_valid': None,
                'pod_valid': False
            }
        
        # Pour les livraisons (à temps ou en retard)
        # 20% des POD ont des problèmes
        has_issue = random.random() < 0.20
        
        if has_issue:
            issue_type = random.choice([
                'poor_photo',      # Photo floue/rue
                'wrong_gps',       # GPS incohérent
                'invalid_signature' # Signature invalide
            ])
            
            return {
                'has_pod': True,
                'photo_quality': 'Poor' if issue_type == 'poor_photo' else 'Good',
                'gps_match': False if issue_type == 'wrong_gps' else True,
                'signature_valid': False if issue_type == 'invalid_signature' else True,
                'pod_valid': False
            }
        else:
            return {
                'has_pod': True,
                'photo_quality': 'Good',
                'gps_match': True,
                'signature_valid': True,
                'pod_valid': True
            }
    
    def calculate_recoverable_amount(self, row):
        """Calcule le montant récupérable selon les règles de litige."""
        recoverable = 0.0
        reason = []
        
        # Règle 1: Retard sur service Express/Premium
        if row['delay_days'] > 2 and row['service'] in ['Express', 'Premium']:
            recoverable += row['shipping_cost']
            reason.append('Late_Delivery_Premium_Service')
        
        # Règle 2: Colis perdu
        if row['status'] == 'Lost':
            recoverable += row['product_value'] + row['shipping_cost']
            reason.append('Package_Lost_Full_Refund')
        
        # Règle 3: POD invalide (preuve de livraison contestable)
        if row['status'] in ['Delivered', 'Delivered_Late'] and not row['pod_valid']:
            # Si client conteste + POD invalide = traitable comme perte
            if random.random() < 0.30:  # 30% des POD invalides deviennent litiges
                recoverable += row['product_value'] * 0.5  # Récupération partielle
                reason.append('Invalid_POD_Customer_Claim')
        
        # Règle 4: Retard significatif (>5 jours pour Standard)
        if row['delay_days'] > 5 and row['service'] == 'Standard':
            recoverable += row['shipping_cost'] * 0.5  # Remboursement partiel
            reason.append('Significant_Delay_Standard')
        
        return recoverable, ', '.join(reason) if reason else None
    
    def generate_dataset(self):
        """Génère le dataset complet."""
        print(f"🔄 Génération de {self.num_orders} commandes synthétiques...")
        
        orders = []
        
        for order_id in range(1, self.num_orders + 1):
            # Données de base
            order_date = self.generate_order_date()
            carrier = random.choice(list(self.carriers.keys()))
            service = random.choices(
                list(self.services.keys()),
                weights=[0.60, 0.30, 0.10],  # Standard plus fréquent
                k=1
            )[0]
            
            product_type = random.choice(list(self.products.keys()))
            product_info = self.products[product_type]
            product_value = max(5, np.random.normal(product_info['avg_price'], product_info['std']))
            
            city = random.choice(self.cities)
            
            # Génération du statut de livraison
            delivery_info = self.generate_delivery_status(carrier, service, order_date)
            
            # Génération POD
            pod_info = self.generate_pod_quality(delivery_info['status'])
            
            # Construction de la ligne
            order = {
                'order_id': f'ORD-{order_id:06d}',
                'order_date': order_date.strftime('%Y-%m-%d'),
                'customer_city': city,
                'product_type': product_type,
                'product_value': round(product_value, 2),
                'carrier': carrier,
                'service': service,
                'shipping_cost': self.services[service]['cost'],
                'promised_delivery_days': self.services[service]['promised_days'],
                'promised_date': delivery_info['promised_date'].strftime('%Y-%m-%d'),
                'actual_date': delivery_info['actual_date'].strftime('%Y-%m-%d') if delivery_info['actual_date'] else None,
                'status': delivery_info['status'],
                'delay_days': delivery_info['delay_days'],
                'issue_type': delivery_info['issue'],
                'has_pod': pod_info['has_pod'],
                'pod_photo_quality': pod_info['photo_quality'],
                'pod_gps_match': pod_info['gps_match'],
                'pod_signature_valid': pod_info['signature_valid'],
                'pod_valid': pod_info['pod_valid'],
            }
            
            # Calcul du montant récupérable
            recoverable, reason = self.calculate_recoverable_amount(order)
            order['recoverable_amount'] = round(recoverable, 2)
            order['recovery_reason'] = reason
            
            orders.append(order)
            
            if order_id % 1000 == 0:
                print(f"  ✓ {order_id} commandes générées...")
        
        df = pd.DataFrame(orders)
        print(f"✅ Dataset généré avec succès!")
        
        return df
    
    def generate_statistics(self, df):
        """Génère des statistiques sur le dataset."""
        stats = {
            'total_orders': len(df),
            'total_issues': len(df[df['issue_type'].notna()]),
            'total_recoverable': df['recoverable_amount'].sum(),
            'avg_recoverable_per_issue': df[df['recoverable_amount'] > 0]['recoverable_amount'].mean(),
            'breakdown_by_carrier': df.groupby('carrier').agg({
                'order_id': 'count',
                'recoverable_amount': 'sum'
            }).to_dict(),
            'breakdown_by_issue': df[df['issue_type'].notna()].groupby('issue_type').agg({
                'order_id': 'count',
                'recoverable_amount': 'sum'
            }).to_dict(),
            'roi_potential': {
                'total_money_left_on_table': df['recoverable_amount'].sum(),
                'num_recoverable_cases': len(df[df['recoverable_amount'] > 0]),
                'success_fee_20pct': df['recoverable_amount'].sum() * 0.20
            }
        }
        
        return stats


def main():
    """Point d'entrée principal."""
    print("=" * 70)
    print("  GÉNÉRATEUR DE DONNÉES SYNTHÉTIQUES - AGENT RECOUVREMENT LOGISTIQUE")
    print("=" * 70)
    print()
    
    # Génération
    generator = SyntheticDataGenerator(num_orders=5000)
    df = generator.generate_dataset()
    
    # Sauvegarde
    output_file = 'data/synthetic_orders.csv'
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n💾 Dataset sauvegardé: {output_file}")
    
    # Statistiques
    print("\n" + "=" * 70)
    print("  STATISTIQUES DU DATASET")
    print("=" * 70)
    
    stats = generator.generate_statistics(df)
    
    print(f"\n📊 Vue d'ensemble:")
    print(f"   Total commandes: {stats['total_orders']:,}")
    print(f"   Commandes avec problème: {stats['total_issues']:,} ({stats['total_issues']/stats['total_orders']*100:.1f}%)")
    print(f"   Cas récupérables: {stats['roi_potential']['num_recoverable_cases']:,}")
    
    print(f"\n💰 Potentiel de recouvrement:")
    print(f"   Montant total récupérable: {stats['total_recoverable']:,.2f} €")
    print(f"   Moyenne par cas: {stats['avg_recoverable_per_issue']:.2f} €")
    print(f"   Success Fee (20%): {stats['roi_potential']['success_fee_20pct']:,.2f} €")
    
    print(f"\n🚚 Répartition par transporteur:")
    for carrier, data in stats['breakdown_by_carrier']['order_id'].items():
        recoverable = stats['breakdown_by_carrier']['recoverable_amount'][carrier]
        print(f"   {carrier}: {data} commandes → {recoverable:,.2f} € récupérable")
    
    print(f"\n⚠️  Répartition par type de problème:")
    if stats['breakdown_by_issue']['order_id']:
        for issue, count in stats['breakdown_by_issue']['order_id'].items():
            recoverable = stats['breakdown_by_issue']['recoverable_amount'][issue]
            print(f"   {issue}: {count} cas → {recoverable:,.2f} €")
    
    # Sauvegarde des stats
    stats_file = 'data/dataset_statistics.json'
    with open(stats_file, 'w', encoding='utf-8') as f:
        # Conversion pour JSON (problème avec types numpy)
        stats_json = json.loads(json.dumps(stats, default=str))
        json.dump(stats_json, f, indent=2, ensure_ascii=False)
    print(f"\n📄 Statistiques sauvegardées: {stats_file}")
    
    print("\n" + "=" * 70)
    print("✅ GÉNÉRATION TERMINÉE AVEC SUCCÈS!")
    print("=" * 70)


if __name__ == '__main__':
    main()
