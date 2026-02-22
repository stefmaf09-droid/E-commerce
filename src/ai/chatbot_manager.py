
import os
import logging
import json
import google.generativeai as genai
from typing import List, Dict, Generator, Optional, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.config import Config
from src.database.database_manager import get_db_manager
from src.ai.chatbot_tools import ChatbotTools

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
        """Configure l'API Gemini avec config centralisée et function calling."""
        api_key = Config.get_gemini_api_key()

        if not api_key:
            logger.error("GEMINI_API_KEY non trouvée. Le chatbot ne fonctionnera pas.")
            return

        genai.configure(api_key=api_key)
        
        # Initialiser les tools
        self.tools = ChatbotTools()
        
        # Créer le modèle AVEC function calling
        try:
            # En version 0.8.6, il est plus stable d'utiliser genai.types.Tool
            from google.generativeai.types import Tool, FunctionDeclarationsTool, FunctionDeclaration
            
            declarations = []
            for tool_dict in self.tools.get_available_tools():
                declarations.append(FunctionDeclaration(
                    name=tool_dict['name'],
                    description=tool_dict['description'],
                    parameters=tool_dict['parameters']
                ))
            
            # Utiliser la structure attendue par genai
            gemini_tools = [Tool(function_declarations=declarations)]
            
            # Utiliser gemini-2.0-flash (disponible dans cet environnement)
            self.model = genai.GenerativeModel(
                'gemini-2.0-flash',
                tools=gemini_tools
            )
            logger.info("Gemini model initialized successfully with gemini-2.0-flash")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model with tools: {e}")
            # Fallback stable
            try:
                self.model = genai.GenerativeModel('gemini-2.0-flash')
                logger.warning("Gemini model initialized WITHOUT function calling (fallback to 2.0-flash)")
            except Exception as e2:
                logger.error(f"Failed to initialize Gemini model: {e2}")
                self.model = None

    def _load_knowledge_base(self) -> str:
        """Charge le contenu de la base de connaissances enrichie."""
        try:
            # Remonte de 2 niveaux (src/ai) -> racine
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            # Charge la base de connaissances technique (knowledge_base.md)
            kb_path = os.path.join(base_dir, 'src', 'ai', 'knowledge_base.md')
            knowledge = ""
            
            if os.path.exists(kb_path):
                with open(kb_path, 'r', encoding='utf-8') as f:
                    knowledge = f.read()
                logger.info("Knowledge base loaded successfully")
            else:
                # Fallback sur la FAQ si knowledge_base n'existe pas
                faq_path = os.path.join(base_dir, 'FAQ.md')
                if os.path.exists(faq_path):
                    with open(faq_path, 'r', encoding='utf-8') as f:
                        knowledge = f.read()
                    logger.warning("Using FAQ.md as fallback")
                else:
                    logger.error("No knowledge base found")
                    return "Aucune base de connaissances disponible."
            
            return knowledge
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")
            return "Erreur lors du chargement de la base de connaissances."

    def _load_client_context(self, client_email: str) -> str:
        """Charge le contexte spécifique du client depuis la base de données."""
        try:
            db = get_db_manager()
            
            # Récupérer les infos du client
            client = db.get_client(email=client_email)
            if not client:
                return "Client non trouvé en base de données."
            
            client_id = client['id']
            
            # Statistiques générales
            stats = db.get_client_statistics(client_id)
            
            # Réclamations récentes
            recent_claims = db.get_client_claims(client_id)
            
            # Litiges non réclamés
            disputes = db.get_client_disputes(client_id, is_claimed=False)
            
            # Construire le contexte
            context_parts = []
            context_parts.append("--- CONTEXTE CLIENT ---")
            context_parts.append(f"Email: {client_email}")
            context_parts.append(f"Nom: {client.get('full_name', 'N/A')}")
            context_parts.append(f"Entreprise: {client.get('company_name', 'N/A')}")
            
            # Statistiques
            if stats:
                context_parts.append("\nStatistiques:")
                total_claims = stats.get('total_claims', 0) or 0
                accepted_claims = stats.get('accepted_claims', 0) or 0
                pending_claims = stats.get('pending_claims', 0) or 0
                total_requested = stats.get('total_requested', 0) or 0
                total_recovered = stats.get('total_recovered', 0) or 0
                total_paid = stats.get('total_paid_to_client', 0) or 0
                
                success_rate = (accepted_claims / total_claims * 100) if total_claims > 0 else 0
                
                context_parts.append(f"  - Total réclamations: {total_claims}")
                context_parts.append(f"  - Acceptées: {accepted_claims} ({success_rate:.1f}% de succès)")
                context_parts.append(f"  - En attente: {pending_claims}")
                context_parts.append(f"  - Montant demandé: {total_requested:.2f} EUR")
                context_parts.append(f"  - Montant récupéré: {total_recovered:.2f} EUR")
                context_parts.append(f"  - Montant versé au client: {total_paid:.2f} EUR")
            
            # Réclamations récentes (5 dernières)
            if recent_claims:
                context_parts.append("\nRéclamations récentes:")
                for claim in recent_claims[:5]:
                    ref = claim.get('claim_reference', 'N/A')
                    carrier = claim.get('carrier', 'N/A')
                    dispute_type = claim.get('dispute_type', 'N/A')
                    amount = claim.get('amount_requested', 0)
                    status = claim.get('status', 'N/A')
                    context_parts.append(f"  - {ref} ({carrier}, {dispute_type}, {amount} EUR, status: {status})")
            
            # Litiges en attente
            if disputes:
                total_recoverable = sum(d.get('amount_recoverable', 0) for d in disputes)
                context_parts.append(f"\nLitiges détectés non réclamés: {len(disputes)} litiges ({total_recoverable:.2f} EUR récupérable)")
            
            context_parts.append("--- FIN CONTEXTE CLIENT ---")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Error loading client context: {e}")
            return "Erreur lors du chargement du contexte client."

    def generate_response_stream(self, user_input: str, history: List[Dict[str, str]], client_email: Optional[str] = None) -> Generator[str, None, None]:
        """
        Génère une réponse en streaming en utilisant l'historique et le contexte.
        
        Args:
            user_input: Question de l'utilisateur
            history: Historique de la conversation
            client_email: Email du client connecté (pour contexte personnalisé)
        """
        if not hasattr(self, 'model'):
            yield "Désolé, je ne suis pas correctement configuré (Clé API manquante)."
            return

        # Construction du prompt système avec base de connaissances enrichie
        system_prompt = f"""
        Tu es l'Assistant Refundly, un expert en recouvrement de litiges e-commerce et logistique.
        Ton rôle est d'aider les marchands à comprendre et utiliser la plateforme Refundly.ai.
        
        IMPORTANT - UTILISATION DES OUTILS DISPONIBLES :
        Tu as accès à des outils pour EXÉCUTER DES ACTIONS RÉELLES. Utilise-les systématiquement pour :
        - "suivre un colis" / "où est mon colis" / "état du colis [numéro]" → APPELLE get_tracking_status(tracking_number="...")
        - "exporter" / "télécharger" / "récupérer en CSV" / "exporter litiges" → APPELLE export_claims_csv()
        - "créer une réclamation" / "faire une réclamation" → APPELLE create_claim()
        - "relancer" / "envoyer un rappel" → APPELLE send_carrier_reminder()
        - "marquer comme payé" / "enregistrer paiement" → APPELLE mark_claim_paid()
        - "lister mes réclamations" / "voir mes dossiers" → APPELLE list_pending_claims()
        
        VOCABULAIRE - Ces termes sont ÉQUIVALENTS :
        - Réclamation = Claim = Dossier = Litige (dans le contexte de gestion Refundly)
        - Exporter = Télécharger = Récupérer les données
        
        RÈGLES CRUCIALES:
        1. Quand l'utilisateur demande une ACTION concrète (suivre un colis, exporter, créer, relancer, etc.),
           tu DOIS appeler la fonction correspondante au lieu de juste expliquer comment faire.
        2. Utilise TOUJOURS le contexte fourni pour répondre de manière précise
        3. Si le client a des données personnels (réclamations, statistiques), cite-les explicitement
        4. Cite les références de réclamations (CLM-XXXXXX-XXX) quand pertinent
        5. Pour les questions juridiques, cite les articles de loi appropriés
        6. Sois concis, professionnel et serviable
        7. Réponds TOUJOURS en Français
        
        --- BASE DE CONNAISSANCES REFUNDLY ---
        {self.context}
        --- FIN BASE DE CONNAISSANCES ---
        """
        
        # Ajouter le contexte client si disponible
        client_context = ""
        if client_email:
            client_context = self._load_client_context(client_email)
            system_prompt += f"\n\n{client_context}\n"
        
        # FALLBACK MANUEL: Détecter les intentions d'action directement
        # Car Gemini ne déclenche pas toujours les function calls de manière fiable
        user_input_lower = user_input.lower()
        
        # Détection: Suivi de colis (regex simple pour numéros de suivi communs)
        import re
        tracking_match = re.search(r'([A-Z0-9]{10,20})', user_input)
        if tracking_match and any(kw in user_input_lower for kw in ['colis', 'suivi', 'tracking', 'où est', 'info']):
            tracking_number = tracking_match.group(1)
            # Éviter de matcher des dates ou des ref de claims
            if not tracking_number.startswith('CLM-') and not re.match(r'^\d{4}-\d{2}-\d{2}$', tracking_number):
                logger.info(f"MANUAL TRIGGER: get_tracking_status detected for {tracking_number}")
                yield f"🔍 Analyse du colis {tracking_number} en cours...\n\n"
                
                result = self.tools.execute_tool('get_tracking_status', {
                    'tracking_number': tracking_number
                })
                
                if result['success']:
                    data = result['data']
                    yield f"✅ **Statut : {data.get('status', 'Inconnu')}** ({data.get('carrier', 'Inconnu')})\n\n"
                    
                    if data.get('delivery_date'):
                        yield f"📅 Livré le : {data['delivery_date']}\n"
                    
                    if data.get('events'):
                        yield "\n**Derniers événements :**\n"
                        for event in data['events'][:3]:
                            yield f"- {event.get('label')} ({event.get('date', '')[:10]})\n"
                    
                    yield "\n💡 *Vous pouvez maintenant me demander de créer une réclamation si ce statut ne correspond pas à la réalité.*"
                else:
                    yield f"❌ {result['message']}\n"
                return

        # Détection: Export CSV
        if any(keyword in user_input_lower for keyword in ['exporter', 'export', 'télécharger', 'download', 'csv']):
            if any(keyword in user_input_lower for keyword in ['litige', 'réclamation', 'claim', 'dossier']):
                logger.info(f"MANUAL TRIGGER: export_claims_csv detected from user input")
                yield "🔧 Détection automatique : Export CSV demandé...\n\n"
                
                result = self.tools.execute_tool('export_claims_csv', {
                    'client_email': client_email or 'demo@refundly.ai'
                })
                
                if result['success']:
                    yield f"✅ {result['message']}\n\n"
                    
                    if 'data' in result and result['data']:
                        csv_content = result['data'].get('csv_content', '')
                        count = result['data'].get('count', 0)
                        
                        if csv_content:
                            yield f"📄 **Fichier CSV généré** ({count} réclamation(s)) :\n\n"
                            yield f"```csv\n{csv_content}\n```\n\n"
                            yield "💡 **Copier-coller** ce contenu dans Excel/Sheets ou enregistrer en .csv\n"
                        else:
                            yield "ℹ️ Aucune donnée à exporter.\n"
                else:
                    yield f"❌ {result['message']}\n"
                
                return  # STOP: ne pas appeler Gemini après
        
        # Si pas de détection manuelle, continuer avec Gemini normalement
        # Préparation de l'historique pour Gemini
        chat = self.model.start_chat(history=[])
        
        # Construire le prompt complet
        full_prompt = f"{system_prompt}\n\nHistorique de conversation:\n"
        for msg in history[-5:]:  # Garde les 5 derniers échanges
            role = "Utilisateur" if msg["role"] == "user" else "Assistant"
            full_prompt += f"{role}: {msg['content']}\n"
            
        full_prompt += f"\nUtilisateur: {user_input}\nAssistant:"
        
        
        try:
            # Call Gemini with retry logic
            logger.info(f"Sending prompt to Gemini (user: {client_email or 'anonymous'})")
            response = self._call_gemini_with_retry(full_prompt)
            
            # Stream la réponse sans essayer de détecter les function calls (pas supportés pour l'instant)
            for chunk in response:
                try:
                    # Extraire le texte du chunk
                    if hasattr(chunk, 'text'):
                        yield chunk.text
                    elif hasattr(chunk, 'parts'):
                        for part in chunk.parts:
                            if hasattr(part, 'text'):
                                yield part.text
                            # Détecter si c'est un function call
                            if hasattr(part, 'function_call'):
                                function_call_detected = True
                                fc = part.function_call
                                
                                # Exécuter la fonction
                                yield f"🔧 Exécution de l'action : {fc.name}...\n\n"
                                
                                # Convertir les args en dict
                                params = {k: v for k, v in fc.args.items()}
                                
                                # Ajouter client_email si nécessaire
                                if 'client_email' in params and params['client_email'] == 'CURRENT_USER':
                                    params['client_email'] = client_email
                                
                                # Exécuter
                                result = self.tools.execute_tool(fc.name, params)
                                
                                if result['success']:
                                    yield f"✅ {result['message']}\n\n"
                                    if 'data' in result and result['data']:
                                        # Formater les données de retour
                                        yield f"📋 Détails :\n"
                                        if isinstance(result['data'], dict):
                                            for key, value in result['data'].items():
                                                yield f"- {key}: {value}\n"
                                        else:
                                            yield f"{result['data']}\n"
                                else:
                                    yield f"❌ Erreur : {result['message']}\n"
                                
                                logger.info(f"Function call executed: {fc.name} - Success: {result['success']}")
                                # IMPORTANT: Stopper la génération pour éviter que Gemini invente du texte
                                return
                except Exception as chunk_error:
                    logger.warning(f"Error processing chunk: {chunk_error}")
                    continue
                    
        except Exception as e:
            error_msg = f"Erreur lors de l'appel à Gemini: {str(e)}"
            logger.error(error_msg, exc_info=True)
            yield f"Désolé, j'ai rencontré une erreur technique: {str(e)}"
    
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
