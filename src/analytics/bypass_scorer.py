
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class BypassScorer:
    """
    Moteur de scoring IA (Heuristique & Statistique) pour la détection de fraude/bypass
    et l'estimation des chances de succès.
    """
    
    def __init__(self, db_manager):
        self.db = db_manager

    def calculate_client_risk_score(self, client_id: int) -> float:
        """
        Calcule un score de risque de 0 (sûr) à 100 (suspect).
        
        Facteurs:
        - Ratio de réclamations marquées 'unpaid' alors que le tracking est 'compensated'
        - Historique de détection de bypass (alertes système)
        - Volume de réclamations vs âge du compte
        """
        score = 0
        
        # 1. Analyse de l'historique des alertes
        conn = self.db.get_connection()
        try:
            alerts_count = conn.execute(
                "SELECT COUNT(*) FROM system_alerts WHERE related_resource_type = 'client' AND related_resource_id = ? AND alert_type = 'bypass_detected'",
                (client_id,)
            ).fetchone()[0]
            
            # Chaque alerte ajoute 25 points
            score += min(alerts_count * 25, 50)
            
            # 2. Analyse des réclamations suspectes (non-déclarées)
            # Dossiers où on a détecté un bypass mais le client n'a pas mis à jour
            suspicious_claims = conn.execute("""
                SELECT COUNT(*) FROM claims 
                WHERE client_id = ? 
                AND payment_status = 'unpaid' 
                AND automation_status = 'action_required'
            """, (client_id,)).fetchone()[0]
            
            score += min(suspicious_claims * 15, 40)
            
            # 3. Ancienneté (plus le client est ancien sans incident, plus on a confiance)
            client = conn.execute("SELECT created_at FROM clients WHERE id = ?", (client_id,)).fetchone()
            if client:
                created_at = datetime.fromisoformat(client[0])
                days_active = (datetime.now() - created_at).days
                if days_active > 90: # Vétéran (3 mois)
                    score -= 10
                    
        finally:
            conn.close()
            
        return max(0, min(score, 100))

    def estimate_success_probability(self, carrier: str, dispute_type: str) -> float:
        """
        Prédit la probabilité de succès (0.0 à 1.0) basée sur les données historiques.
        """
        # Historique par transporteur/type
        conn = self.db.get_connection()
        try:
            stats = conn.execute("""
                SELECT 
                    SUM(CASE WHEN status = 'accepted' THEN 1 ELSE 0 END) as accepted,
                    COUNT(*) as total
                FROM claims 
                WHERE carrier = ? AND dispute_type = ?
            """, (carrier, dispute_type)).fetchone()
            
            if stats and stats[1] > 5: # Besoin d'un minimum de data
                return stats[0] / stats[1]
            
            # Valeurs par défaut basées sur les benchmarks du marché
            defaults = {
                'late_delivery': 0.95,
                'lost': 0.85,
                'damaged': 0.45,
                'invalid_pod': 0.30
            }
            return defaults.get(dispute_type, 0.50)
        finally:
            conn.close()

    def get_client_trust_label(self, score: float) -> Dict[str, str]:
        """Retourne un label et une couleur pour le dashboard admin."""
        if score < 20:
            return {"label": "Excellent", "color": "green"}
        elif score < 50:
            return {"label": "Vigilance", "color": "orange"}
        else:
            return {"label": "CRITIQUE", "color": "red"}
