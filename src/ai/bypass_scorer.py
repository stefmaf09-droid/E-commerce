
import logging
from typing import Dict, Any, List
import sqlite3
import os

from src.database.database_manager import get_db_manager

logger = logging.getLogger(__name__)

class BypassScorer:
    """ AI-powered success prediction for disputes. """
    
    def __init__(self):
        self.db = get_db_manager()
        
        # Expert Rules (Baseline Success Probabilities)
        self.base_weights = {
            'dispute_type': {
                'lost': 0.95,
                'late_delivery': 0.85,
                'damaged': 0.40,
                'invalid_pod': 0.70,
                'unknown': 0.50
            },
            'carrier': {
                'Chronopost': 1.0,
                'Colissimo': 1.0,
                'UPS': 0.9,
                'DHL': 0.9,
                'FedEx': 0.8,
                'DPD': 0.7
            }
        }

    def predict_success(self, dispute_data: Dict[str, Any]) -> float:
        """
        Calculate the probability of success for a given dispute.
        
        Formula: Base Type Weight * Carrier Multiplier * Historical Factor
        """
        dispute_type = dispute_data.get('dispute_type', 'unknown')
        carrier = dispute_data.get('carrier', 'Unknown')
        
        # 1. Start with base weight for type
        score = self.base_weights['dispute_type'].get(dispute_type, 0.5)
        
        # 2. Apply carrier multiplier
        carrier_mult = self.base_weights['carrier'].get(carrier, 0.8)
        score *= carrier_mult
        
        # 3. Apply historical factor from database (if enough data)
        history_factor = self._get_historical_factor(carrier, dispute_type)
        score *= history_factor
        
        # Clamp between 0.01 and 0.99
        return max(0.01, min(0.99, score))

    def _get_historical_factor(self, carrier: str, dispute_type: str) -> float:
        """Query DB to see how well we've done in the past with similar disputes."""
        try:
            conn = self.db.get_connection()
            query = """
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'accepted' THEN 1 ELSE 0 END) as accepted
                FROM claims 
                WHERE carrier = ? AND dispute_type = ?
            """
            cursor = conn.execute(query, (carrier, dispute_type))
            row = cursor.fetchone()
            
            if row and row['total'] >= 5: # Need at least 5 samples to influence score
                actual_rate = row['accepted'] / row['total']
                # Weighted average with base score (Bayesian shrinking)
                return 0.5 + (actual_rate * 0.5)
            
            return 1.0 # No change if not enough data
        except Exception as e:
            logger.warning(f"Error calculating historical factor: {e}")
            return 1.0
        finally:
            if 'conn' in locals():
                conn.close()

    def get_strategic_advice(self, dispute_data: Dict[str, Any]) -> str:
        """Returns a short AI advice based on success probability."""
        score = self.predict_success(dispute_data)
        
        if score > 0.8:
            return "🚀 Très haute probabilité de succès. Soumettez immédiatement."
        elif score > 0.5:
            return "⚖️ Probabilité moyenne. Assurez-vous d'avoir une attestation client."
        else:
            return "⚠️ Probabilité faible. Nécessite des preuves photos solides pour Bypass."
