"""
EscalationEmailHandler - Gestion des emails d'escalade avec pièces jointes PDF.

Ce module gère l'envoi d'emails d'escalade juridique avec les mises en demeure PDF attachées.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import smtplib

from src.utils.i18n import get_i18n_text, format_currency

logger = logging.getLogger(__name__)


class EscalationEmailHandler:
    """Gestionnaire des emails d'escalade juridique."""
    
    def __init__(
        self,
        smtp_host: str = "smtp.gmail.com",
        smtp_port: int = 587,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: str = "Recours E-commerce - Service Juridique"
    ):
        """
        Initialize escalation email handler.
        
        Args:
            smtp_host: SMTP server host
            smtp_port: SMTP server port
            smtp_user: SMTP username
            smtp_password: SMTP password
            from_email: Sender email address
            from_name: Sender display name
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user or os.getenv('GMAIL_SENDER')
        self.smtp_password = smtp_password or os.getenv('GMAIL_APP_PASSWORD')
        self.from_email = from_email or self.smtp_user
        self.from_name = from_name
        
        # Carrier email mapping (à déplacer en BDD en production)
        self.carrier_emails = {
            'Colissimo': 'litiges.colissimo@laposte.fr',
            'Chronopost': 'reclamations@chronopost.fr',
            'DHL': 'customer.service@dhl.com',
            'UPS': 'claims@ups.com',
            'FedEx': 'claims@fedex.com',
            'DPD': 'service.client@dpd.fr',
            'GLS': 'service.reclamation@gls-france.com',
            'Mondial Relay': 'serviceclient@mondialrelay.fr',
        }
    
    def send_formal_notice_email(
        self,
        claim: Dict[str, Any],
        pdf_path: str,
        lang: str = 'FR'
    ) -> bool:
        """
        Envoie une mise en demeure par email avec PDF attaché.
        
        Args:
            claim: Données de la réclamation
            pdf_path: Chemin vers le PDF de mise en demeure
            lang: Langue de l'email
            
        Returns:
            True si envoi réussi, False sinon
        """
        carrier = claim.get('carrier', 'Transporteur')
        carrier_email = self.carrier_emails.get(carrier, 'unknown@example.com')
        
        # En production, récupérer l'email depuis la BDD ou config
        if carrier_email == 'unknown@example.com':
            logger.warning(f"Email du transporteur {carrier} non configuré")
            # Pour le test, on utilise l'email de l'expéditeur
            carrier_email = self.from_email or 'test@example.com'
        
        subject = self._create_subject('formal_notice', claim, lang)
        html_body = self._create_email_template('formal_notice', claim, lang)
        
        return self._send_email_with_attachment(
            to_email=carrier_email,
            subject=subject,
            html_body=html_body,
            attachment_path=pdf_path,
            claim_ref=claim.get('claim_reference', 'N/A')
        )
    
    def send_status_request_email(
        self,
        claim: Dict[str, Any],
        lang: str = 'FR'
    ) -> bool:
        """
        Envoie une demande de statut (J+7) par email.
        
        Args:
            claim: Données de la réclamation
            lang: Langue de l'email
            
        Returns:
            True si envoi réussi, False sinon
        """
        carrier = claim.get('carrier', 'Transporteur')
        carrier_email = self.carrier_emails.get(carrier, self.from_email or 'test@example.com')
        
        subject = self._create_subject('status_request', claim, lang)
        html_body = self._create_email_template('status_request', claim, lang)
        
        return self._send_email_with_attachment(
            to_email=carrier_email,
            subject=subject,
            html_body=html_body,
            claim_ref=claim.get('claim_reference', 'N/A')
        )
    
    def send_warning_email(
        self,
        claim: Dict[str, Any],
        lang: str = 'FR'
    ) -> bool:
        """
        Envoie un avertissement (J+14) par email.
        
        Args:
            claim: Données de la réclamation
            lang: Langue de l'email
            
        Returns:
            True si envoi réussi, False sinon
        """
        carrier = claim.get('carrier', 'Transporteur')
        carrier_email = self.carrier_emails.get(carrier, self.from_email or 'test@example.com')
        
        subject = self._create_subject('warning', claim, lang)
        html_body = self._create_email_template('warning', claim, lang)
        
        return self._send_email_with_attachment(
            to_email=carrier_email,
            subject=subject,
            html_body=html_body,
            claim_ref=claim.get('claim_reference', 'N/A')
        )
    
    def _create_subject(
        self,
        email_type: str,
        claim: Dict[str, Any],
        lang: str
    ) -> str:
        """Crée le sujet de l'email selon le type."""
        claim_ref = claim.get('claim_reference', 'N/A')
        
        subjects = {
            'formal_notice': {
                'FR': f"⚖️ MISE EN DEMEURE - Réclamation {claim_ref}",
                'EN': f"⚖️ FORMAL NOTICE - Claim {claim_ref}",
                'DE': f"⚖️ FÖRMLICHE MAHNUNG - Reklamation {claim_ref}",
                'IT': f"⚖️ DIFFIDA FORMALE - Reclamo {claim_ref}",
                'ES': f"⚖️ REQUERIMIENTO FORMAL - Reclamación {claim_ref}"
            },
            'status_request': {
                'FR': f"Demande de mise à jour - Réclamation {claim_ref}",
                'EN': f"Status Update Request - Claim {claim_ref}",
                'DE': f"Statusaktualisierung - Reklamation {claim_ref}",
                'IT': f"Richiesta aggiornamento - Reclamo {claim_ref}",
                'ES': f"Solicitud de actualización - Reclamación {claim_ref}"
            },
            'warning': {
                'FR': f"⚠️ DERNIER RAPPEL - Réclamation {claim_ref}",
                'EN': f"⚠️ FINAL REMINDER - Claim {claim_ref}",
                'DE': f"⚠️ LETZTE MAHNUNG - Reklamation {claim_ref}",
                'IT': f"⚠️ ULTIMO PROMEMORIA - Reclamo {claim_ref}",
                'ES': f"⚠️ RECORDATORIO FINAL - Reclamación {claim_ref}"
            }
        }
        
        return subjects.get(email_type, {}).get(lang, subjects[email_type]['FR'])
    
    def _create_email_template(
        self,
        email_type: str,
        claim: Dict[str, Any],
        lang: str
    ) -> str:
        """Crée le template HTML de l'email selon le type."""
        claim_ref = claim.get('claim_reference', 'N/A')
        carrier = claim.get('carrier', 'Transporteur')
        tracking = claim.get('tracking_number', 'N/A')
        amount = claim.get('amount_requested', 0)
        currency = claim.get('currency', 'EUR')
        
        if email_type == 'formal_notice':
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
            </head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: #dc2626; color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center;">
                        <h1 style="margin: 0; font-size: 24px;">⚖️ MISE EN DEMEURE OFFICIELLE</h1>
                    </div>
                    
                    <div style="background: #f3f4f6; padding: 20px; border: 2px solid #dc2626;">
                        <p><strong>Madame, Monsieur,</strong></p>
                        
                        <p>Nous vous adressons la présente mise en demeure concernant le dossier suivant :</p>
                        
                        <div style="background: white; padding: 15px; margin: 20px 0; border-left: 4px solid #dc2626;">
                            <p style="margin: 5px 0;"><strong>Référence réclamation :</strong> {claim_ref}</p>
                            <p style="margin: 5px 0;"><strong>Numéro de suivi :</strong> {tracking}</p>
                            <p style="margin: 5px 0;"><strong>Montant réclamé :</strong> {format_currency(amount, currency)}</p>
                        </div>
                        
                        <p>Malgré nos précédentes relances, nous n'avons reçu aucune réponse de votre part concernant cette réclamation.</p>
                        
                        <p><strong>En conséquence, nous vous mettons formellement en demeure de procéder au remboursement du montant susmentionné dans un délai de 15 jours à compter de la réception de ce courrier.</strong></p>
                        
                        <p>À défaut de régularisation dans ce délai, nous nous réserverons le droit d'engager toute action judiciaire appropriée, sans autre préavis.</p>
                        
                        <p style="margin-top: 30px;">Veuillez trouver ci-joint le document officiel de mise en demeure.</p>
                        
                        <p style="margin-top: 30px;">
                            Cordialement,<br>
                            <strong>Service Juridique - Recours E-commerce</strong><br>
                            Pour le compte de notre mandant
                        </p>
                    </div>
                    
                    <div style="background: #fef3c7; padding: 15px; margin-top: 20px; border-radius: 4px;">
                        <p style="margin: 0; font-size: 12px; color: #78350f;">
                            📎 <strong>Document joint :</strong> Mise en demeure officielle au format PDF<br>
                            ⚖️ Ce document fait foi juridiquement et engage notre responsabilité légale
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
        
        elif email_type == 'status_request':
            return f"""
            <!DOCTYPE html>
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #3b82f6;">Demande de mise à jour - Réclamation {claim_ref}</h2>
                    
                    <p>Madame, Monsieur,</p>
                    
                    <p>Nous avons soumis une réclamation concernant le colis <strong>{tracking}</strong> pour un montant de <strong>{format_currency(amount, currency)}</strong>.</p>
                    
                    <p>Nous vous serions reconnaissants de bien vouloir nous informer de l'état d'avancement de ce dossier.</p>
                    
                    <p>Référence : <strong>{claim_ref}</strong></p>
                    
                    <p>Dans l'attente de votre retour,<br>Cordialement</p>
                </div>
            </body>
            </html>
            """
        
        elif email_type == 'warning':
            return f"""
            <!DOCTYPE html>
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: #f59e0b; color: white; padding: 15px; border-radius: 8px;">
                        <h2 style="margin: 0;">⚠️ DERNIER RAPPEL</h2>
                    </div>
                    
                    <p>Madame, Monsieur,</p>
                    
                    <p>Nous n'avons toujours pas reçu de réponse concernant notre réclamation <strong>{claim_ref}</strong> relative au colis <strong>{tracking}</strong>.</p>
                    
                    <p style="background: #fef3c7; padding: 15px; border-left: 4px solid #f59e0b;">
                        <strong>⚠️ Ceci constitue notre dernier rappel amiable.</strong><br>
                        En l'absence de réponse sous 7 jours, nous procéderons à l'envoi d'une mise en demeure formelle.
                    </p>
                    
                    <p>Montant réclamé : <strong>{format_currency(amount, currency)}</strong></p>
                    
                    <p>Nous vous invitons à régulariser cette situation dans les plus brefs délais afin d'éviter toute procédure juridique.</p>
                    
                    <p>Cordialement,<br><strong>Service Réclamations - Recours E-commerce</strong></p>
                </div>
            </body>
            </html>
            """
        
        return ""
    
    def _send_email_with_attachment(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        attachment_path: Optional[str] = None,
        claim_ref: str = 'N/A'
    ) -> bool:
        """
        Envoie un email avec pièce jointe optionnelle.
        
        Args:
            to_email: Email du destinataire
            subject: Sujet de l'email
            html_body: Corps HTML de l'email
            attachment_path: Chemin vers le fichier à attacher (optionnel)
            claim_ref: Référence de la réclamation (pour logging)
            
        Returns:
            True si envoi réussi, False sinon
        """
        if not all([self.smtp_user, self.smtp_password, self.from_email]):
            logger.error("SMTP credentials not configured")
            return False
        
        # Vérifier que le fichier existe si un attachment_path est fourni
        if attachment_path and not os.path.exists(attachment_path):
            logger.error(f"Fichier PDF non trouvé : {attachment_path}")
            return False
        
        try:
            # Créer le message
            msg = MIMEMultipart()
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            # Attacher le corps HTML
            msg.attach(MIMEText(html_body, 'html'))
            
            # Attacher le PDF si fourni
            if attachment_path:
                with open(attachment_path, 'rb') as f:
                    part = MIMEBase('application', 'pdf')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    
                    filename = os.path.basename(attachment_path)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename="{filename}"'
                    )
                    msg.attach(part)
                    logger.info(f"PDF attaché : {filename}")
            
            # Envoyer l'email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email d'escalade envoyé à {to_email} pour {claim_ref}")
            return True
            
        except FileNotFoundError as e:
            logger.error(f"Fichier PDF non trouvé : {attachment_path}")
            return False
        except Exception as e:
            logger.error(f"Échec d'envoi email pour {claim_ref} : {e}")
            return False


# Helper function pour usage direct
def send_formal_notice(claim: Dict[str, Any], pdf_path: str, lang: str = 'FR') -> bool:
    """Helper function pour envoyer une mise en demeure."""
    handler = EscalationEmailHandler()
    return handler.send_formal_notice_email(claim, pdf_path, lang)
