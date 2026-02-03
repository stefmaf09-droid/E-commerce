
import logging
from typing import Dict, Any, Optional
from src.database.database_manager import get_db_manager

logger = logging.getLogger(__name__)

class RiskCheckService:
    """Service d'analyse de risque pré-expédition."""
    
    def __init__(self, db_manager=None):
        self.db = db_manager or get_db_manager()

    def check_order_risk(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyse une commande pour détecter des risques de fraude ou de litige futur.
        """
        email = order_data.get('customer_email')
        address = order_data.get('delivery_address')
        phone = order_data.get('customer_phone')
        
        risk_score = 0
        reasons = []
        
        # 1. Véron dans le registre global de fraude
        entities = [
            ('email', email),
            ('address', address),
            ('phone', phone)
        ]
        
        conn = self.db.get_connection()
        for entity_type, value in entities:
            if not value: continue
            
            match = conn.execute(
                "SELECT risk_level, reason FROM global_fraud_registry WHERE entity_type = ? AND entity_value = ?",
                (entity_type, value)
            ).fetchone()
            
            if match:
                level = match['risk_level']
                risk_score += self._level_to_score(level)
                reasons.append(f"Entity {entity_type} matched in fraud registry: {match['reason']}")
        
        conn.close()
        
        # 2. Analyse comportementale simple (Multi-commandes rapides)
        # (Simulation de logique métier)
        
        return {
            'risk_score': min(risk_score, 100),
            'risk_level': self._score_to_level(risk_score),
            'reasons': reasons,
            'is_safe': risk_score < 70
        }

    def _level_to_score(self, level: str) -> int:
        scores = {'low': 10, 'medium': 30, 'high': 60, 'critical': 90}
        return scores.get(level, 0)

    def _score_to_level(self, score: int) -> str:
        if score < 20: return 'low'
        if score < 50: return 'medium'
        if score < 80: return 'high'
        return 'critical'

    def report_fraud(self, entity_type: str, entity_value: str, reason: str, client_id: int):
        """Signale une entité frauduleuse dans le registre partagé."""
        conn = self.db.get_connection()
        try:
            conn.execute("""
                INSERT OR REPLACE INTO global_fraud_registry (entity_type, entity_value, reason, reported_by_client_id)
                VALUES (?, ?, ?, ?)
            """, (entity_type, entity_value, reason, client_id))
            conn.commit()
            logger.info(f"Fraud reported: {entity_type}={entity_value}")
        finally:
            conn.close()
