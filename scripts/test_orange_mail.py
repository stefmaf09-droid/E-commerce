
import os
import sys
import toml

# Path Setup
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from src.email.attachment_manager import AttachmentManager

def test_orange_sync():
    print("🟠 Test de synchronisation Orange pour: stephenrouxel22@orange.fr")
    
    # Charger les secrets
    secrets_path = os.path.join(root_dir, '.streamlit', 'secrets.toml')
    if not os.path.exists(secrets_path):
        print(f"❌ Fichier {secrets_path} introuvable.")
        return
        
    try:
        secrets = toml.load(secrets_path)
        email_config = secrets.get('email', {})
        
        username = email_config.get('username')
        password = email_config.get('password')
        
        if not password or password == "VOTRE_MOT_DE_PASSE_ICI":
            print("❌ Erreur: Vous devez d'abord mettre votre mot de passe dans .streamlit/secrets.toml")
            return
            
        # Configurer les variables d'environnement manuellement pour le manager
        os.environ['IMAP_SERVER'] = email_config.get('imap_server', 'imap.orange.fr')
        os.environ['IMAP_PORT'] = str(email_config.get('imap_port', 993))
        os.environ['IMAP_USERNAME'] = username
        os.environ['IMAP_PASSWORD'] = password
        
        print(f"🔌 Connexion à {os.environ['IMAP_SERVER']}...")
        
        manager = AttachmentManager()
        result = manager.sync_emails(username)
        
        if result['success']:
            print(f"✅ {result['message']}")
            if 'attachments' in result and result['attachments']:
                print(f"📂 {len(result['attachments'])} pièces jointes extraites !")
                for att in result['attachments']:
                    print(f"   - {att['original_filename']} ({att['file_size']} octets)")
            else:
                print("ℹ️ Aucune nouvelle pièce jointe trouvée (tous les mails non-lus ont été traités).")
        else:
            print(f"❌ Échec: {result['message']}")
            
    except Exception as e:
        print(f"💥 Erreur critique: {e}")

if __name__ == "__main__":
    test_orange_sync()
