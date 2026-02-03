"""
EscalationLogger - Système de logging dédié aux actions d'escalade juridique.

Ce module gère la traçabilité complète des actions d'escalade :
- Génération de PDFs
- Envoi d'emails
- Réponses des transporteurs
- Statistiques d'escalade
"""

import sqlite3
import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class EscalationLogger:
    """Gestionnaire de logging pour les escalades juridiques."""
    
    def __init__(self, db_path: str = "database/recours_ecommerce.db"):
        """
        Initialize escalation logger.
        
        Args:
            db_path: Chemin vers la base de données SQLite
        """
        self.db_path = db_path
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """Crée la table escalation_log si elle n'existe pas."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS escalation_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    claim_id INTEGER NOT NULL,
                    escalation_level INTEGER NOT NULL,
                    action_type TEXT NOT NULL,
                    pdf_path TEXT,
                    email_sent_to TEXT,
                    email_status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    details TEXT,
                    FOREIGN KEY (claim_id) REFERENCES claims(id)
                )
            """)
            conn.commit()
            logger.info("Table escalation_log vérifiée/créée")
        except Exception as e:
            logger.error(f"Erreur création table escalation_log : {e}")
        finally:
            conn.close()
    
    def log_pdf_generation(
        self,
        claim_id: int,
        escalation_level: int,
        pdf_path: str,
        details: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Log la génération d'un PDF de mise en demeure.
        
        Args:
            claim_id: ID de la réclamation
            escalation_level: Niveau d'escalade (1=status, 2=warning, 3=formal_notice)
            pdf_path: Chemin vers le PDF généré
            details: Informations supplémentaires (optionnel)
            
        Returns:
            ID de l'entrée créée
        """
        return self._log_action(
            claim_id=claim_id,
            escalation_level=escalation_level,
            action_type='pdf_generated',
            pdf_path=pdf_path,
            details=details
        )
    
    def log_email_sent(
        self,
        claim_id: int,
        escalation_level: int,
        email_sent_to: str,
        email_status: str = 'sent',
        pdf_path: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Log l'envoi d'un email d'escalade.
        
        Args:
            claim_id: ID de la réclamation
            escalation_level: Niveau d'escalade
            email_sent_to: Adresse email du destinataire
            email_status: Statut de l'envoi ('sent', 'failed', 'bounced')
            pdf_path: Chemin du PDF attaché (optionnel)
            details: Informations supplémentaires
            
        Returns:
            ID de l'entrée créée
        """
        return self._log_action(
            claim_id=claim_id,
            escalation_level=escalation_level,
            action_type='email_sent',
            email_sent_to=email_sent_to,
            email_status=email_status,
            pdf_path=pdf_path,
            details=details
        )
    
    def log_carrier_response(
        self,
        claim_id: int,
        escalation_level: int,
        details: Dict[str, Any]
    ) -> int:
        """
        Log une réponse du transporteur.
        
        Args:
            claim_id: ID de la réclamation
            escalation_level: Niveau d'escalade actuel
            details: Détails de la réponse
            
        Returns:
            ID de l'entrée créée
        """
        return self._log_action(
            claim_id=claim_id,
            escalation_level=escalation_level,
            action_type='carrier_response',
            details=details
        )
    
    def _log_action(
        self,
        claim_id: int,
        escalation_level: int,
        action_type: str,
        pdf_path: Optional[str] = None,
        email_sent_to: Optional[str] = None,
        email_status: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Log interne d'une action d'escalade.
        
        Args:
            claim_id: ID de la réclamation
            escalation_level: Niveau d'escalade
            action_type: Type d'action ('pdf_generated', 'email_sent', 'carrier_response')
            pdf_path: Chemin du PDF (optionnel)
            email_sent_to: Email du destinataire (optionnel)
            email_status: Statut de l'email (optionnel)
            details: Informations supplémentaires (optionnel)
            
        Returns:
            ID de l'entrée créée
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute("""
                INSERT INTO escalation_log 
                (claim_id, escalation_level, action_type, pdf_path, email_sent_to, email_status, details)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                claim_id,
                escalation_level,
                action_type,
                pdf_path,
                email_sent_to,
                email_status,
                json.dumps(details) if details else None
            ))
            conn.commit()
            log_id = cursor.lastrowid
            logger.info(f"Escalation logged: claim_id={claim_id}, type={action_type}, level={escalation_level}")
            return log_id
        except Exception as e:
            logger.error(f"Erreur logging escalation : {e}")
            return -1
        finally:
            conn.close()
    
    def get_claim_escalation_history(self, claim_id: int) -> List[Dict[str, Any]]:
        """
        Récupère l'historique d'escalade d'une réclamation.
        
        Args:
            claim_id: ID de la réclamation
            
        Returns:
            Liste des actions d'escalade, triées par date (plus récent d'abord)
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM escalation_log
                WHERE claim_id = ?
                ORDER BY created_at DESC
            """, (claim_id,))
            
            rows = cursor.fetchall()
            history = []
            for row in rows:
                entry = dict(row)
                if entry['details']:
                    try:
                        entry['details'] = json.loads(entry['details'])
                    except:
                        pass
                history.append(entry)
            
            return history
        except Exception as e:
            logger.error(f"Erreur récupération historique escalade : {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def get_escalation_statistics(self) -> Dict[str, Any]:
        """
        Récupère les statistiques globales d'escalade.
        
        Returns:
            Dictionnaire avec les statistiques :
            - total_escalations: Nombre total d'escalades
            - by_level: Répartition par niveau
            - by_status: Répartition par statut d'email
            - success_rate: Taux de succès (emails envoyés vs échecs)
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            # Total d'escalades
            cursor = conn.execute("SELECT COUNT(*) as total FROM escalation_log")
            total = cursor.fetchone()['total']
            
            # Par niveau
            cursor = conn.execute("""
                SELECT escalation_level, COUNT(*) as count
                FROM escalation_log
                GROUP BY escalation_level
            """)
            by_level = {row['escalation_level']: row['count'] for row in cursor.fetchall()}
            
            # Par statut d'email
            cursor = conn.execute("""
                SELECT email_status, COUNT(*) as count
                FROM escalation_log
                WHERE action_type = 'email_sent'
                GROUP BY email_status
            """)
            by_status = {row['email_status']: row['count'] for row in cursor.fetchall() if row['email_status']}
            
            # Taux de succès
            sent = by_status.get('sent', 0)
            failed = by_status.get('failed', 0)
            total_emails = sent + failed
            success_rate = (sent / total_emails * 100) if total_emails > 0 else 0
            
            return {
                'total_escalations': total,
                'by_level': by_level,
                'by_email_status': by_status,
                'success_rate': round(success_rate, 2)
            }
        except Exception as e:
            logger.error(f"Erreur récupération statistiques : {e}")
            return {
                'total_escalations': 0,
                'by_level': {},
                'by_email_status': {},
                'success_rate': 0
            }
        finally:
            if conn:
                conn.close()
    
    def get_recent_escalations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Récupère les escalades les plus récentes.
        
        Args:
            limit: Nombre maximum d'entrées à retourner
            
        Returns:
            Liste des escalades récentes avec infos de la réclamation
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT 
                    el.*,
                    c.claim_reference,
                    c.carrier,
                    c.amount_requested
                FROM escalation_log el
                LEFT JOIN claims c ON el.claim_id = c.id
                ORDER BY el.created_at DESC
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            escalations = []
            for row in rows:
                entry = dict(row)
                if entry.get('details'):
                    try:
                        entry['details'] = json.loads(entry['details'])
                    except:
                        pass
                escalations.append(entry)
            
            return escalations
        except Exception as e:
            logger.error(f"Erreur récupération escalades récentes : {e}")
            return []
        finally:
            if conn:
                conn.close()


# Helper functions pour usage direct
def log_escalation_action(
    claim_id: int,
    escalation_level: int,
    action_type: str,
    **kwargs
) -> int:
    """Helper function pour logger une action d'escalade."""
    logger_instance = EscalationLogger()
    return logger_instance._log_action(
        claim_id=claim_id,
        escalation_level=escalation_level,
        action_type=action_type,
        **kwargs
    )
