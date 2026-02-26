"""
Email Sender Module - Send emails via Gmail SMTP.

Handles password reset, welcome emails, claim confirmations, etc.
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailSender:
    """Send emails using Gmail SMTP."""
    
    def __init__(self):
        """Initialize email sender with Gmail SMTP configuration."""
        # Configuration depuis variables d'environnement
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 465  # SSL
        self.sender_email = os.getenv('GMAIL_SENDER', 'votre-email@gmail.com')
        self.sender_password = os.getenv('GMAIL_APP_PASSWORD', '')
        self.sender_name = "Refundly.ai"
        
        if not self.sender_password:
            logger.warning("⚠️ GMAIL_APP_PASSWORD non configuré. Les emails ne seront pas envoyés.")
    
    def send_email(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str,
        plain_text: Optional[str] = None
    ) -> bool:
        """
        Send an email via Gmail SMTP.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content of the email
            plain_text: Optional plain text version
            
        Returns:
            True if successful, False otherwise
        """
        if not self.sender_password:
            logger.error("Cannot send email: GMAIL_APP_PASSWORD not configured")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = to_email
            
            # Add plain text version (fallback)
            if plain_text:
                text_part = MIMEText(plain_text, 'plain', 'utf-8')
                msg.attach(text_part)
            
            # Add HTML version
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, to_email, msg.as_string())
            
            logger.info(f"✅ Email sent to {to_email}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send email to {to_email}: {e}")
            return False
    
    def send_welcome_email(self, to_email: str, client_name: str) -> bool:
        """
        Send welcome email after registration.
        
        Args:
            to_email: Client email
            client_name: Client name or email
            
        Returns:
            True if successful
        """
        subject = "🎉 Bienvenue sur Refundly.ai"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                          color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9fafb; padding: 30px; }}
                .button {{ background: #10b981; color: white; padding: 12px 30px; 
                          text-decoration: none; border-radius: 5px; display: inline-block; 
                          margin: 20px 0; }}
                .footer {{ background: #333; color: #fff; padding: 20px; text-align: center; 
                          border-radius: 0 0 10px 10px; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Bienvenue chez Agent IA !</h1>
                </div>
                <div class="content">
                    <p>Bonjour <strong>{client_name}</strong>,</p>
                    
                    <p>Votre compte a été créé avec succès ! Nous sommes ravis de vous accompagner dans la récupération de vos litiges de livraison.</p>
                    
                    <h3>✨ Ce que nous faisons pour vous :</h3>
                    <ul>
                        <li>📊 Détection automatique des litiges</li>
                        <li>🤖 Génération optimisée de réclamations</li>
                        <li>📤 Soumission automatique aux transporteurs</li>
                        <li>💰 Récupération de votre argent (80% pour vous)</li>
                    </ul>
                    
                    <p style="text-align: center;">
                        <a href="http://localhost:8501" class="button">Accéder à mon tableau de bord</a>
                    </p>
                    
                    <p>Si vous avez des questions, n'hésitez pas à nous contacter.</p>
                    
                    <p>À très bientôt,<br>
                    <strong>L'équipe Refundly.ai</strong></p>
                </div>
                <div class="footer">
                    <p>© 2026 Refundly.ai - Tous droits réservés</p>
                    <p>Cet email a été envoyé à {to_email}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_text = f"""
        Bienvenue {client_name} !
        
        Votre compte Refundly.ai a été créé avec succès.
        
        Accédez à votre tableau de bord : http://localhost:8501
        
        L'équipe Refundly.ai
        """
        
        return self.send_email(to_email, subject, html_content, plain_text)
    
    def send_password_reset_email(
        self, 
        to_email: str, 
        reset_token: Optional[str] = None
    ) -> bool:
        """
        Send password reset confirmation email.
        
        Args:
            to_email: Client email
            reset_token: Optional reset token for secure link (future)
            
        Returns:
            True if successful
        """
        subject = "🔑 Réinitialisation de votre mot de passe"
        
        # Pour l'instant, simple confirmation (pas de lien sécurisé)
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #dc2626; color: white; padding: 30px; text-align: center; 
                          border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9fafb; padding: 30px; }}
                .alert {{ background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; 
                         margin: 20px 0; }}
                .footer {{ background: #333; color: #fff; padding: 20px; text-align: center; 
                          border-radius: 0 0 10px 10px; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔑 Réinitialisation de mot de passe</h1>
                </div>
                <div class="content">
                    <p>Bonjour,</p>
                    
                    <p>Votre mot de passe a été <strong>réinitialisé avec succès</strong>.</p>
                    
                    <div class="alert">
                        <strong>⚠️ Sécurité :</strong> Si vous n'êtes pas à l'origine de cette demande, 
                        veuillez nous contacter immédiatement.
                    </div>
                    
                    <p>Vous pouvez maintenant vous connecter avec votre nouveau mot de passe.</p>
                    
                    <p>Pour des raisons de sécurité, nous vous recommandons de choisir un mot de passe :</p>
                    <ul>
                        <li>D'au moins 8 caractères</li>
                        <li>Contenant majuscules et minuscules</li>
                        <li>Avec des chiffres et caractères spéciaux</li>
                    </ul>
                    
                    <p>Cordialement,<br>
                    <strong>L'équipe Refundly.ai</strong></p>
                </div>
                <div class="footer">
                    <p>© 2026 Refundly.ai</p>
                    <p>Email envoyé le {datetime.now().strftime('%d/%m/%Y à %H:%M')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_text = f"""
        Réinitialisation de mot de passe
        
        Votre mot de passe a été réinitialisé avec succès.
        
        Si vous n'êtes pas à l'origine de cette demande, contactez-nous immédiatement.
        
        L'équipe Refundly.ai
        """
        
        return self.send_email(to_email, subject, html_content, plain_text)
    
    def send_claim_confirmation_email(
        self,
        to_email: str,
        claim_reference: str,
        carrier: str,
        amount: float,
        photos_count: int,
        response_days: int
    ) -> bool:
        """
        Send claim submission confirmation email.
        
        Args:
            to_email: Client email
            claim_reference: Claim reference number
            carrier: Carrier name
            amount: Claim amount
            photos_count: Number of photos
            response_days: Expected response time
            
        Returns:
            True if successful
        """
        subject = f"📋 Réclamation soumise - {claim_reference}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                          color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9fafb; padding: 30px; }}
                .info-box {{ background: white; border-left: 4px solid #10b981; 
                            padding: 20px; margin: 20px 0; border-radius: 5px; }}
                .highlight {{ background: #d1fae5; padding: 15px; border-radius: 5px; 
                             text-align: center; margin: 20px 0; }}
                .footer {{ background: #333; color: #fff; padding: 20px; text-align: center; 
                          border-radius: 0 0 10px 10px; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Réclamation soumise avec succès !</h1>
                </div>
                <div class="content">
                    <p>Bonjour,</p>
                    
                    <p>Votre réclamation a été <strong>soumise automatiquement</strong> au transporteur.</p>
                    
                    <div class="info-box">
                        <h3>📋 Détails de votre réclamation</h3>
                        <p><strong>Référence :</strong> {claim_reference}</p>
                        <p><strong>Transporteur :</strong> {carrier}</p>
                        <p><strong>Montant demandé :</strong> {amount:.2f}€</p>
                        <p><strong>Photos jointes :</strong> {photos_count} photo(s)</p>
                        <p><strong>Soumis le :</strong> {datetime.now().strftime('%d/%m/%Y à %H:%M')}</p>
                    </div>
                    
                    <div class="highlight">
                        <h3>⚖️ Délai légal de réponse</h3>
                        <p style="font-size: 24px; margin: 10px 0;"><strong>{response_days} jours maximum</strong></p>
                        <p>Le transporteur doit répondre avant le <strong>{(datetime.now().strftime('%d/%m/%Y'))}</strong></p>
                    </div>
                    
                    <h3>📊 Prochaines étapes</h3>
                    <ol>
                        <li>Le transporteur examine votre dossier</li>
                        <li>Vous recevrez une réponse sous {response_days} jours</li>
                        <li>Si acceptée, vous recevrez 80% du montant récupéré</li>
                    </ol>
                    
                    <p><strong>💡 Astuce :</strong> Vous pouvez suivre l'avancement de votre réclamation dans votre tableau de bord.</p>
                    
                    <p>Cordialement,<br>
                    <strong>L'équipe Refundly.ai</strong></p>
                </div>
                <div class="footer">
                    <p>© 2026 Refundly.ai</p>
                    <p>Référence: {claim_reference}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_text = f"""
        Réclamation soumise avec succès !
        
        Référence : {claim_reference}
        Transporteur : {carrier}
        Montant : {amount:.2f}€
        
        Délai de réponse : {response_days} jours maximum
        
        Vous serez notifié de la décision du transporteur.
        
        L'équipe Refundly.ai
        """
        
        return self.send_email(to_email, subject, html_content, plain_text)


# Convenience functions for easy import
def send_welcome_email(to_email: str, client_name: str) -> bool:
    """Send welcome email."""
    sender = EmailSender()
    return sender.send_welcome_email(to_email, client_name)


def send_password_reset_email(to_email: str) -> bool:
    """Send password reset confirmation."""
    sender = EmailSender()
    return sender.send_password_reset_email(to_email)


def send_claim_confirmation_email(
    to_email: str,
    claim_reference: str,
    carrier: str,
    amount: float,
    photos_count: int,
    response_days: int
) -> bool:
    """Send claim confirmation email."""
    sender = EmailSender()
    return sender.send_claim_confirmation_email(
        to_email, claim_reference, carrier, amount, photos_count, response_days
    )


if __name__ == "__main__":
    # Test email sending
    print("="*70)
    print("EMAIL SENDER - Test")
    print("="*70)
    
    sender = EmailSender()
    
    print(f"\n📧 Configuration:")
    print(f"  SMTP Server: {sender.smtp_server}:{sender.smtp_port}")
    print(f"  Sender: {sender.sender_email}")
    print(f"  Password configured: {'✅ Yes' if sender.sender_password else '❌ No'}")
    
    if not sender.sender_password:
        print("\n⚠️  Pour tester, configurez les variables d'environnement:")
        print("  export GMAIL_SENDER='votre-email@gmail.com'")
        print("  export GMAIL_APP_PASSWORD='votre-mot-de-passe-app'")
        print("\n💡 Créez un mot de passe d'application sur:")
        print("  https://myaccount.google.com/apppasswords")
    else:
        print("\n✅ Configuration OK - Envoi d'un email de test...")
        # Uncomment to test:
        # sender.send_welcome_email("test@example.com", "Test User")
    
    print("\n" + "="*70)
    print("✅ Test Complete")
    print("="*70)
