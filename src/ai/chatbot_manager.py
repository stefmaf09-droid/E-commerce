
import os
import logging
import json
from google import genai
from google.genai import types
from typing import List, Dict, Generator, Optional, Any

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

        # Nouveau SDK : client avec api_key
        self.client = genai.Client(api_key=api_key)

        # Initialiser les tools
        self.tools = ChatbotTools()

        # Construire les function declarations pour le function calling
        try:
            declarations = []
            for tool_dict in self.tools.get_available_tools():
                declarations.append(types.FunctionDeclaration(
                    name=tool_dict['name'],
                    description=tool_dict['description'],
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            k: types.Schema(
                                type=types.Type.STRING if v.get('type') == 'string' else types.Type.NUMBER,
                                description=v.get('description', '')
                            )
                            for k, v in tool_dict['parameters'].get('properties', {}).items()
                        },
                        required=tool_dict['parameters'].get('required', [])
                    )
                ))

            self.gemini_tools = [types.Tool(function_declarations=declarations)]
            self.model_name = 'gemini-2.0-flash'
            logger.info("Gemini client initialized (google.genai SDK) with gemini-2.0-flash + function calling")
        except Exception as e:
            logger.error(f"Failed to build function declarations: {e}")
            self.gemini_tools = None
            self.model_name = 'gemini-2.0-flash'
            logger.warning("Gemini initialized WITHOUT function calling (fallback)")

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
        if not hasattr(self, 'client'):
            yield "Désolé, je ne suis pas correctement configuré (Clé API manquante)."
            return

        # Construction du prompt système — allégé pour économiser les tokens
        # Les questions qui arrivent ici sont purement conversationnelles/Q&A
        system_prompt = (
            "Tu es l'Assistant Refundly.AI, expert en litiges e-commerce et logistique.\n"
            "Réponds TOUJOURS en Français. Sois concis, précis et professionnel.\n"
            "Aide le client à comprendre la plateforme, ses droits, et les démarches.\n\n"
            "--- BASE DE CONNAISSANCES ---\n"
            f"{self.context}\n"
            "--- FIN BASE DE CONNAISSANCES ---\n"
        )

        # Ajouter le contexte client si disponible
        client_context = ""
        if client_email:
            client_context = self._load_client_context(client_email)
            system_prompt += f"\n{client_context}\n"

        
        # FALLBACK MANUEL: Détecter les intentions d'action directement
        # Car Gemini ne déclenche pas toujours les function calls de manière fiable
        user_input_lower = user_input.lower()
        import re

        # ── 1. SUIVI DE COLIS ────────────────────────────────────────────────
        tracking_match = re.search(r'([A-Z]{2}[A-Z0-9]{8,18}[A-Z]{2}|[A-Z0-9]{10,25})', user_input)
        if tracking_match and any(kw in user_input_lower for kw in ['colis', 'suivi', 'tracking', 'où est', 'info', 'livraison']):
            tracking_number = tracking_match.group(1)
            if not tracking_number.startswith('CLM-') and not re.match(r'^\d{4}-\d{2}-\d{2}$', tracking_number):
                logger.info(f"MANUAL TRIGGER: get_tracking_status for {tracking_number}")
                yield f"🔍 Analyse du colis **{tracking_number}** en cours...\n\n"
                result = self.tools.execute_tool('get_tracking_status', {'tracking_number': tracking_number})
                if result['success']:
                    data = result.get('data', {})
                    yield f"✅ **Statut : {data.get('status', 'Inconnu')}** ({data.get('carrier', 'Inconnu')})\n\n"
                    if data.get('delivery_date'):
                        yield f"📅 Livré le : {data['delivery_date']}\n"
                    if data.get('events'):
                        yield "\n**Derniers événements :**\n"
                        for event in data['events'][:3]:
                            yield f"- {event.get('label', '')} ({event.get('date', '')[:10]})\n"
                    yield "\n💡 *Demandez-moi de créer une réclamation si ce statut est incorrect.*"
                else:
                    yield f"❌ {result['message']}\n"
                return

        # ── 2. LISTER LES RÉCLAMATIONS ──────────────────────────────────────
        if any(kw in user_input_lower for kw in ['mes réclamations', 'mes dossiers', 'mes litiges', 'liste', 'lister', 'voir mes', 'afficher mes', 'quelles réclamations', 'quels dossiers']):
            if any(kw in user_input_lower for kw in ['réclamation', 'dossier', 'litige', 'claim', 'en attente', 'pending']):
                logger.info("MANUAL TRIGGER: list_pending_claims")
                yield "📋 Chargement de vos réclamations...\n\n"
                result = self.tools.execute_tool('list_pending_claims', {'client_email': client_email or 'demo@refundly.ai'})
                if result['success']:
                    claims = result.get('data', {}).get('claims', [])
                    if claims:
                        yield f"**{len(claims)} réclamation(s) trouvée(s) :**\n\n"
                        yield "| Référence | Transporteur | Type | Montant | Statut | Relance |\n"
                        yield "|---|---|---|---|---|---|\n"
                        for c in claims[:10]:
                            level = c.get('follow_up_level') or 0
                            last_fu = c.get('last_follow_up_at') or ''
                            status = c.get('status', '')
                            if level == 0:
                                # Rejected sans aucune relance = signal d'alarme
                                if status == 'rejected':
                                    relance_cell = "⚠️ Rejeté sans suivi"
                                elif status == 'accepted':
                                    relance_cell = "✅ Résolu"
                                else:
                                    relance_cell = "🟢 Aucune"
                            else:
                                # Calculer l'ancienneté de la dernière relance
                                try:
                                    from datetime import datetime as _dt
                                    last_d = _dt.fromisoformat(last_fu[:19])
                                    days = (_dt.now() - last_d).days
                                    age = f"il y a {days}j" if days > 0 else "aujourd'hui"
                                except Exception:
                                    age = last_fu[:10] if last_fu else "?"
                                # Cas spécial : rejected malgré des relances
                                if status == 'rejected':
                                    relance_cell = f"🔴 {level}× — Rejeté malgré relances"
                                else:
                                    badge = "🟡" if level == 1 else ("🟠" if level == 2 else "🔴")
                                    relance_cell = f"{badge} {level}× ({age})"
                            yield f"| {c.get('claim_reference','N/A')} | {c.get('carrier','N/A')} | {c.get('dispute_type','N/A')} | {c.get('amount_requested',0):.2f}€ | {status or 'N/A'} | {relance_cell} |\n"
                        if len(claims) > 10:
                            yield f"\n*... et {len(claims)-10} autres.*\n"
                        yield "\n💡 Dites-moi si vous souhaitez relancer une réclamation ou exporter le tout en CSV."

                    else:
                        yield "ℹ️ Aucune réclamation en attente pour votre compte."
                else:
                    yield f"❌ {result['message']}"
                return

        # ── 3. RELANCE TRANSPORTEUR ───────────────────────────────────────────
        clm_match = re.search(r'(CLM-[\w-]+)', user_input.upper())
        if clm_match and any(kw in user_input_lower for kw in ['relancer', 'relance', 'rappel', 'remind', 'relance', 'suivre up', 'follow']):
            claim_ref = clm_match.group(1)
            logger.info(f"MANUAL TRIGGER: send_carrier_reminder for {claim_ref}")
            yield f"📨 Envoi d'une relance au transporteur pour **{claim_ref}**...\n\n"
            result = self.tools.execute_tool('send_carrier_reminder', {'claim_reference': claim_ref})
            if result['success']:
                yield f"✅ {result['message']}\n\n"
                yield "📅 La relance a été enregistrée. Le transporteur dispose de 30 jours pour répondre."
            else:
                yield f"❌ {result['message']}"
            return

        # ── 4. MARQUER COMME PAYÉ ────────────────────────────────────────────
        if clm_match and any(kw in user_input_lower for kw in ['payé', 'paiement', 'reçu', 'rembours', 'viré', 'encaiss']):
            claim_ref = clm_match.group(1)
            amount_match = re.search(r'(\d+[.,]?\d*)\s*€?', user_input)
            amount = float(amount_match.group(1).replace(',', '.')) if amount_match else 0.0
            logger.info(f"MANUAL TRIGGER: mark_claim_paid for {claim_ref} amount={amount}")
            yield f"💰 Enregistrement du paiement pour **{claim_ref}** ({amount:.2f}€)...\n\n"
            result = self.tools.execute_tool('mark_claim_paid', {'claim_reference': claim_ref, 'amount_received': amount})
            if result['success']:
                yield f"✅ {result['message']}\n"
            else:
                yield f"❌ {result['message']}"
            return

        # ── 5. EXPORT CSV ──────────────────────────────────────────────────────
        if any(kw in user_input_lower for kw in ['exporter', 'export', 'télécharger', 'download', 'csv']):
            if any(kw in user_input_lower for kw in ['litige', 'réclamation', 'claim', 'dossier']):
                logger.info("MANUAL TRIGGER: export_claims_csv")
                yield "🔧 Génération du fichier CSV...\n\n"
                result = self.tools.execute_tool('export_claims_csv', {'client_email': client_email or 'demo@refundly.ai'})
                if result['success']:
                    yield f"✅ {result['message']}\n\n"
                    data = result.get('data', {})
                    csv_content = data.get('csv_content', '')
                    count = data.get('count', 0)
                    if csv_content:
                        yield f"📄 **Fichier CSV** ({count} réclamation(s)) :\n\n```csv\n{csv_content}\n```\n\n"
                        yield "💡 Cliquez sur **Télécharger le CSV** ci-dessous pour sauvegarder le fichier."
                    else:
                        yield "ℹ️ Aucune donnée à exporter."
                else:
                    yield f"❌ {result['message']}"
                return

        # ── 6. CRÉATION RÉCLAMATION ──────────────────────────────────────────
        if any(kw in user_input_lower for kw in ['créer une réclamation', 'créer réclamation', 'nouvelle réclamation', 'ouvrir un dossier', 'faire une réclamation', 'déposer une réclamation']):
            # Vérifier si on a les infos nécessaires
            has_tracking = bool(re.search(r'[A-Z0-9]{10,25}', user_input))
            if has_tracking:
                logger.info("MANUAL TRIGGER: create_claim (forwarded to Gemini for params)")
            else:
                yield "📥 Pour créer une réclamation, j'ai besoin des informations suivantes :\n\n"
                yield "1. 📦 **Numéro de suivi** du colis\n"
                yield "2. 🚚 **Transporteur** (Colissimo, Chronopost, UPS, DHL...)\n"
                yield "3. ⚖️ **Type de litige** : perte, avarie, retard, fausse livraison\n"
                yield "4. 💶 **Montant** de la réclamation (en euros)\n\n"
                yield "💡 *Répondez avec ces informations et je créerai le dossier automatiquement.*"
                return

        # ── 7. CONTESTATION / LETTRE D'APPEL ───────────────────────────────────
        if clm_match and any(kw in user_input_lower for kw in [
            'contester', 'contestation', 'lettre', 'appel', 'recours',
            'mise en demeure', 'génère', 'genere', 'rédige', 'redige'
        ]):
            claim_ref = clm_match.group(1)
            logger.info(f"MANUAL TRIGGER: generate_appeal for {claim_ref}")
            yield f"⚖️ Génération de la lettre de contestation pour **{claim_ref}**\u2026\n\n"
            try:
                from src.database.database_manager import get_db_manager
                from src.ai.appeal_generator import AppealGenerator
                db = get_db_manager()
                claim = db.get_claim(claim_reference=claim_ref)
                if not claim:
                    yield f"❌ Dossier **{claim_ref}** introuvable en base."
                    return

                reason_key = claim.get('ai_reason_key') or 'default'
                dispute_data = {
                    'claim_reference': claim_ref,
                    'tracking_number': claim.get('tracking_number', 'N/A'),
                    'carrier': claim.get('carrier', 'le transporteur'),
                    'amount_requested': claim.get('amount_requested', 0),
                    'order_date': str(claim.get('order_date', 'N/A')),
                    'client_name': client_email or 'Client',
                    'client_email': client_email or '',
                    'recipient_name': claim.get('customer_name', 'le destinataire'),
                    'status': claim.get('status', ''),
                }

                # Détecter si mise en demeure (21j+) ou simple appel
                from datetime import datetime as _dt, timedelta
                last_fu = claim.get('last_follow_up_at') or claim.get('created_at') or ''
                is_formal_notice = False
                if last_fu:
                    try:
                        age_days = (_dt.now() - _dt.fromisoformat(str(last_fu)[:19])).days
                        is_formal_notice = age_days >= 21
                    except Exception:
                        pass

                if is_formal_notice:
                    from src.reports.legal_document_generator import LegalDocumentGenerator
                    yield f"📜 Dossier âgé de plus de 21 jours — génération d'une **mise en demeure**.\n\n"
                    gen = LegalDocumentGenerator()
                    import tempfile, pathlib
                    out_dir = "data/legal_docs"
                    pdf_path = gen.generate_formal_notice(claim, output_dir=out_dir)
                    pdf_bytes = pathlib.Path(pdf_path).read_bytes() if pdf_path else b""
                    doc_type = "Mise en Demeure"
                else:
                    gen = AppealGenerator()
                    letter_text = gen.generate(dispute_data, reason_key)
                    pdf_bytes = AppealGenerator.generate_pdf(letter_text, f"contestation_{claim_ref}.pdf")
                    doc_type = "Lettre de Contestation"

                if pdf_bytes:
                    import pathlib
                    save_dir = pathlib.Path("data/appeals")
                    save_dir.mkdir(parents=True, exist_ok=True)
                    ts = _dt.now().strftime("%Y%m%d_%H%M%S")
                    pdf_file = save_dir / f"{ts}_{claim_ref}_{doc_type.replace(' ', '_')}.pdf"
                    pdf_file.write_bytes(pdf_bytes)

                    # Mettre à jour le statut en 'appealing'
                    try:
                        db.update_claim(claim['id'], status='appealing')
                    except Exception:
                        pass

                    # Stocker le PDF pour téléchargement Streamlit
                    import streamlit as st
                    st.session_state['_appeal_pdf'] = {
                        'bytes': pdf_bytes,
                        'filename': pdf_file.name,
                        'doc_type': doc_type,
                        'claim_ref': claim_ref,
                    }
                    yield f"✅ **{doc_type}** générée pour {claim_ref}\n"
                    yield f"- Motif utilisé : `{reason_key}`\n"
                    yield f"- Statut dossier mis à jour : `appealing`\n\n"
                    yield "📥 **Cliquez sur le bouton de téléchargement ci-dessous** pour récupérer le PDF."
                else:
                    yield "⚠️ Génération PDF impossible (ReportLab manquant ?). Lettre texté disponible."
            except Exception as e:
                logger.error(f"Appeal generation failed: {e}")
                yield f"❌ Erreur lors de la génération : {e}"
            return

        # ── 8. STATISTIQUES / TAUX DE SUCCÈS ──────────────────────────────────
        if any(kw in user_input_lower for kw in [
            'statistique', 'stats', 'taux', 'succès', 'combien', 'récupéré',
            'remboursement', 'performance', 'bilan', 'résumé', 'résultats',
            'montant', 'total', 'dossiers clos', 'accepté', 'rejeté'
        ]) and any(kw in user_input_lower for kw in [
            'mes', 'mon', 'mes dossiers', 'mes réclamations', 'globales', 'global',
            'remboursement', 'statistique', 'stat', 'taux', 'bilan', 'performance'
        ]):
            logger.info("MANUAL TRIGGER: statistics from DB (no Gemini call)")
            try:
                from src.database.database_manager import get_db_manager
                db = get_db_manager()
                client = db.get_client(email=client_email) if client_email else None
                if not client:
                    yield "ℹ️ Impossible de charger vos statistiques (client non identifié)."
                    return
                client_id = client['id']
                stats = db.get_client_statistics(client_id) or {}
                claims = db.get_client_claims(client_id) or []

                total = stats.get('total_claims', 0) or 0
                accepted = stats.get('accepted_claims', 0) or 0
                pending = stats.get('pending_claims', 0) or 0
                rejected = total - accepted - pending if total > 0 else 0
                requested = stats.get('total_requested', 0) or 0
                recovered = stats.get('total_recovered', 0) or 0
                paid = stats.get('total_paid_to_client', 0) or 0
                rate = round(accepted / total * 100, 1) if total > 0 else 0

                # Répartition par transporteur
                carriers: dict = {}
                for c in claims:
                    car = c.get('carrier', 'Inconnu')
                    carriers[car] = carriers.get(car, 0) + 1
                top_carriers = sorted(carriers.items(), key=lambda x: -x[1])[:3]

                yield "📊 **Vos Statistiques Refundly.AI**\n\n"
                yield f"| Indicateur | Valeur |\n|---|---|\n"
                yield f"| 📋 Total dossiers | **{total}** |\n"
                yield f"| ✅ Acceptés | **{accepted}** ({rate}% de succès) |\n"
                yield f"| ⏳ En attente | **{pending}** |\n"
                yield f"| ❌ Rejetés | **{rejected}** |\n"
                yield f"| 💶 Montant réclamé | **{requested:,.2f} €** |\n"
                yield f"| 💰 Montant récupéré | **{recovered:,.2f} €** |\n"
                yield f"| 🏦 Versé à votre compte | **{paid:,.2f} €** |\n"

                if top_carriers:
                    yield "\n**Top transporteurs :**\n"
                    for car, cnt in top_carriers:
                        yield f"- {car} : {cnt} dossier(s)\n"

                if accepted == 0 and total > 0:
                    yield "\n💡 *Aucun dossier accepté encore — les délais de traitement transporteurs sont souvent de 30 à 60 jours.*"
                elif rate >= 50:
                    yield f"\n🎉 *Excellent taux de succès ({rate}%) — continuez !*"
            except Exception as e:
                logger.error(f"Stats handler error: {e}")
                yield f"❌ Erreur lors du chargement des statistiques : {e}"
            return

        # ── 9. STATUT D'UN DOSSIER SPÉCIFIQUE ────────────────────────────────
        if clm_match and any(kw in user_input_lower for kw in [
            'statut', 'état', 'avancement', 'info', 'détail', 'où en est',
            'quoi de neuf', 'news', 'progression', 'dossier', 'réclamation'
        ]):
            claim_ref = clm_match.group(1)
            logger.info(f"MANUAL TRIGGER: get_claim_details for {claim_ref}")
            yield f"🔍 Chargement du dossier **{claim_ref}**...\n\n"
            result = self.tools.execute_tool('get_claim_details', {'claim_reference': claim_ref})
            if result['success']:
                c = result['data']
                status_labels = {
                    'pending': '⏳ En attente',
                    'submitted': '📤 Soumis au transporteur',
                    'under_review': '🔍 En cours d\'instruction',
                    'accepted': '✅ Accepté',
                    'rejected': '❌ Rejeté',
                    'appealing': '⚖️ Contestation en cours',
                    'paid': '💰 Payé',
                    'closed': '📁 Clôturé',
                }
                s = status_labels.get(c.get('status', ''), c.get('status', 'Inconnu'))
                yield f"**Référence :** {claim_ref}\n"
                yield f"**Statut :** {s}\n"
                yield f"**Transporteur :** {c.get('carrier', 'N/A')}\n"
                yield f"**Type :** {c.get('dispute_type', 'N/A')}\n"
                yield f"**Montant demandé :** {c.get('amount_requested', 0):.2f} €\n"
                if c.get('tracking_number'):
                    yield f"**Numéro de suivi :** `{c['tracking_number']}`\n"
                if c.get('follow_up_level', 0) > 0:
                    yield f"**Relances envoyées :** {c['follow_up_level']}\n"
                if c.get('status') == 'rejected':
                    yield "\n💡 Ce dossier a été rejeté. Vous pouvez contester — dites-moi *\"génère une lettre de contestation pour {claim_ref}\"*."
                elif c.get('status') == 'pending':
                    yield "\n💡 Dossier en attente. Si pas de réponse sous 15 jours, dites *\"relance le transporteur pour {claim_ref}\"*."
            else:
                yield f"❌ {result['message']}"
            return

        # ── 10. ANNULER UN DOSSIER ────────────────────────────────────────────
        if any(kw in user_input_lower for kw in [
            'annuler', 'annulation', 'supprimer', 'clôturer', 'fermer',
            'abandonner', 'retirer', 'retrait'
        ]) and any(kw in user_input_lower for kw in ['dossier', 'réclamation', 'litige', 'claim']):
            if clm_match:
                claim_ref = clm_match.group(1)
                yield f"⚠️ **Demande d'annulation du dossier {claim_ref}**\n\n"
            else:
                yield "⚠️ **Annulation d'un dossier**\n\n"
            yield "Pour annuler un dossier, notre équipe doit intervenir manuellement (pour des raisons de traçabilité légale).\n\n"
            yield "**Procédure :**\n"
            yield "1. Envoyez un email à **support@recours-ecommerce.fr** avec l'objet : `ANNULATION DOSSIER [référence]`\n"
            yield "2. Indiquez la raison de l'annulation\n"
            yield "3. Nous clôturerons le dossier sous 48h ouvrées\n\n"
            yield "💡 *Si le transporteur a finalement accepté la réclamation, dites-moi plutôt \"marque comme payé\" avec le montant reçu.*"
            return

        # ── 11. DÉLAI DE REMBOURSEMENT / QUAND SERAI-JE PAYÉ ? ──────────────
        if any(kw in user_input_lower for kw in [
            'quand', 'combien de temps', 'délai', 'remboursé', 'paiement attendu',
            'serai payé', 'virement', 'délai moyen', 'combien temps'
        ]) and any(kw in user_input_lower for kw in [
            'remboursé', 'payé', 'paiement', 'virer', 'versement', 'reçu', 'délai'
        ]):
            logger.info("MANUAL TRIGGER: delay estimation")
            yield "⏱️ **Délais de traitement typiques :**\n\n"
            yield "| Transporteur | Délai moyen de réponse |\n|---|---|\n"
            yield "| 📦 Colissimo (La Poste) | 30 à 60 jours |\n"
            yield "| ⚡ Chronopost | 15 à 30 jours |\n"
            yield "| 🟤 UPS | 10 à 20 jours |\n"
            yield "| 🔴 DHL | 10 à 20 jours |\n"
            yield "| 🟢 GLS | 20 à 45 jours |\n"
            yield "| 🟡 Mondial Relay | 30 à 60 jours |\n\n"
            yield "Une fois le transporteur ayant accepté votre réclamation :\n"
            yield "- **Virement Refundly → votre compte** : sous 5 jours ouvrés\n\n"
            # Chercher les dossiers en attente depuis longtemps
            try:
                from src.database.database_manager import get_db_manager
                from datetime import datetime as _dt
                db = get_db_manager()
                client = db.get_client(email=client_email) if client_email else None
                if client:
                    claims = db.get_client_claims(client['id']) or []
                    overdue = []
                    for c in claims:
                        if c.get('status') in ('pending', 'submitted', 'under_review'):
                            created = c.get('submitted_at') or c.get('created_at', '')
                            try:
                                days = (_dt.now() - _dt.fromisoformat(str(created)[:19])).days
                                if days > 30:
                                    overdue.append((c.get('claim_reference', ''), c.get('carrier', ''), days))
                            except Exception:
                                pass
                    if overdue:
                        yield f"\n⚠️ **{len(overdue)} dossier(s) en attente depuis + de 30 jours** — pensez à relancer :\n"
                        for ref, carrier, days in overdue[:5]:
                            yield f"- **{ref}** ({carrier}) — {days} jours sans réponse\n"
                        yield "\nDites *\"relance le transporteur pour [référence]\"* pour chaque dossier bloqué."
            except Exception:
                pass
            return

        # ── 12. DOSSIERS BLOQUÉS / ANCIENS / SANS RÉPONSE ────────────────────
        if any(kw in user_input_lower for kw in [
            'bloqué', 'sans réponse', 'pas de réponse', 'rien depuis', 'ignoré',
            'ancien', 'vieux dossier', 'dossiers anciens', 'en retard', 'dépasse'
        ]):
            logger.info("MANUAL TRIGGER: overdue claims")
            yield "🔴 **Dossiers sans réponse (+ de 30 jours)**\n\n"
            try:
                from src.database.database_manager import get_db_manager
                from datetime import datetime as _dt
                db = get_db_manager()
                client = db.get_client(email=client_email) if client_email else None
                if not client:
                    yield "ℹ️ Impossible d'identifier le client."
                    return
                claims = db.get_client_claims(client['id']) or []
                overdue = []
                for c in claims:
                    if c.get('status') in ('pending', 'submitted', 'under_review'):
                        created = c.get('submitted_at') or c.get('created_at', '')
                        try:
                            days = (_dt.now() - _dt.fromisoformat(str(created)[:19])).days
                            if days > 30:
                                overdue.append((c.get('claim_reference', ''), c.get('carrier', ''), c.get('amount_requested', 0), days, c.get('follow_up_level', 0)))
                        except Exception:
                            pass
                if overdue:
                    overdue.sort(key=lambda x: -x[3])
                    yield f"**{len(overdue)} dossier(s) bloqué(s) :**\n\n"
                    yield "| Référence | Transporteur | Montant | Jours | Relances |\n|---|---|---|---|---|\n"
                    for ref, carrier, amt, days, lvl in overdue:
                        level_badge = "🟢 Aucune" if lvl == 0 else (f"🟡 {lvl}×" if lvl == 1 else f"🔴 {lvl}×")
                        yield f"| {ref} | {carrier} | {amt:.2f}€ | {days}j | {level_badge} |\n"
                    yield "\n💡 Dites *\"relance le transporteur pour [référence]\"* pour réactiver un dossier."
                else:
                    yield "✅ Aucun dossier bloqué ! Tous vos dossiers actifs ont moins de 30 jours."
            except Exception as e:
                yield f"❌ Erreur : {e}"
            return

        # Si pas de détection manuelle, envoyer à Gemini — prompt allégé


        full_prompt = f"{system_prompt}\n\nHistorique de conversation:\n"
        for msg in history[-5:]:  # Garde les 5 derniers échanges
            role = "Utilisateur" if msg["role"] == "user" else "Assistant"
            full_prompt += f"{role}: {msg['content']}\n"
            
        full_prompt += f"\nUtilisateur: {user_input}\nAssistant:"
        
        
        try:
            # Call Gemini with retry logic
            logger.info(f"Sending prompt to Gemini (user: {client_email or 'anonymous'})")
            
            # Instance propre à ce générateur pour garantir sa durée de vie sur toute l'itération
            api_key = Config.get_gemini_api_key()
            if not api_key:
                yield "Désolé, clé API manquante."
                return
            
            # Stocker en variable d'instance pour éviter le Garbage Collection de Python pendant le yield
            self.current_client = genai.Client(api_key=api_key)
            config = types.GenerateContentConfig(
                tools=self.gemini_tools if self.gemini_tools else None
            )
            
            # Utilisation de l'appel synchrone complet pour éviter les "client closed"
            # sur les yields asynchrones du nouveau SDK Google GenAI
            raw_response = self.current_client.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
                config=config
            )
            
            # Gérer les function calls
            if hasattr(raw_response, 'candidates') and raw_response.candidates:
                candidate = raw_response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    for part in candidate.content.parts:
                        if hasattr(part, 'function_call') and part.function_call.name:
                            fc = part.function_call
                            yield f"🔧 Exécution de l'action : {fc.name}...\n\n"
                            params = dict(fc.args)
                            if 'client_email' in params and params['client_email'] == 'CURRENT_USER':
                                params['client_email'] = client_email
                            result = self.tools.execute_tool(fc.name, params)
                            if result['success']:
                                yield f"✅ {result['message']}\n\n"
                                if 'data' in result and result['data']:
                                    yield f"📋 Détails :\n"
                                    if isinstance(result['data'], dict):
                                        for key, value in result['data'].items():
                                            yield f"- {key}: {value}\n"
                                    else:
                                        yield f"{result['data']}\n"
                            else:
                                yield f"❌ Erreur : {result['message']}\n"
                            logger.info(f"Function call executed: {fc.name} - Success: {result['success']}")
                            return  # Stop après un function call
                        
                        elif hasattr(part, 'text') and part.text:
                            # Simuler un streaming pour l'UI
                            words = part.text.split(' ')
                            for i, word in enumerate(words):
                                yield word + (' ' if i < len(words) - 1 else '')
                                
            elif hasattr(raw_response, 'text') and raw_response.text:
                # Simuler un streaming pour l'UI
                words = raw_response.text.split(' ')
                for i, word in enumerate(words):
                    yield word + (' ' if i < len(words) - 1 else '')
                    
        except Exception as e:
            error_str = str(e)
            error_msg = f"Erreur lors de l'appel à Gemini: {error_str}"
            logger.error(error_msg, exc_info=True)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
                yield "⚠️ **Système IA temporairement surchargé.** Le quota gratuit de l'assistant (Gemini Free Tier) est limité. Veuillez patienter environ une minute avant de redemander."
            else:
                yield f"Désolé, j'ai rencontré une erreur technique: {error_str}"
    

