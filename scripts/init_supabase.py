import os
import requests
import json
from supabase import create_client, Client

# Configuration à partir des entrées utilisateur
SUPABASE_URL = "https://lrvqbgirvwytkmmmwjsx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxydnFiZ2lydnd5dGttbW13anN4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MDIwODY4OCwiZXhwIjoyMDg1Nzg0Njg4fQ.qEGlbLr04Z_-k5oPoIfxRfoi09T0FLNpGsw63wqh584"
SCHEMA_PATH = "database/schema_postgres.sql"

def initialize_supabase():
    print(f"🚀 Initialisation de Supabase : {SUPABASE_URL}")
    
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # 1. Création du Bucket de Stockage
        print("📁 Création du bucket 'evidence'...")
        try:
            res = supabase.storage.create_bucket('evidence', options={'public': True})
            print("✅ Bucket 'evidence' créé avec succès.")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("ℹ️ Le bucket 'evidence' existe déjà.")
            else:
                print(f"⚠️ Erreur lors de la création du bucket : {e}")

        # 2. Exécution du Schéma SQL
        # Note: Le SDK Python ne permet pas d'exécuter du SQL brut directement pour des raisons de sécurité.
        # Il faut passer par l'interface SQL Editor de Supabase pour le schéma.
        print("\n📥 Pour la base de données :")
        print("Le script ne peut pas exécuter le SQL brut directement via l'API client.")
        print(f"Veuillez copier le contenu de {SCHEMA_PATH} dans le 'SQL Editor' de votre dashboard Supabase.")
        
        # 3. Test de connexion simple
        print("\n🔍 Test de connexion au projet...")
        # On essaie de lister les buckets pour vérifier la clé
        buckets = supabase.storage.list_buckets()
        print(f"✅ Connexion réussie ! Clé valide. {len(buckets)} bucket(s) détecté(s).")
        
    except Exception as e:
        print(f"❌ Erreur critique : {e}")

if __name__ == "__main__":
    initialize_supabase()
