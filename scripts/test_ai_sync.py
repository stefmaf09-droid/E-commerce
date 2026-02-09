
import os
import sys
import unittest.mock
import sqlite3

# Path Setup
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Mock Streamlit
st_mock = unittest.mock.MagicMock()
st_mock.session_state = {}
st_mock.query_params = {}
sys.modules['streamlit'] = st_mock
sys.modules['streamlit.components.v1'] = unittest.mock.MagicMock()

from src.email.attachment_manager import AttachmentManager
from src.database.database_manager import get_db_manager

def test_sync():
    client_email = "stephenrouxel22@orange.fr"
    print(f"🔄 Déclenchement de la synchronisation pour {client_email}...")
    
    # Charger les secrets manuellement pour le manager
    import toml
    secrets_path = os.path.join(root_dir, '.streamlit', 'secrets.toml')
    secrets = toml.load(secrets_path)
    
    # Force SQLite for local simulation test
    os.environ['DATABASE_TYPE'] = 'sqlite'
    os.environ['DATABASE_PATH'] = os.path.join(root_dir, 'data', 'recours_ecommerce.db')
    
    os.environ['IMAP_SERVER'] = 'imap.orange.fr'
    os.environ['IMAP_PORT'] = '993'
    os.environ['IMAP_USERNAME'] = secrets['email']['username']
    os.environ['IMAP_PASSWORD'] = secrets['email']['password']
    
    manager = AttachmentManager()
    result = manager.sync_emails(client_email)
    
    print(f"📊 Résultat Sync: {result['message']}")
    
    # Vérification en BDD
    print("\n🧐 Vérification des résultats AI en base de données...")
    db = get_db_manager()
    conn = db.get_connection()
    cursor = conn.execute("SELECT claim_reference, status, ai_reason_key, ai_advice FROM claims WHERE claim_reference = 'CLM-20260207-SIMUL'")
    claim = cursor.fetchone()
    
    if claim:
        print(f"✅ Réclamation trouvée : {claim['claim_reference']}")
        print(f"   Statut : {claim['status']}")
        print(f"   AI Reason : {claim['ai_reason_key']}")
        print(f"   AI Advice : {claim['ai_advice']}")
    else:
        print("❌ Réclamation non trouvée en base.")
        
    cursor = conn.execute("SELECT attachment_filename, ai_analysis FROM email_attachments WHERE claim_reference = 'CLM-20260207-SIMUL'")
    attachments = cursor.fetchall()
    for att in attachments:
        print(f"📎 Pièce jointe : {att['attachment_filename']}")
        print(f"   Analyse AI : {att['ai_analysis']}")
        
    conn.close()

if __name__ == "__main__":
    test_sync()
