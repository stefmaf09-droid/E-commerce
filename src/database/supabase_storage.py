import os
import logging
from typing import Optional, List, Dict, Any

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = Any # type hint fallback

logger = logging.getLogger(__name__)

class SupabaseStorageManager:
    """Gestionnaire de stockage pour Supabase Storage."""
    
    def __init__(self):
        """Initialise le client Supabase à partir des variables d'environnement."""
        if not SUPABASE_AVAILABLE:
            logger.warning("Supabase library not installed. Cloud storage disabled.")
            self.client = None
            return

        self.url = os.getenv("SUPABASE_URL")

        self.key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") # Utiliser service_role pour outrepasser RLS
        self.bucket_name = os.getenv("SUPABASE_STORAGE_BUCKET", "evidence")
        
        if not self.url or not self.key:
            logger.warning("Supabase credentials missing. Cloud storage disabled.")
            self.client = None
        else:
            try:
                self.client: Client = create_client(self.url, self.key)
                logger.info("Supabase client initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
                self.client = None

    def upload_file(self, claim_id: str, filename: str, file_content: bytes, content_type: str = None) -> Optional[str]:
        """
        Upload un fichier vers Supabase Storage.
        
        Chemin : {claim_id}/{filename}
        """
        if not self.client:
            logger.error("Supabase client not available for upload.")
            return None
            
        path = f"{claim_id}/{filename}"
        
        try:
            # check if file exist to decide between upload or update or just handle error
            # Simple approach: delete if exists then upload or use upset
            # Supabase Python SDK doesn't always have a clean 'upsert' for storage yet in all versions
            
            # Options for upload
            opts = {"cache-control": "3600", "upsert": "true"}
            if content_type:
                opts["content-type"] = content_type
                
            res = self.client.storage.from_(self.bucket_name).upload(
                path=path,
                file=file_content,
                file_options=opts
            )
            
            logger.info(f"File uploaded to Supabase Storage: {path}")
            return path
        except Exception as e:
            logger.error(f"Error uploading to Supabase: {e}")
            return None

    def get_public_url(self, path: str) -> Optional[str]:
        """Récupère l'URL publique d'un fichier."""
        if not self.client:
            return None
        try:
            return self.client.storage.from_(self.bucket_name).get_public_url(path)
        except Exception as e:
            logger.error(f"Error getting public URL: {e}")
            return None

    def list_files(self, claim_id: str) -> List[Dict[str, Any]]:
        """Liste les fichiers pour un litige donné."""
        if not self.client:
            return []
        try:
            return self.client.storage.from_(self.bucket_name).list(claim_id)
        except Exception as e:
            logger.error(f"Error listing files in Supabase: {e}")
            return []

    def download_file(self, path: str) -> Optional[bytes]:
        """Télécharge un fichier depuis Supabase Storage."""
        if not self.client:
            return None
        try:
            return self.client.storage.from_(self.bucket_name).download(path)
        except Exception as e:
            logger.error(f"Error downloading from Supabase: {e}")
            return None

# Instance globale
_storage_manager = None

def get_storage_manager() -> SupabaseStorageManager:
    """Obtenir l'instance globale du gestionnaire de stockage."""
    global _storage_manager
    if _storage_manager is None:
        _storage_manager = SupabaseStorageManager()
    return _storage_manager
