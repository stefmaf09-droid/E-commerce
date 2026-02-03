
import logging
import time
from typing import Dict, Any
from src.database.database_manager import get_db_manager

logger = logging.getLogger(__name__)

class HealthMonitor:
    """Surveille la santé des composants critiques du système."""
    
    def __init__(self, db_manager=None):
        self.db = db_manager or get_db_manager()

    def check_database(self) -> Dict[str, Any]:
        """Vérifie la réactivité de la base de données."""
        start = time.time()
        try:
            conn = self.db.get_connection()
            conn.execute("SELECT 1").fetchone()
            conn.close()
            latency = (time.time() - start) * 1000
            return {"status": "HEALTHY", "latency_ms": round(latency, 2)}
        except Exception as e:
            logger.error(f"DB Health Check failed: {e}")
            return {"status": "UNHEALTHY", "error": str(e)}

    def check_stripe_api(self) -> Dict[str, Any]:
        """Vérifie la connexion à Stripe (simulation)."""
        # En prod: stripe.Balance.retrieve()
        return {"status": "HEALTHY", "service": "Stripe API"}

    def get_system_metrics(self) -> str:
        """Exporte des métriques au format Prometheus."""
        conn = self.db.get_connection()
        try:
            total_claims = conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
            pending_claims = conn.execute("SELECT COUNT(*) FROM claims WHERE status = 'pending'").fetchone()[0]
            
            metrics = [
                f'recours_total_claims_count {total_claims}',
                f'recours_pending_claims_count {pending_claims}',
                f'recours_db_health {1 if self.check_database()["status"] == "HEALTHY" else 0}'
            ]
            return "\n".join(metrics)
        finally:
            conn.close()

    def detect_anomalies(self) -> list:
        """Détecte des chutes anormales de taux de succès (Alerte préventive)."""
        # Si un transporteur qui a d'habitude 80% tombe à 20% sur les 10 derniers dossiers
        return [] # Logique complexe de Data Drift pour v2
