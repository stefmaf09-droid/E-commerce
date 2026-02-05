
import logging
import google.generativeai as genai
from typing import List, Dict, Generator
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.config import Config

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
        """Configure l'API Gemini avec config centralisée."""
        api_key = Config.get_gemini_api_key()

        if not api_key:
            logger.error("GEMINI_API_KEY non trouvée. Le chatbot ne fonctionnera pas.")
            return

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        logger.info("Gemini model initialized successfully")

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
            # Call Gemini with retry logic
            response = self._call_gemini_with_retry(full_prompt)
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            # Sanitize error to prevent API key leakage
            error_type = type(e).__name__
            logger.error(f"Gemini API Error after retries: {error_type}")
            yield "Désolé, j'ai rencontré une erreur technique."
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True
    )
    def _call_gemini_with_retry(self, prompt: str):
        """Call Gemini API with automatic retry on transient failures."""
        logger.debug("Calling Gemini API (with retry logic)")
        return self.model.generate_content(prompt, stream=True)
