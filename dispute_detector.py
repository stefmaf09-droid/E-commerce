"""
Moteur de Détection de Litiges - Agent de Recouvrement Logistique
==================================================================

Analyse les commandes e-commerce et détecte automatiquement les cas
où de l'argent peut être récupéré auprès des transporteurs.
"""

import pandas as pd
import json
from datetime import datetime
from typing import Dict, List, Tuple


class DisputeDetectionEngine:
    """Moteur de détection et d'analyse des litiges transporteurs."""
    
    def __init__(self):
        """Initialise le moteur avec les règles de recouvrement."""
        
        # Règles de recouvrement par type de problème
        self.recovery_rules = {
            'express_delay': {
                'name': 'Retard Service Express/Premium',
                'condition': lambda row: row['delay_days'] > 2 and row['service'] in ['Express', 'Premium'],
                'recovery': lambda row: row['shipping_cost'],
                'priority': 'HIGH',
                'success_rate': 0.95,
                'legal_basis': 'Violation engagement contractuel délai garanti'
            },
            'package_lost': {
                'name': 'Colis Perdu',
                'condition': lambda row: row['status'] == 'Lost',
                'recovery': lambda row: row['product_value'] + row['shipping_cost'],
                'priority': 'CRITICAL',
                'success_rate': 0.98,
                'legal_basis': 'Article L133-3 Code de Commerce - Responsabilité transporteur'
            },
            'invalid_pod': {
                'name': 'Preuve de Livraison Invalide',
                'condition': lambda row: row['status'] in ['Delivered', 'Delivered_Late'] and not row['pod_valid'],
                'recovery': lambda row: row['product_value'] * 0.5,  # Récupération partielle
                'priority': 'MEDIUM',
                'success_rate': 0.70,
                'legal_basis': 'Défaut de preuve de remise conforme (CGV transporteur)'
            },
            'standard_delay': {
                'name': 'Retard Significatif Service Standard',
                'condition': lambda row: row['delay_days'] > 5 and row['service'] == 'Standard',
                'recovery': lambda row: row['shipping_cost'] * 0.5,
                'priority': 'LOW',
                'success_rate': 0.60,
                'legal_basis': 'Manquement obligation de moyens'
            },
            'wrong_gps': {
                'name': 'GPS Incohérent (Livraison contestable)',
                'condition': lambda row: row['has_pod'] and row['pod_gps_match'] == False,
                'recovery': lambda row: row['product_value'] * 0.3,
                'priority': 'MEDIUM',
                'success_rate': 0.65,
                'legal_basis': 'Preuve de livraison géolocalisée non conforme'
            }
        }
    
    def analyze_order(self, order: pd.Series) -> Dict:
        """Analyse une commande et détecte les opportunités de recouvrement."""
        
        disputes = []
        total_recoverable = 0.0
        
        from src.ai.predictor import AIPredictor
        predictor = AIPredictor()
        
        for rule_id, rule in self.recovery_rules.items():
            if rule['condition'](order):
                amount = rule['recovery'](order)
                
                if amount > 0:
                    # Appel au moteur prédictif Phase 5
                    prediction = predictor.predict_success({
                        'carrier': order['carrier'],
                        'dispute_type': rule_id,
                        'amount_recoverable': amount
                    })
                    
                    dispute = {
                        'rule_id': rule_id,
                        'rule_name': rule['name'],
                        'priority': rule['priority'],
                        'recoverable_amount': round(amount, 2),
                        'success_probability': prediction['probability'],
                        'predicted_days': prediction['predicted_days'],
                        'expected_recovery': round(amount * prediction['probability'], 2),
                        'legal_basis': rule['legal_basis'],
                        'ai_reasoning': prediction['reasoning']
                    }
                    disputes.append(dispute)
                    total_recoverable += amount
        
        return {
            'order_id': order['order_id'],
            'has_dispute': len(disputes) > 0,
            'num_disputes': len(disputes),
            'total_recoverable': round(total_recoverable, 2),
            'disputes': disputes,
            'carrier': order['carrier'],
            'order_date': order['order_date']
        }
    
    def process_dataset(self, csv_path: str) -> Tuple[pd.DataFrame, Dict]:
        """Traite l'ensemble du dataset et génère le rapport de recouvrement."""
        
        print("🔍 Chargement du dataset...")
        df = pd.read_csv(csv_path)
        print(f"   ✓ {len(df):,} commandes chargées\n")
        
        print("🤖 Analyse des litiges en cours...")
        results = []
        
        for idx, row in df.iterrows():
            result = self.analyze_order(row)
            results.append(result)
            
            if (idx + 1) % 1000 == 0:
                print(f"   ✓ {idx + 1:,} commandes analysées...")
        
        print(f"   ✓ Analyse terminée!\n")
        
        # Création du DataFrame de résultats
        results_df = pd.DataFrame(results)
        
        # Génération des statistiques
        stats = self._generate_statistics(results_df, results)
        
        return results_df, stats
    
    def _generate_statistics(self, results_df: pd.DataFrame, results: List[Dict]) -> Dict:
        """Génère les statistiques détaillées du recouvrement."""
        
        # Filtrer les cas avec litiges
        disputed = results_df[results_df['has_dispute'] == True]
        
        # Collecter tous les litiges
        all_disputes = []
        for result in results:
            if result['disputes']:
                for dispute in result['disputes']:
                    dispute_copy = dispute.copy()
                    dispute_copy['order_id'] = result['order_id']
                    dispute_copy['carrier'] = result['carrier']
                    all_disputes.append(dispute_copy)
        
        disputes_df = pd.DataFrame(all_disputes)
        
        stats = {
            'overview': {
                'total_orders': len(results_df),
                'disputed_orders': len(disputed),
                'dispute_rate': round(len(disputed) / len(results_df) * 100, 2),
                'total_recoverable': round(disputed['total_recoverable'].sum(), 2),
                'avg_per_dispute': round(disputed['total_recoverable'].mean(), 2),
            },
            'by_priority': {},
            'by_carrier': {},
            'by_rule': {},
            'roi_projection': {}
        }
        
        # Par priorité
        if not disputes_df.empty:
            for priority in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
                priority_disputes = disputes_df[disputes_df['priority'] == priority]
                if not priority_disputes.empty:
                    stats['by_priority'][priority] = {
                        'count': len(priority_disputes),
                        'total_recoverable': round(priority_disputes['recoverable_amount'].sum(), 2),
                        'expected_recovery': round(priority_disputes['expected_recovery'].sum(), 2)
                    }
        
        # Par transporteur
        if not disputed.empty:
            carrier_stats = disputed.groupby('carrier').agg({
                'order_id': 'count',
                'total_recoverable': 'sum'
            }).to_dict()
            
            for carrier in carrier_stats['order_id'].keys():
                stats['by_carrier'][carrier] = {
                    'disputed_orders': carrier_stats['order_id'][carrier],
                    'total_recoverable': round(carrier_stats['total_recoverable'][carrier], 2)
                }
        
        # Par règle de litige
        if not disputes_df.empty:
            rule_stats = disputes_df.groupby('rule_name').agg({
                'order_id': 'count',
                'recoverable_amount': 'sum',
                'expected_recovery': 'sum'
            }).to_dict()
            
            for rule_name in rule_stats['order_id'].keys():
                stats['by_rule'][rule_name] = {
                    'count': rule_stats['order_id'][rule_name],
                    'total_recoverable': round(rule_stats['recoverable_amount'][rule_name], 2),
                    'expected_recovery': round(rule_stats['expected_recovery'][rule_name], 2)
                }
        
        # Projection ROI
        total_recoverable = stats['overview']['total_recoverable']
        expected_recovery = disputes_df['expected_recovery'].sum() if not disputes_df.empty else 0
        
        stats['roi_projection'] = {
            'total_recoverable_optimistic': round(total_recoverable, 2),
            'total_recoverable_realistic': round(expected_recovery, 2),
            'success_fee_20pct': round(expected_recovery * 0.20, 2),
            'cost_per_case': 0.50,  # Coût IA vs 25-40€ humain
            'total_processing_cost': round(len(disputed) * 0.50, 2),
            'net_profit': round((expected_recovery * 0.20) - (len(disputed) * 0.50), 2)
        }
        
        return stats
    
    def generate_audit_report(self, stats: Dict, output_path: str = 'data/audit_report.txt'):
        """Génère un rapport d'audit lisible."""
        
        report = []
        report.append("=" * 80)
        report.append("  RAPPORT D'AUDIT - POTENTIEL DE RECOUVREMENT LOGISTIQUE")
        report.append("=" * 80)
        report.append("")
        
        # Vue d'ensemble
        report.append("📊 VUE D'ENSEMBLE")
        report.append("-" * 80)
        overview = stats['overview']
        report.append(f"   Total de commandes analysées: {overview['total_orders']:,}")
        report.append(f"   Commandes avec litiges détectés: {overview['disputed_orders']:,} ({overview['dispute_rate']}%)")
        report.append(f"   Montant total récupérable: {overview['total_recoverable']:,.2f} €")
        report.append(f"   Moyenne par litige: {overview['avg_per_dispute']:.2f} €")
        report.append("")
        
        # Par priorité
        if stats['by_priority']:
            report.append("🎯 RÉPARTITION PAR PRIORITÉ")
            report.append("-" * 80)
            for priority, data in sorted(stats['by_priority'].items()):
                report.append(f"   [{priority}] {data['count']} cas → {data['total_recoverable']:,.2f} € "
                             f"(attendu: {data['expected_recovery']:,.2f} €)")
            report.append("")
        
        # Par transporteur
        if stats['by_carrier']:
            report.append("🚚 RÉPARTITION PAR TRANSPORTEUR")
            report.append("-" * 80)
            carrier_sorted = sorted(stats['by_carrier'].items(), 
                                   key=lambda x: x[1]['total_recoverable'], 
                                   reverse=True)
            for carrier, data in carrier_sorted:
                report.append(f"   {carrier}: {data['disputed_orders']} litiges → {data['total_recoverable']:,.2f} €")
            report.append("")
        
        # Par type de litige
        if stats['by_rule']:
            report.append("⚖️  RÉPARTITION PAR TYPE DE LITIGE")
            report.append("-" * 80)
            rule_sorted = sorted(stats['by_rule'].items(), 
                                key=lambda x: x[1]['total_recoverable'], 
                                reverse=True)
            for rule, data in rule_sorted:
                report.append(f"   {rule}:")
                report.append(f"      • Cas détectés: {data['count']}")
                report.append(f"      • Montant récupérable: {data['total_recoverable']:,.2f} €")
                report.append(f"      • Récupération attendue: {data['expected_recovery']:,.2f} €")
            report.append("")
        
        # ROI Projection
        report.append("💰 PROJECTION ROI (MODÈLE SUCCESS FEE 20%)")
        report.append("-" * 80)
        roi = stats['roi_projection']
        report.append(f"   Scénario optimiste (100% récupération): {roi['total_recoverable_optimistic']:,.2f} €")
        report.append(f"   Scénario réaliste (taux succès moyen): {roi['total_recoverable_realistic']:,.2f} €")
        report.append(f"   Commission Success Fee (20%): {roi['success_fee_20pct']:,.2f} €")
        report.append(f"   Coût de traitement IA: {roi['total_processing_cost']:,.2f} €")
        report.append(f"   Profit net estimé: {roi['net_profit']:,.2f} €")
        report.append("")
        
        # Comparaison avec traitement humain
        report.append("📈 COMPARAISON TRAITEMENT HUMAIN vs IA")
        report.append("-" * 80)
        num_cases = overview['disputed_orders']
        human_cost = num_cases * 30  # Coût moyen humain: 30€/cas
        ia_cost = roi['total_processing_cost']
        savings = human_cost - ia_cost
        
        report.append(f"   Coût traitement humain: {human_cost:,.2f} € ({num_cases} cas × 30€)")
        report.append(f"   Coût traitement IA: {ia_cost:,.2f} € ({num_cases} cas × 0.50€)")
        report.append(f"   Économie opérationnelle: {savings:,.2f} € ({savings/human_cost*100:.1f}%)")
        report.append("")
        
        report.append("=" * 80)
        report.append("✅ CONCLUSION: Argent laissé sur la table récupérable via automatisation IA")
        report.append("=" * 80)
        
        report_text = "\n".join(report)
        
        # Sauvegarde
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        return report_text


def main():
    """Point d'entrée principal."""
    
    print("=" * 80)
    print("  MOTEUR DE DÉTECTION DE LITIGES - AGENT RECOUVREMENT LOGISTIQUE")
    print("=" * 80)
    print()
    
    # Initialisation
    engine = DisputeDetectionEngine()
    
    # Traitement
    results_df, stats = engine.process_dataset('data/synthetic_orders.csv')
    
    # Sauvegarde des résultats
    results_df.to_csv('data/dispute_analysis.csv', index=False, encoding='utf-8-sig')
    print(f"💾 Résultats sauvegardés: data/dispute_analysis.csv\n")
    
    # Sauvegarde des statistiques
    with open('data/dispute_statistics.json', 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    print(f"💾 Statistiques sauvegardées: data/dispute_statistics.json\n")
    
    # Génération du rapport
    report = engine.generate_audit_report(stats)
    print(report)
    print(f"\n💾 Rapport d'audit sauvegardé: data/audit_report.txt")
    
    print("\n" + "=" * 80)
    print("✅ ANALYSE TERMINÉE AVEC SUCCÈS!")
    print("=" * 80)


if __name__ == '__main__':
    main()
