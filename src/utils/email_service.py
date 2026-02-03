"""
Email service for password reset and notifications.

Supports SMTP email sending for password reset links.
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import secrets
import json
from datetime import datetime, timedelta
from pathlib import Path


class EmailService:
    """Handle email sending for password resets and notifications."""
    
    def __init__(self):
        """Initialize email service with SMTP configuration."""
        # Configuration from environment variables
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', self.smtp_user)
        self.from_name = os.getenv('FROM_NAME', 'Agent IA Recouvrement')
        
        # Token storage
        self.tokens_file = "data/reset_tokens.json"
        Path(self.tokens_file).parent.mkdir(parents=True, exist_ok=True)
        
        if not os.path.exists(self.tokens_file):
            with open(self.tokens_file, 'w') as f:
                json.dump({}, f)
    
    def generate_reset_token(self, email: str) -> str:
        """Generate a secure reset token for an email."""
        token = secrets.token_urlsafe(32)
        
        # Store token with expiration (24 hours)
        with open(self.tokens_file, 'r') as f:
            tokens = json.load(f)
        
        tokens[token] = {
            'email': email,
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(hours=24)).isoformat()
        }
        
        with open(self.tokens_file, 'w') as f:
            json.dump(tokens, f, indent=2)
        
        return token
    
    def validate_reset_token(self, token: str) -> Optional[str]:
        """Validate a reset token and return the email if valid."""
        try:
            with open(self.tokens_file, 'r') as f:
                tokens = json.load(f)
            
            if token not in tokens:
                return None
            
            token_data = tokens[token]
            expires_at = datetime.fromisoformat(token_data['expires_at'])
            
            if datetime.now() > expires_at:
                # Token expired
                del tokens[token]
                with open(self.tokens_file, 'w') as f:
                    json.dump(tokens, f)
                return None
            
            return token_data['email']
        except Exception as e:
            print(f"Error validating token: {e}")
            return None
    
    def invalidate_token(self, token: str):
        """Invalidate a reset token after use."""
        try:
            with open(self.tokens_file, 'r') as f:
                tokens = json.load(f)
            
            if token in tokens:
                del tokens[token]
                with open(self.tokens_file, 'w') as f:
                    json.dump(tokens, f)
        except Exception as e:
            print(f"Error invalidating token: {e}")
    
    def send_password_reset_email(self, to_email: str, reset_url: str) -> bool:
        """Send password reset email."""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = "Réinitialisation de votre mot de passe"
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            # Email body
            text_content = f"""
Bonjour,

Vous avez demandé la réinitialisation de votre mot de passe.

Cliquez sur le lien ci-dessous pour réinitialiser votre mot de passe :
{reset_url}

Ce lien est valide pendant 24 heures.

Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.

Cordialement,
L'équipe Agent IA Recouvrement
            """
            
            html_content = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #dc2626;">🔐 Réinitialisation de mot de passe</h2>
        
        <p>Bonjour,</p>
        
        <p>Vous avez demandé la réinitialisation de votre mot de passe.</p>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_url}" 
               style="background-color: #10b981; color: white; padding: 12px 30px; 
                      text-decoration: none; border-radius: 5px; font-weight: bold;">
                Réinitialiser mon mot de passe
            </a>
        </div>
        
        <p style="color: #666; font-size: 14px;">
            Ce lien est valide pendant 24 heures.
        </p>
        
        <p style="color: #999; font-size: 12px; margin-top: 30px;">
            Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.
        </p>
        
        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        
        <p style="color: #999; font-size: 12px;">
            L'équipe Agent IA Recouvrement
        </p>
    </div>
</body>
</html>
            """
            
            # Attach parts
            part1 = MIMEText(text_content, 'plain')
            part2 = MIMEText(html_content, 'html')
            msg.attach(part1)
            msg.attach(part2)
            
            # Send email
            if not self.smtp_user or not self.smtp_password:
                print("⚠️ SMTP credentials not configured. Email would be sent to:", to_email)
                print("Reset URL:", reset_url)
                return True  # For dev/testing
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            print(f"✅ Password reset email sent to {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False


# Test
if __name__ == "__main__":  # pragma: no cover
    print("="*70)
    print("EMAIL SERVICE - Test")
    print("="*70)
    
    service = EmailService()
    
    # Test token generation
    email = "test@example.com"
    token = service.generate_reset_token(email)
    
    print(f"\n✅ Token generated: {token[:20]}...")
    
    # Test validation
    validated_email = service.validate_reset_token(token)
    print(f"✅ Token validates to: {validated_email}")
    
    # Test email sending (will print URL in dev mode)
    reset_url = f"http://localhost:8503?reset_token={token}"
    service.send_password_reset_email(email, reset_url)
    
    print("\n" + "="*70)
    print("✅ Test Complete")
    print("="*70)
    print("\nℹ️  Pour production, configurez:")
    print("  - SMTP_HOST, SMTP_PORT")
    print("  - SMTP_USER, SMTP_PASSWORD")
    print("  - FROM_EMAIL, FROM_NAME")
