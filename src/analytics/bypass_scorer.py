
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from src.ai.predictor import AIPredictor

logger = logging.getLogger(__name__)

class BypassScorer:
    """
    Moteur de scoring IA (Heuristique & Statistique) pour la détection de fraude/bypass
    et l'estimation des chances de succès.
    """
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.predictor = AIPredictor()

    def calculate_client_risk_score(self, client_id: int) -> float:
        """
        Calcule un score de risque de 0 (sûr) à 100 (suspect).
        
        Facteurs:
        - Ratio de réclamations marquées 'unpaid' alors que le tracking est 'compensated'
        - Historique de détection de bypass (alertes système)
        - Volume de réclamations vs âge du compte
        - Bypass density (ratio alertes/total)
        """
        score = 0
        
        conn = self.db.get_connection()
        try:
            # 1. Analyse de l'historique des alertes
            alerts_count = conn.execute(
                "SELECT COUNT(*) FROM system_alerts WHERE related_resource_type = 'client' AND related_resource_id = ? AND alert_type = 'bypass_detected' AND is_resolved = 0",
                (client_id,)
            ).fetchone()[0]
            
            # Chaque alerte non résolue ajoute 25 points
            score += min(alerts_count * 25, 60)
            
            # 2. Analyse des réclamations suspectes (non-déclarées)
            suspicious_claims = conn.execute("""
                SELECT COUNT(*) FROM claims 
                WHERE client_id = ? 
                AND payment_status = 'unpaid' 
                AND automation_status = 'action_required'
            """, (client_id,)).fetchone()[0]
            
            score += min(suspicious_claims * 10, 30)
            
            # 3. Bypass Density (Nouveauté)
            total_claims = conn.execute("SELECT COUNT(*) FROM claims WHERE client_id = ?", (client_id,)).fetchone()[0]
            if total_claims > 10:
                density = alerts_count / total_claims
                if density > 0.1: # Plus de 10% d'alertes
                    score += 20

            # 4. Ancienneté (plus le client est ancien sans incident, plus on a confiance)
            client = conn.execute("SELECT created_at FROM clients WHERE id = ?", (client_id,)).fetchone()
            if client:
                try:
                    created_at = datetime.fromisoformat(client[0])
                    days_active = (datetime.now() - created_at).days
                    if days_active > 90 and alerts_count == 0: 
                        score -= 15
                except (ValueError, TypeError):
                    pass
                    
        finally:
            conn.close()
            
        return max(0, min(score, 100))

    def estimate_success_probability(self, carrier: str, dispute_type: str, amount: float = 0.0) -> float:
        """
        Prédit la probabilité de succès (0.0 à 1.0) via un modèle hybride:
        - 70% Base IA (Predictor)
        - 30% Historique réel du système
        """
        # 1. Base IA (70%)
        ai_prediction = self.predictor.predict_success({
            'carrier': carrier,
            'dispute_type': dispute_type,
            'amount_recoverable': amount
        })
        ai_proba = ai_prediction['probability']
        
        # 2. Historique local (30%)
        hist_proba = ai_proba # Fallback
        conn = self.db.get_connection()
        try:
            stats = conn.execute("""
                SELECT 
                    SUM(CASE WHEN status = 'accepted' THEN 1 ELSE 0 END) as accepted,
                    COUNT(*) as total
                FROM claims 
                WHERE carrier = ? AND dispute_type = ?
            """, (carrier, dispute_type)).fetchone()
            
            if stats and stats[1] >= 3: 
                hist_proba = stats[0] / stats[1]
                
            # 3. Facteur de rejet par transporteur (Nouveauté)
            rejection_factor = self._calculate_rejection_factor(conn, carrier)
            
            final_proba = (0.7 * ai_proba) + (0.3 * hist_proba)
            return max(0.05, min(0.98, final_proba - rejection_factor))
            
        finally:
            conn.close()

    def _calculate_rejection_factor(self, conn, carrier: str) -> float:
        """Calcule un malus basé sur le taux de rejet récent du transporteur."""
        last_month = (datetime.now() - timedelta(days=30)).isoformat()
        res = conn.execute("""
            SELECT 
                SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected,
                COUNT(*) as total
            FROM claims 
            WHERE carrier = ? AND updated_at > ?
        """, (carrier, last_month)).fetchone()
        
        if res and res[1] > 5:
            rejection_rate = res[0] / res[1]
            if rejection_rate > 0.5: # Transporteur en mode "refus systématique"
                return 0.15
            elif rejection_rate > 0.3:
                return 0.05
        return 0.0

    def get_client_trust_label(self, score: float) -> Dict[str, str]:
        """Retourne un label et une couleur pour le dashboard admin."""
        if score < 15:
            return {"label": "Elite", "color": "blue", "description": "Client de confiance, traitement VIP."}
        elif score < 30:
            return {"label": "Standard", "color": "green", "description": "Comportement normal."}
        elif score < 60:
            return {"label": "Vigilance", "color": "orange", "description": "Anomalies détectées, monitoring accru."}
        else:
            return {"label": "CRITIQUE", "color": "red", "description": "Forte suspicion de bypass. Gel des paiements conseillé."}
