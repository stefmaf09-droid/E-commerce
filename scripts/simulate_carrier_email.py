
import smtplib
import os
import sys
import toml
import unittest.mock
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Path Setup
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Mock Streamlit BEFORE importing src modules
st_mock = unittest.mock.MagicMock()
st_mock.session_state = {}
st_mock.query_params = {}
sys.modules['streamlit'] = st_mock
sys.modules['streamlit.components.v1'] = unittest.mock.MagicMock()

from src.email_service.email_templates import template_claim_accepted
from src.reports.legal_document_generator import LegalDocumentGenerator

def simulate_carrier_email():
    print("🚀 Simulation d'envoi d'email transporteur professionnel...")
    
    # Charger les secrets
    secrets_path = os.path.join(root_dir, '.streamlit', 'secrets.toml')
    try:
        secrets = toml.load(secrets_path)
        email_config = secrets.get('email', {})
        
        username = email_config.get('username')
        password = email_config.get('password')
        
        if not password or password == "VOTRE_MOT_DE_PASSE_ICI":
            print("❌ Erreur: Mot de passe non configuré dans secrets.toml")
            return

        # Configuration des données de simulation
        mock_claim = {
            'claim_reference': 'CLM-20260207-SIMUL',
            'carrier': 'Chronopost',
            'tracking_number': '6A1234567890',
            'amount_requested': 45.0,
            'dispute_type': 'Retard de livraison',
            'company_name': 'Votre Boutique SAS',
            'currency': 'EUR'
        }
        
        # 1. Génération de l'email HTML professionnel
        html_body = template_claim_accepted(
            client_name="Stephen",
            claim_reference=mock_claim['claim_reference'],
            carrier=mock_claim['carrier'],
            accepted_amount=45.0,
            client_share=36.0, # 80%
            platform_fee=9.0   # 20%
        )
        
        msg = MIMEMultipart()
        msg['From'] = username
        msg['To'] = username
        msg['Subject'] = f"Réclamation Acceptée {mock_claim['claim_reference']} - Refundly.ai"
        msg.attach(MIMEText(html_body, 'html'))
        
        # 2. Génération d'un PDF juridique réel
        print("📄 Génération du PDF juridique...")
        pdf_gen = LegalDocumentGenerator()
        temp_dir = os.path.join(root_dir, 'data', 'temp_test')
        os.makedirs(temp_dir, exist_ok=True)
        
        pdf_path = pdf_gen.generate_formal_notice(mock_claim, lang='FR', output_dir=temp_dir)
        filename = os.path.basename(pdf_path)
        
        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()
        
        part = MIMEBase('application', 'pdf')
        part.set_payload(pdf_content)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename= {filename}")
        msg.attach(part)
        
        # Envoi via SMTP Orange
        smtp_server = "smtp.orange.fr"
        smtp_port = 465 # SSL
        
        print(f"📧 Envoi de l'email à {username}...")
        
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(username, password)
            server.send_message(msg)
            
        print("✅ Email envoyé avec succès !")
        print(f"💡 Contenu : Template professionnel + PDF '{filename}'")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi : {e}")

if __name__ == "__main__":
    simulate_carrier_email()
