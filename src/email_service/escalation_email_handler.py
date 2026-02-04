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
from src.database.email_template_manager import EmailTemplateManager

logger = logging.getLogger(__name__)


class EscalationEmailHandler:
    """Gestionnaire des emails d'escalade juridique."""
    
    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
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
        # Configuration SMTP générique (priorité aux vars d'env, fallback sur Gmail pour compatibilité)
        self.smtp_host = smtp_host or os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = smtp_port or int(os.getenv('SMTP_PORT', 587))
        self.smtp_user = smtp_user or os.getenv('SMTP_USER') or os.getenv('GMAIL_SENDER')
        self.smtp_password = smtp_password or os.getenv('SMTP_PASSWORD') or os.getenv('GMAIL_APP_PASSWORD')
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
        
        # Sécurité pour les tests : si TEST_MODE est actif, on ne contacte pas les transporteurs
        self.test_mode = os.getenv('TEST_MODE', 'False').lower() == 'true'
        self.test_recipient = os.getenv('TEST_EMAIL_RECIPIENT', self.from_email)

    def _get_safe_recipient(self, carrier: str) -> str:
        """Retourne l'email du destinataire (réel ou test)."""
        if self.test_mode:
            logger.info(f"🧪 TEST MODE: Redirecting email for {carrier} to {self.test_recipient}")
            return self.test_recipient
            
        return self.carrier_emails.get(carrier, self.from_email)

    
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
        carrier_email = self._get_safe_recipient(carrier)
        
        # Fallback si jamais vide
        if not carrier_email:
            carrier_email = self.from_email
        
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
        carrier_email = self._get_safe_recipient(carrier)
        
        # Fallback si jamais vide
        if not carrier_email:
            carrier_email = self.from_email
        
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
        carrier_email = self._get_safe_recipient(carrier)
        
        # Fallback si jamais vide
        if not carrier_email:
            carrier_email = self.from_email
        
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
        """Crée le sujet de l'email via le Template Manager."""
        template_manager = EmailTemplateManager()
        client_id = claim.get('client_id')
        template = template_manager.get_template(email_type, lang, client_id=client_id)
        rendered = template_manager.render_template(template, claim)
        return rendered['subject']
    
    def _create_email_template(
        self,
        email_type: str,
        claim: Dict[str, Any],
        lang: str
    ) -> str:
        """Crée le corps HTML de l'email via le Template Manager."""
        template_manager = EmailTemplateManager()
        client_id = claim.get('client_id')
        template = template_manager.get_template(email_type, lang, client_id=client_id)
        
        # Enrichir les données de la claim avec une localisation si manquante
        if 'location' not in claim:
            claim['location'] = 'Paris' # Valeur par défaut
            
        rendered = template_manager.render_template(template, claim)
        return rendered['body']
    
    def _send_email_with_attachment(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        attachment_path: Optional[str] = None,
        claim_ref: str = 'N/A'
    ) -> bool:
        """
        Envoie un email avec support d'image inline (logo) et pièce jointe PDF.
        Structure MIME: multipart/mixed [ multipart/related [ html, image ], pdf ]
        """
        if not all([self.smtp_user, self.smtp_password, self.from_email]):
            logger.error("SMTP credentials not configured")
            return False
        
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'static', 'refundly_logo.png')
        
        try:
            # 1. Root container (mixed) pour supporter body + attachments
            msg = MIMEMultipart('mixed')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            # 2. Related container pour HTML + Images
            msg_related = MIMEMultipart('related')
            msg.attach(msg_related)
            
            # 2.1 HTML Body
            msg_related.attach(MIMEText(html_body, 'html'))
            
            # 2.2 Logo Inline
            if os.path.exists(logo_path):
                with open(logo_path, 'rb') as f:
                    img_data = f.read()
                    from email.mime.image import MIMEImage
                    img = MIMEImage(img_data)
                    # Define the image ID as referenced in the HTML
                    img.add_header('Content-ID', '<refundly_logo>')
                    img.add_header('Content-Disposition', 'inline', filename='refundly_logo.png')
                    msg_related.attach(img)
            else:
                logger.warning(f"Logo not found at {logo_path}")

            # 3. PDF Attachment (attached to Root Mixed)
            if attachment_path:
                if os.path.exists(attachment_path):
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
                else:
                    logger.error(f"Fichier PDF non trouvé : {attachment_path}")
            
            # Envoyer l'email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email d'escalade envoyé à {to_email} pour {claim_ref}")
            return True
            
        except Exception as e:
            logger.error(f"Échec d'envoi email pour {claim_ref} : {e}")
            return False


# Helper function pour usage direct
def send_formal_notice(claim: Dict[str, Any], pdf_path: str, lang: str = 'FR') -> bool:
    """Helper function pour envoyer une mise en demeure."""
    handler = EscalationEmailHandler()
    return handler.send_formal_notice_email(claim, pdf_path, lang)
