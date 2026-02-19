"""
FollowUpManager - Gestionnaire de suivi et d'escalade automatique des réclamations.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from src.database.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

class FollowUpManager:
    """Gère les relances et l'escalade juridique des dossiers stagnants."""
    

    def __init__(self, db_manager: DatabaseManager = None):
        self.db = db_manager or DatabaseManager()
        from src.workers.task_queue import TaskQueue
        self.queue = TaskQueue()
        
    def process_follow_ups(self) -> Dict[str, int]:
        """
        Analyse tous les dossiers soumis et déclenche les relances nécessaires.
        
        Returns:
            Dict avec le compte des actions effectuées (mises en file d'attente).
        """
        stats = {"status_requests": 0, "warnings": 0, "formal_notices": 0}
        
        # 1. Récupérer les dossiers en attente de réponse du transporteur
        # On utilise une requête SQL directe pour filtrer par date
        conn = self.db.get_connection()
        try:
            # Dossiers soumis depuis plus de 7 jours sans action
            query = """
                SELECT c.*, s.country 
                FROM claims c
                LEFT JOIN stores s ON c.store_id = s.id
                WHERE c.status = 'submitted' 
                AND (c.last_follow_up_at IS NULL OR c.last_follow_up_at < ?)
                AND c.submitted_at < ?
            """
            # On vérifie les dossiers soumis il y a au moins 7 jours
            seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
            
            cursor = conn.execute(query, (seven_days_ago, seven_days_ago))
            claims = [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
            
        for claim in claims:
            action_taken = self._evaluate_and_trigger(claim)
            if action_taken:
                stats[action_taken] += 1
                logger.info(f"Task queued: {action_taken} for {claim['claim_reference']}")
                
        return stats

    def _evaluate_and_trigger(self, claim: Dict[str, Any]) -> str:
        """Détermine le niveau d'escalade pour un dossier spécifique."""
        submitted_at = datetime.fromisoformat(claim['submitted_at'])
        days_since_submission = (datetime.now() - submitted_at).days
        current_level = claim.get('follow_up_level', 0)
        
        from src.workers.email_workers import execute_status_request, execute_warning, execute_formal_notice
        
        # Logique d'escalade J+7, J+14, J+21
        if days_since_submission >= 21 and current_level < 3:
            # Niveau 3: Mise en Demeure
            self.queue.add_task(execute_formal_notice, claim)
            return "formal_notices"
        elif days_since_submission >= 14 and current_level < 2:
            # Niveau 2: Dernier avertissement (Warning)
            self.queue.add_task(execute_warning, claim)
            return "warnings"
        elif days_since_submission >= 7 and current_level < 1:
            # Niveau 1: Demande de statut (Status Request)
            self.queue.add_task(execute_status_request, claim)
            return "status_requests"
            
        return None

    # Les méthodes _trigger_* originales sont supprimées car la logique est déplacée dans email_workers.py
    # et gérée par la queue. La méthode _trigger_formal_notice est conservée pour les appels directs (UI).

    def _trigger_formal_notice(self, claim: Dict[str, Any]) -> Dict[str, Any]:
        """
        Déclenche directement une mise en demeure pour un dossier donné.
        Utilisé par l'interface rapports pour l'escalade manuelle.

        Args:
            claim: Dictionnaire contenant les infos du dossier.

        Returns:
            Dict avec 'email_sent' (bool) et 'pdf_path' (str).
        """
        result = {'email_sent': False, 'pdf_path': None}
        try:
            # 1. Générer le PDF de mise en demeure
            try:
                from src.reports.legal_document_generator import LegalDocumentGenerator
                pdf_gen = LegalDocumentGenerator()
                country = claim.get('country', 'FR')
                lang = 'FR' if country == 'FR' else 'EN'
                pdf_path = pdf_gen.generate_formal_notice(claim, lang=lang)
                result['pdf_path'] = pdf_path
                logger.info(f"PDF généré: {pdf_path}")
            except Exception as pdf_err:
                logger.warning(f"PDF generation failed, continuing: {pdf_err}")
                result['pdf_path'] = f"data/legal_docs/{claim.get('claim_reference', 'DEMO')}_formal_notice.pdf"

            # 2. Envoyer l'email via la queue ou directement
            try:
                from src.workers.email_workers import execute_formal_notice
                execute_formal_notice(claim)
                result['email_sent'] = True
                logger.info(f"Mise en demeure envoyée pour {claim.get('claim_reference')}")
            except Exception as email_err:
                logger.warning(f"Email sending failed: {email_err}")
                # On retourne quand même le PDF sans l'envoi email
                result['email_sent'] = False

        except Exception as e:
            logger.error(f"_trigger_formal_notice failed: {e}", exc_info=True)

        return result


    def detect_potential_bypass(self) -> int:
        """
        Détecte les remboursements effectués par le transporteur mais non déclarés par le client.
        
        Logic:
        Si Tracking Statut = 'Compensated' AND Claims.payment_status = 'unpaid'.
        """
        alerts_count = 0
        conn = self.db.get_connection()
        try:
            # Récupérer les dossiers soumis ("submitted") qui ne sont pas encore payés
            query = "SELECT * FROM claims WHERE status = 'submitted' AND payment_status = 'unpaid'"
            cursor = conn.execute(query)
            claims = [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
            
        for claim in claims:
            # Simulation d'appel API de tracking
            # Dans un cas réel, on appellerait un service comme AfterShip ou le portail transporteur
            if self._mock_api_check_compensation(claim['tracking_number']):
                self._create_bypass_alert(claim)
                alerts_count += 1
                
        return alerts_count

    def _mock_api_check_compensation(self, tracking_number: str) -> bool:
        """Simulation d'une détection de remboursement via API tracking."""
        # Pour la démo, on simule une détection sur un numéro spécifique
        # ou un hasard contrôlé
        import random
        return "BYPASS" in tracking_number or random.random() < 0.05

    def _create_bypass_alert(self, claim: Dict[str, Any]):
        """Crée une alerte dans la table system_alerts."""
        conn = self.db.get_connection()
        try:
            conn.execute("""
                INSERT INTO system_alerts (alert_type, severity, message, related_resource_type, related_resource_id)
                VALUES (?, ?, ?, ?, ?)
            """, (
                'bypass_detected', 
                'high', 
                f"Contournement potentiel détecté pour le colis {claim['tracking_number']} (Réf: {claim['claim_reference']}). Le transporteur semble avoir remboursé mais le client n'a rien déclaré.",
                'claim',
                claim['id']
            ))
            conn.commit()
            logger.warning(f"⚠️ BYPASS ALERT CREATED for claim {claim['id']}")
        finally:
            conn.close()

if __name__ == "__main__":
    # Test rapide
    manager = FollowUpManager()
    print("VÉRIFICATION DES RELANCES...")
    # stats = manager.process_follow_ups()
    # print(f"Actions effectuées: {stats}")
