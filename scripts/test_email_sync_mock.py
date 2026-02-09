
import os
import sys
from unittest.mock import MagicMock, patch

# Path Setup
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from src.email.attachment_manager import AttachmentManager

def test_mock_sync():
    print("🚀 Démarrage du test de synchronisation simulé...")
    
    # Mock des dépendances
    with patch('src.email.attachment_manager.EmailListener') as MockListener:
        with patch('src.email.attachment_manager.AttachmentExtractor') as MockExtractor:
            with patch('src.database.database_manager.get_db_manager') as MockDB:
                
                # Setup Mocks
                instance = MockListener.return_value
                instance.connect.return_value = True
                
                # Simuler un email
                mock_msg = MagicMock()
                instance.fetch_unread_emails.return_value = [{
                    'id': b'1',
                    'subject': 'Litige CLM-20260207-ABC',
                    'from': 'chronopost@transport.com',
                    'date': 'Sat, 07 Feb 2026 12:00:00 +0000',
                    'message': mock_msg
                }]
                
                # Simuler l'extraction
                MockExtractor.return_value.extract_attachments.return_value = [{
                    'original_filename': 'preuve.pdf',
                    'saved_path': '/tmp/preuve.pdf',
                    'file_size': 1234,
                    'mime_type': 'application/pdf'
                }]
                
                # Simuler la DB
                MockDB.return_value.create_email_attachment.return_value = 42
                
                # Exécution
                manager = AttachmentManager()
                # Injecter les mocks manuellement si nécessaire ou laisser patch faire
                manager.extractor = MockExtractor.return_value
                manager.db = MockDB.return_value
                
                # Simuler les variables d'environnement pour passer la validation initiale
                with patch.dict(os.environ, {"IMAP_USERNAME": "test", "IMAP_PASSWORD": "test"}):
                    result = manager.sync_emails('demo@refundly.ai')
                
                # Vérifications
                print(f"Résultat : {result['message']}")
                if result['success'] and result['attachments']:
                    print("✅ Test réussi : Pièce jointe extraite et enregistrée en simulation.")
                    print(f"   Détails : {result['attachments'][0]['original_filename']} (ID: {result['attachments'][0]['db_id']})")
                else:
                    print("❌ Test échoué.")

if __name__ == "__main__":
    test_mock_sync()
