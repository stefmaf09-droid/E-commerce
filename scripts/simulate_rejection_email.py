
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

from src.reports.legal_document_generator import LegalDocumentGenerator

def simulate_rejection_email():
    print("🚀 Simulation d'envoi d'email de REJET transporteur...")
    
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

        claim_ref = 'CLM-20260207-SIMUL'
        
        # 1. Contenu de l'email simulant un rejet
        html_body = f"""
        <html>
        <body>
            <h2>Notification de Rejet de Réclamation</h2>
            <p>Bonjour,</p>
            <p>Nous avons étudié votre réclamation <strong>{claim_ref}</strong>.</p>
            <p>Après vérification, nous constatons que <strong>le poids réel du colis lors du transit correspond au poids déclaré</strong> sur le bordereau.</p>
            <p>En conséquence, votre demande est rejetée.</p>
            <p>Cordialement,<br>Service Client Transporteur</p>
        </body>
        </html>
        """
        
        msg = MIMEMultipart()
        msg['From'] = username
        msg['To'] = username
        msg['Subject'] = f"REJET de votre réclamation {claim_ref} - Poids conforme"
        msg.attach(MIMEText(html_body, 'html'))
        
        # 2. Ajout d'une pièce jointe (Lettre de rejet simulée)
        # On va créer un PDF qui contient le mot clé "poids conforme"
        # Since we have reportlab installed now, we can use it to make a PDF with that text
        from reportlab.pdfgen import canvas
        
        temp_dir = os.path.join(root_dir, 'data', 'temp_test')
        os.makedirs(temp_dir, exist_ok=True)
        pdf_path = os.path.join(temp_dir, f"lettre_rejet_{claim_ref}.pdf")
        
        c = canvas.Canvas(pdf_path)
        c.drawString(100, 750, "LETTRE DE REJET OFFICIELLE")
        c.drawString(100, 700, f"Référence : {claim_ref}")
        c.drawString(100, 650, "Motif du rejet :")
        c.drawString(100, 630, "Après pesée contradictoire, le poids est conforme.")
        c.drawString(100, 610, "Aucune spoliation n'est donc reconnue.")
        c.save()
        
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
        
        print(f"📧 Envoi de l'email de rejet à {username}...")
        
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(username, password)
            server.send_message(msg)
            
        print("✅ Email de rejet envoyé avec succès !")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi : {e}")

if __name__ == "__main__":
    simulate_rejection_email()
