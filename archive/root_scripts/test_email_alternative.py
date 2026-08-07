"""
Alternative pour tester les emails SANS Gmail App Password.
Utilise un serveur SMTP de test (Mailtrap ou service similaire).

Option 1: Mailtrap.io (Gratuit)
-------------------------------
1. Créer compte sur https://mailtrap.io
2. Copier credentials SMTP
3. Configurer ci-dessous

Option 2: Gmail avec Paramètres moins sécurisés (NON RECOMMANDÉ)
-----------------------------------------------------------------
Gmail a désactivé cette option depuis mai 2022.
Vous DEVEZ utiliser un mot de passe d'application.
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, 'src')

from email_service.email_sender import EmailSender

print("=" * 60)
print("🧪 TEST EMAIL - Configuration Alternative")
print("=" * 60)
print()

# OPTION: Utiliser Mailtrap (pour développement/test)
# Créez un compte gratuit sur https://mailtrap.io
# Copiez les credentials de votre inbox

USE_MAILTRAP = True  # Changez à False pour utiliser Gmail

if USE_MAILTRAP:
    print("📬 Utilisation de Mailtrap (serveur de test)")
    print("👉 Créez un compte gratuit: https://mailtrap.io")
    print()
    
    # Remplacez par vos credentials Mailtrap
    smtp_host = "sandbox.smtp.mailtrap.io"  # ou smtp.mailtrap.io
    smtp_port = 2525
    smtp_user = input("Mailtrap Username (ex: 1a2b3c4d5e6f7g): ").strip()
    smtp_password = input("Mailtrap Password: ").strip()
    from_email = "test@recours-ecommerce.com"
    
    if not smtp_user or not smtp_password:
        print("❌ Credentials Mailtrap manquants")
        sys.exit(1)
    
    # Test email
    sender = EmailSender(
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_user=smtp_user,
        smtp_password=smtp_password,
        from_email=from_email
    )
    
    result = sender.send_email(
        to_email="client@example.com",  # N'importe quel email (Mailtrap capture tout)
        subject="🧪 Test Mailtrap - Recours Ecommerce",
        html_body="""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h1 style="color: #667eea;">✅ Email de Test</h1>
            <p>Si vous voyez cet email dans votre inbox Mailtrap, la configuration fonctionne !</p>
            <p><strong>Prochaine étape:</strong> Configurez Gmail avec un mot de passe d'application pour la production.</p>
        </body>
        </html>
        """
    )
    
    if result:
        print()
        print("✅ Email envoyé avec succès !")
        print("📬 Vérifiez votre inbox Mailtrap: https://mailtrap.io/inboxes")
    else:
        print("❌ Échec de l'envoi")

else:
    print("📧 Pour utiliser Gmail:")
    print("1. Activez la 2FA: https://myaccount.google.com/signinoptions/two-step-verification")
    print("2. Créez un mot de passe d'app: https://myaccount.google.com/apppasswords")
    print()
