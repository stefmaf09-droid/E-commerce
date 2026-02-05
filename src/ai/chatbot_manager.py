
import os
import logging
import google.generativeai as genai
from typing import List, Dict, Generator

logger = logging.getLogger(__name__)

class ChatbotManager:
    """
    Gestionnaire du chatbot Refundly Assistant.
    Utilise Google Gemini pour répondre aux questions en se basant sur la FAQ.
    """

    def __init__(self):
        """Initialise le modèle Gemini et charge la base de connaissances."""
        self._setup_gemini()
        self.context = self._load_knowledge_base()

    def _setup_gemini(self):
        """Configure l'API Gemini."""
        # Try retrieving standard GEMINI_API_KEY or GOOGLE_API_KEY (common alternative)
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        
        # Fallback to streamlit secrets if not in env (for local dev)
        if not api_key:
            try:
                import toml
                secrets_path = os.path.join(os.path.dirname(__file__), '..', '..', '.streamlit', 'secrets.toml')
                if os.path.exists(secrets_path):
                    secrets = toml.load(secrets_path)
                    api_key = secrets.get("GEMINI_API_KEY") or secrets.get("GOOGLE_API_KEY")
            except Exception as e:
                logger.warning(f"Could not load secrets for Gemini: {e}")

        if not api_key:
            logger.error("GEMINI_API_KEY/GOOGLE_API_KEY non trouvée. Le chatbot ne fonctionnera pas.")
            return

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    def _load_knowledge_base(self) -> str:
        """Charge le contenu du fichier FAQ.md pour servir de contexte."""
        try:
            # Remonte de 2 niveaux (src/ai) -> racine -> FAQ.md
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            faq_path = os.path.join(base_dir, 'FAQ.md')
            
            if os.path.exists(faq_path):
                with open(faq_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                logger.warning(f"FAQ.md not found at {faq_path}")
                return "Aucune base de connaissances disponible."
        except Exception as e:
            logger.error(f"Error loading FAQ: {e}")
            return "Erreur lors du chargement de la base de connaissances."

    def generate_response_stream(self, user_input: str, history: List[Dict[str, str]]) -> Generator[str, None, None]:
        """
        Génère une réponse en streaming en utilisant l'historique et le contexte.
        """
        if not hasattr(self, 'model'):
            yield "Désolé, je ne suis pas correctement configuré (Clé API manquante)."
            return

        # Construction du prompt système avec RAG-lite
        system_prompt = f"""
        Tu es l'Assistant Refundly, un expert en recouvrement de litiges e-commerce et logistique.
        Ton rôle est d'aider les marchands à comprendre comment utiliser la plateforme Refundly.ai et à gérer leurs litiges transporteurs.
        
        Utilise le contexte suivant (extrait de la FAQ officielle) pour répondre aux questions.
        Si la réponse n'est pas dans le contexte, utilise tes connaissances générales en logistique et droit du transport (Code de Commerce Art L. 133-3, Convention CMR), mais précise que ce n'est pas spécifique à Refundly.
        Sois professionnel, concis et serviable. Réponds toujours en Français.
        
        --- CONTEXTE FAQ ---
        {self.context}
        --- FIN CONTEXTE ---
        """
        
        # Préparation de l'historique pour Gemini
        # Gemini attend un format spécifique, mais pour simplifier on concatène dans le prompt ou on utilise start_chat
        # Ici on va rester simple et stateless pour l'instant, ou reconstruire le chat
        
        chat = self.model.start_chat(history=[])
        
        # On injecte le system prompt + la question actuelle
        full_prompt = f"{system_prompt}\n\nHistorique de conversation:\n"
        for msg in history[-5:]: # Garde les 5 derniers échanges pour le contexte immédiat
            role = "Utilisateur" if msg["role"] == "user" else "Assistant"
            full_prompt += f"{role}: {msg['content']}\n"
            
        full_prompt += f"\nUtilisateur: {user_input}\nAssistant:"
        
        try:
            response = self.model.generate_content(full_prompt, stream=True)
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            # Sanitize error to prevent API key leakage
            error_type = type(e).__name__
            logger.error(f"Gemini API Error: {error_type}")
            yield "Désolé, j'ai rencontré une erreur technique."
