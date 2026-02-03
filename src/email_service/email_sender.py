"""
Email sender with templating support.

Sends automated emails for onboarding, OAuth links, and notifications.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class EmailSender:
    """Send automated emails to clients."""
    
    def __init__(
        self, 
        smtp_host: str = "smtp.gmail.com",
        smtp_port: int = 587,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: str = "Agent IA Recouvrement"
    ):
        """
        Initialize email sender.
        
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
        self.smtp_user = smtp_user or from_email
        self.smtp_password = smtp_password
        self.from_email = from_email or smtp_user
        self.from_name = from_name
        
        self.templates_dir = Path(__file__).parent.parent / 'email' / 'templates'
    
    def _load_template(self, template_name: str) -> str:
        """
        Load email template from file.
        
        Args:
            template_name: Template filename (without .html)
            
        Returns:
            Template content
        """
        template_path = self.templates_dir / f"{template_name}.html"
        
        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            logger.warning(f"Template not found: {template_name}")
            return ""
    
    def _replace_variables(self, template: str, variables: Dict[str, str]) -> str:
        """
        Replace template variables with actual values.
        
        Args:
            template: Template string
            variables: Dictionary of variable replacements
            
        Returns:
            Rendered template
        """
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"  # {{variable_name}}
            template = template.replace(placeholder, str(value))
        
        return template
    
    def send_email(
        self, 
        to_email: str, 
        subject: str, 
        html_body: str,
        text_body: Optional[str] = None,
        attachments: Optional[list] = None
    ) -> bool:
        """
        Send an email.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text fallback (optional)
            attachments: List of file paths to attach (optional)
            
        Returns:
            True if successful, False otherwise
        """
        if not all([self.smtp_user, self.smtp_password, self.from_email]):
            logger.error("SMTP credentials not configured")
            return False
        
        try:
            # Import for attachments
            from email.mime.base import MIMEBase
            from email import encoders
            import os
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            # Attach text and HTML versions
            if text_body:
                part1 = MIMEText(text_body, 'plain')
                msg.attach(part1)
            
            part2 = MIMEText(html_body, 'html')
            msg.attach(part2)
            
            # Attach files if provided
            if attachments:
                for file_path in attachments:
                    if not os.path.exists(file_path):
                        logger.warning(f"Attachment not found: {file_path}")
                        continue
                    
                    with open(file_path, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        
                        filename = os.path.basename(file_path)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename="{filename}"'
                        )
                        msg.attach(part)
                        logger.info(f"Attached file: {filename}")
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def send_oauth_link_email(
        self, 
        to_email: str, 
        client_name: str,
        magic_link_url: str,
        platform: str,
        recovery_amount: float,
        expires_in_hours: int = 24
    ) -> bool:
        """
        Send email with OAuth magic link.
        
        Args:
            to_email: Client email
            client_name: Client name
            magic_link_url: Magic link URL
            platform: Platform name
            recovery_amount: Estimated recovery amount
            expires_in_hours: Link expiration time
            
        Returns:
            True if successful
        """
        platform_names = {
            'shopify': 'Shopify',
            'woocommerce': 'WooCommerce',
            'prestashop': 'PrestaShop',
            'magento': 'Magento',
            'bigcommerce': 'BigCommerce',
            'wix': 'Wix'
        }
        
        platform_display = platform_names.get(platform, platform.title())
        
        subject = f"🚀 Activez votre service de récupération automatique ({recovery_amount:,.0f}€)"
        
        # Simple HTML email (in production, use template file)
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #dc2626;">🎉 Prêt à récupérer {recovery_amount:,.0f}€ ?</h1>
                
                <p>Bonjour {client_name},</p>
                
                <p>Votre analyse est terminée ! Nous avons détecté <strong>{recovery_amount:,.0f}€</strong> récupérables sur vos commandes {platform_display}.</p>
                
                <div style="background: #f3f4f6; padding: 20px; border-radius: 10px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">✨ Activez le service en 1 clic</h3>
                    <p>Cliquez sur le bouton ci-dessous pour connecter votre boutique {platform_display} de manière sécurisée :</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{magic_link_url}" 
                           style="display: inline-block; background: #dc2626; color: white; padding: 15px 40px; 
                                  text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px;">
                            🔗 Connecter {platform_display}
                        </a>
                    </div>
                    
                    <p style="font-size: 0.9em; color: #666;">
                        ⏰ Ce lien expire dans {expires_in_hours} heures pour votre sécurité.
                    </p>
                </div>
                
                <h3>🔐 Sécurité et Transparence</h3>
                <ul>
                    <li><strong>Accès en lecture seule</strong> : Nous ne pouvons que consulter vos commandes</li>
                    <li><strong>Aucun risque</strong> : Vous ne payez que sur les résultats (Success Fee 20%)</li>
                    <li><strong>Révocable à tout moment</strong> : Désactivez l'accès quand vous voulez</li>
                </ul>
                
                <h3>💰 Ce qui se passe ensuite</h3>
                <ol>
                    <li>Connexion sécurisée à {platform_display} (en lecture seule)</li>
                    <li>L'IA analyse automatiquement vos litiges</li>
                    <li>Récupération automatique de votre argent</li>
                    <li>You recevez 80% (nous gardons 20% de Success Fee)</li>
                </ol>
                
                <p style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                    Des questions ? Répondez simplement à cet email.
                </p>
                
                <p>
                    Cordialement,<br>
                    <strong>L'équipe Agent IA Recouvrement</strong>
                </p>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        Prêt à récupérer {recovery_amount:,.0f}€ ?
        
        Bonjour {client_name},
        
        Votre analyse est terminée ! Nous avons détecté {recovery_amount:,.0f}€ récupérables sur vos commandes {platform_display}.
        
        Activez le service en 1 clic :
        {magic_link_url}
        
        ⏰ Ce lien expire dans {expires_in_hours} heures.
        
        Cordialement,
        L'équipe Agent IA Recouvrement
        """
        
        return self.send_email(to_email, subject, html_body, text_body)
    
    def send_welcome_email(self, to_email: str, client_name: str, dashboard_url: str) -> bool:
        """
        Send welcome email after successful OAuth.
        
        Args:
            to_email: Client email
            client_name: Client name
            dashboard_url: URL to client dashboard
            
        Returns:
            True if successful
        """
        subject = "✅ Votre service de récupération est activé !"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #10b981;">✅ C'est activé !</h1>
                
                <p>Bonjour {client_name},</p>
                
                <p>Votre boutique est maintenant connectée. Notre IA va commencer à analyser vos commandes et récupérer votre argent automatiquement.</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{dashboard_url}" 
                       style="display: inline-block; background: #10b981; color: white; padding: 15px 40px; 
                              text-decoration: none; border-radius: 8px; font-weight: bold;">
                        📊 Voir mon tableau de bord
                    </a>
                </div>
                
                <h3>📊 Suivi en Temps Réel</h3>
                <p>Consultez votre dashboard pour voir :</p>
                <ul>
                    <li>Litiges détectés en temps réel</li>
                    <li>Montants en cours de récupération</li>
                    <li>Historique des remboursements</li>
                </ul>
                
                <p style="margin-top: 30px;">
                    Cordialement,<br>
                    <strong>L'équipe Agent IA Recouvrement</strong>
                </p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, html_body)
    
    def send_disputes_detected_email(
        self,
        to_email: str,
        client_name: str,
        disputes_count: int,
        total_amount: float,
        disputes_summary: list
    ) -> bool:
        """
        Send email notification about new disputes detected.
        
        Args:
            to_email: Client email
            client_name: Client name
            disputes_count: Number of disputes
            total_amount: Total recoverable amount
            disputes_summary: List of dispute dictionaries
            
        Returns:
            True if successful
        """
        from src.email_service.email_templates import template_disputes_detected
        
        subject = f"🚨 {disputes_count} nouveau{'x' if disputes_count > 1 else ''} litige{'s' if disputes_count > 1 else ''} détecté{'s' if disputes_count > 1 else ''} - {total_amount:.0f}€ récupérables"
        
        html_body = template_disputes_detected(
            client_name=client_name,
            disputes_count=disputes_count,
            total_amount=total_amount,
            disputes_summary=disputes_summary
        )
        
        return self.send_email(to_email, subject, html_body)
    
    def send_claim_submitted_email(
        self,
        to_email: str,
        client_name: str,
        claim_reference: str,
        carrier: str,
        amount_requested: float,
        order_id: str,
        submission_method: str
    ) -> bool:
        """
        Send email notification about claim submitted.
        
        Args:
            to_email: Client email
            client_name: Client name
            claim_reference: Claim reference
            carrier: Carrier name
            amount_requested: Amount requested
            order_id: Order ID
            submission_method: Submission method (api/portal)
            
        Returns:
            True if successful
        """
        from src.email_service.email_templates import template_claim_submitted
        
        subject = f"✅ Réclamation {claim_reference} soumise - {amount_requested:.0f}€"
        
        html_body = template_claim_submitted(
            client_name=client_name,
            claim_reference=claim_reference,
            carrier=carrier,
            amount_requested=amount_requested,
            order_id=order_id,
            submission_method=submission_method
        )
        
        return self.send_email(to_email, subject, html_body)
    
    def send_claim_accepted_email(
        self,
        to_email: str,
        client_name: str,
        claim_reference: str,
        carrier: str,
        accepted_amount: float,
        client_share: float,
        platform_fee: float
    ) -> bool:
        """
        Send email notification about claim accepted.
        
        Args:
            to_email: Client email
            client_name: Client name
            claim_reference: Claim reference
            carrier: Carrier name
            accepted_amount: Accepted amount
            client_share: Client share (80%)
            platform_fee: Platform fee (20%)
            
        Returns:
            True if successful
        """
        from src.email_service.email_templates import template_claim_accepted
        
        subject = f"🎉 Réclamation acceptée - Vous recevez {client_share:.0f}€ !"
        
        html_body = template_claim_accepted(
            client_name=client_name,
            claim_reference=claim_reference,
            carrier=carrier,
            accepted_amount=accepted_amount,
            client_share=client_share,
            platform_fee=platform_fee
        )
        
        return self.send_email(to_email, subject, html_body)
    
    def send_claim_rejected_email(
        self,
        to_email: str,
        client_name: str,
        claim_reference: str,
        carrier: str,
        rejection_reason: str
    ) -> bool:
        """
        Send email notification about claim rejected.
        
        Args:
            to_email: Client email
            client_name: Client name
            claim_reference: Claim reference
            carrier: Carrier name
            rejection_reason: Reason for rejection
            
        Returns:
            True if successful
        """
        from src.email_service.email_templates import template_claim_rejected
        
        subject = f"⚠️ Réclamation {claim_reference} refusée"
        
        html_body = template_claim_rejected(
            client_name=client_name,
            claim_reference=claim_reference,
            carrier=carrier,
            rejection_reason=rejection_reason
        )
        
        return self.send_email(to_email, subject, html_body)


# Helper functions for convenient access
def send_disputes_detected_email(client_email: str, disputes_count: int,
                                 total_amount: float, disputes_summary: list) -> bool:
    """Helper function to send disputes detected email."""
    import os
    sender = EmailSender(
        smtp_user=os.getenv('GMAIL_SENDER'),
        smtp_password=os.getenv('GMAIL_APP_PASSWORD'),
        from_email=os.getenv('GMAIL_SENDER')
    )
    return sender.send_disputes_detected_email(
        to_email=client_email,
        client_name=client_email.split('@')[0].title(),
        disputes_count=disputes_count,
        total_amount=total_amount,
        disputes_summary=disputes_summary
    )


def send_claim_submitted_email(client_email: str, claim_reference: str,
                               carrier: str, amount_requested: float,
                               order_id: str, submission_method: str) -> bool:
    """Helper function to send claim submitted email."""
    import os
    sender = EmailSender(
        smtp_user=os.getenv('GMAIL_SENDER'),
        smtp_password=os.getenv('GMAIL_APP_PASSWORD'),
        from_email=os.getenv('GMAIL_SENDER')
    )
    return sender.send_claim_submitted_email(
        to_email=client_email,
        client_name=client_email.split('@')[0].title(),
        claim_reference=claim_reference,
        carrier=carrier,
        amount_requested=amount_requested,
        order_id=order_id,
        submission_method=submission_method
    )


def send_claim_accepted_email(client_email: str, claim_reference: str,
                              carrier: str, accepted_amount: float,
                              client_share: float, platform_fee: float) -> bool:
    """Helper function to send claim accepted email."""
    import os
    sender = EmailSender(
        smtp_user=os.getenv('GMAIL_SENDER'),
        smtp_password=os.getenv('GMAIL_APP_PASSWORD'),
        from_email=os.getenv('GMAIL_SENDER')
    )
    return sender.send_claim_accepted_email(
        to_email=client_email,
        client_name=client_email.split('@')[0].title(),
        claim_reference=claim_reference,
        carrier=carrier,
        accepted_amount=accepted_amount,
        client_share=client_share,
        platform_fee=platform_fee
    )


def send_claim_rejected_email(client_email: str, claim_reference: str,
                              carrier: str, rejection_reason: str) -> bool:
    """Helper function to send claim rejected email."""
    import os
    sender = EmailSender(
        smtp_user=os.getenv('GMAIL_SENDER'),
        smtp_password=os.getenv('GMAIL_APP_PASSWORD'),
        from_email=os.getenv('GMAIL_SENDER')
    )
    return sender.send_claim_rejected_email(
        to_email=client_email,
        client_name=client_email.split('@')[0].title(),
        claim_reference=claim_reference,
        carrier=carrier,
        rejection_reason=rejection_reason
    )
