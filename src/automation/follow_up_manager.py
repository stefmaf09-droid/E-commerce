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
        
    def process_follow_ups(self) -> Dict[str, int]:
        """
        Analyse tous les dossiers soumis et déclenche les relances nécessaires.
        
        Returns:
            Dict avec le compte des actions effectuées.
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
                
        return stats

    def _evaluate_and_trigger(self, claim: Dict[str, Any]) -> str:
        """Détermine le niveau d'escalade pour un dossier spécifique."""
        submitted_at = datetime.fromisoformat(claim['submitted_at'])
        days_since_submission = (datetime.now() - submitted_at).days
        current_level = claim.get('follow_up_level', 0)
        
        # Logique d'escalade J+7, J+14, J+21
        if days_since_submission >= 21 and current_level < 3:
            # Niveau 3: Mise en Demeure
            self._trigger_formal_notice(claim)
            return "formal_notices"
        elif days_since_submission >= 14 and current_level < 2:
            # Niveau 2: Dernier avertissement (Warning)
            self._trigger_warning(claim)
            return "warnings"
        elif days_since_submission >= 7 and current_level < 1:
            # Niveau 1: Demande de statut (Status Request)
            self._trigger_status_request(claim)
            return "status_requests"
            
        return None

    def _trigger_status_request(self, claim: Dict[str, Any]):
        """Étape 1: Relance de courtoisie / Demande de statut."""
        logger.info(f"Relance J+7 pour {claim['claim_reference']} ({claim['carrier']})")
        
        # Envoyer email de demande de statut
        from src.email_service.escalation_email_handler import EscalationEmailHandler
        from src.database.escalation_logger import EscalationLogger
        
        email_handler = EscalationEmailHandler()
        escalation_logger = EscalationLogger()
        
        # Déterminer la langue
        country = claim.get('country', 'FR')
        lang = 'FR' if country == 'FR' else 'EN'
        
        # Envoyer l'email
        success = email_handler.send_status_request_email(claim, lang=lang)
        
        # Logger l'action
        escalation_logger.log_email_sent(
            claim_id=claim['id'],
            escalation_level=1,
            email_sent_to=email_handler.carrier_emails.get(claim['carrier'], 'unknown'),
            email_status='sent' if success else 'failed',
            details={'type': 'status_request', 'lang': lang}
        )
        
        # Mettre à jour la base de données
        self.db.update_claim(claim['id'], 
                           follow_up_level=1, 
                           last_follow_up_at=datetime.now())

    def _trigger_warning(self, claim: Dict[str, Any]):
        """Étape 2: Rappel des obligations contractuelles."""
        logger.info(f"Avertissement J+14 pour {claim['claim_reference']} ({claim['carrier']})")
        
        # Envoyer email d'avertissement
        from src.email_service.escalation_email_handler import EscalationEmailHandler
        from src.database.escalation_logger import EscalationLogger
        
        email_handler = EscalationEmailHandler()
        escalation_logger = EscalationLogger()
        
        # Déterminer la langue
        country = claim.get('country', 'FR')
        lang = 'FR' if country == 'FR' else 'EN'
        
        # Envoyer l'email
        success = email_handler.send_warning_email(claim, lang=lang)
        
        # Logger l'action
        escalation_logger.log_email_sent(
            claim_id=claim['id'],
            escalation_level=2,
            email_sent_to=email_handler.carrier_emails.get(claim['carrier'], 'unknown'),
            email_status='sent' if success else 'failed',
            details={'type': 'warning', 'lang': lang}
        )
        
        # Mettre à jour la base de données
        self.db.update_claim(claim['id'], 
                           follow_up_level=2, 
                           last_follow_up_at=datetime.now())

    def _trigger_formal_notice(self, claim: Dict[str, Any]):
        """Étape 3: Génération de la Mise en Demeure."""
        logger.info(f"MISE EN DEMEURE J+21 pour {claim['claim_reference']} ({claim['carrier']})")
        
        # Détermination de la langue basée sur le pays
        country = claim.get('country', 'FR')
        lang = 'FR' if country == 'FR' else 'EN'
        
        # 1. Générer le PDF de mise en demeure
        from src.reports.legal_document_generator import LegalDocumentGenerator
        from src.email_service.escalation_email_handler import EscalationEmailHandler
        from src.database.escalation_logger import EscalationLogger
        
        generator = LegalDocumentGenerator()
        email_handler = EscalationEmailHandler()
        escalation_logger = EscalationLogger()
        
        # Générer le PDF
        pdf_path = generator.generate_formal_notice(claim, lang=lang)
        
        # Logger la génération du PDF
        escalation_logger.log_pdf_generation(
            claim_id=claim['id'],
            escalation_level=3,
            pdf_path=pdf_path,
            details={'lang': lang, 'carrier': claim['carrier']}
        )
        
        # 2. Envoyer l'email avec le PDF attaché
        email_success = email_handler.send_formal_notice_email(
            claim=claim,
            pdf_path=pdf_path,
            lang=lang
        )
        
        # Logger l'envoi de l'email
        escalation_logger.log_email_sent(
            claim_id=claim['id'],
            escalation_level=3,
            email_sent_to=email_handler.carrier_emails.get(claim['carrier'], 'unknown'),
            email_status='sent' if email_success else 'failed',
            pdf_path=pdf_path,
            details={'type': 'formal_notice', 'lang': lang}
        )
        
        # 3. Mettre à jour la base de données
        self.db.update_claim(claim['id'], 
                           follow_up_level=3, 
                           last_follow_up_at=datetime.now(),
                           automation_status='action_required')  # Alerte dashboard
        
        # 4. Retourner les informations
        return {
            'pdf_path': pdf_path,
            'email_sent': email_success,
            'escalation_level': 3
        }

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
