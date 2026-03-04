
import streamlit as st
import time
import re
from src.ai.chatbot_manager import ChatbotManager
from src.workers.reminder_worker import ReminderWorker


# ── Raccourcis actions ────────────────────────────────────────────────────────
QUICK_ACTIONS = [
    ("📋 Mes réclamations", "Montre-moi mes réclamations en attente"),
    ("📤 Exporter CSV",     "Exporter mes réclamations en CSV"),
    ("🔍 Suivre un colis",  "__tracking_prompt__"),   # traité spécialement
    ("🆕 Nouvelle récl.",   "Créer une réclamation"),
    ("⚖️ Contester",         "__contest_prompt__"),   # traité spécialement
]


def render_assistant_page():
    st.markdown("## 💬 Refundly Assistant")
    st.markdown(
        "Posez vos questions ou demandez au bot d'agir directement : "
        "relancer un transporteur, exporter vos données, créer un dossier…"
    )

    # ── Bannière d'état du ReminderWorker ───────────────────────────────
    try:
        worker = ReminderWorker.get_instance()
        stats = worker.stats
        last_run = stats.get("last_run")
        last_count = stats.get("last_run_count", 0)
        total = stats.get("total_reminders_sent", 0)

        if last_run:
            from datetime import datetime
            last_dt = datetime.fromisoformat(last_run)
            age_min = int((datetime.now() - last_dt).total_seconds() / 60)
            age_label = f"il y a {age_min} min" if age_min < 60 else f"il y a {age_min // 60}h"

            if last_count > 0:
                st.success(
                    f"🤖 **Relances automatiques** : {last_count} relance(s) envoyée(s) {age_label} — "
                    f"{total} au total depuis le démarrage."
                )
            else:
                st.info(
                    f"🤖 **Relances auto actives** — dernier scan {age_label}, aucun dossier éligible."
                )
        else:
            st.info("🤖 **Relances automatiques actives** — premier scan en cours…")
    except Exception:
        pass  # Ne pas bloquer l'interface si le worker n'est pas disponible

    # ── Init ──────────────────────────────────────────────────────────────────
    if "chatbot_manager" not in st.session_state:
        st.session_state.chatbot_manager = ChatbotManager()

    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({
            "role": "assistant",
            "content": (
                "Bonjour ! Je suis l'Assistant Refundly 🤖\n\n"
                "Je peux **agir à votre place** :\n"
                "- 📋 Lister / relancer vos réclamations\n"
                "- 🔍 Suivre un colis en temps réel\n"
                "- 📤 Exporter vos données en CSV\n"
                "- 💰 Enregistrer un paiement reçu\n"
                "- 🆕 Créer un nouveau dossier\n\n"
                "Que puis-je faire pour vous ?"
            )
        })

    # ── Boutons raccourcis ────────────────────────────────────────────────────
    cols = st.columns(len(QUICK_ACTIONS))
    for col, (label, action_text) in zip(cols, QUICK_ACTIONS):
        if col.button(label, use_container_width=True, key=f"qa_{label}"):
            if action_text == "__tracking_prompt__":
                st.session_state["_tracking_input_mode"] = True
            elif action_text == "__contest_prompt__":
                st.session_state["_contest_input_mode"] = True
            else:
                st.session_state["_quick_action"] = action_text

    # Mode saisie numéro de suivi (déclenché par le bouton 🔍)
    if st.session_state.get("_tracking_input_mode"):
        with st.form(key="tracking_form", clear_on_submit=True):
            tracking_num = st.text_input(
                "📦 Numéro de suivi",
                placeholder="Ex: XS419416933FR, 1Z999AA10123456784…",
            )
            submitted = st.form_submit_button("🔍 Rechercher")
            if submitted and tracking_num.strip():
                st.session_state["_quick_action"] = f"Suivi colis {tracking_num.strip()}"
                st.session_state.pop("_tracking_input_mode", None)
                st.rerun()

    # Mode saisie référence contestation (déclenché par le bouton ⚖️)
    if st.session_state.get("_contest_input_mode"):
        with st.form(key="contest_form", clear_on_submit=True):
            contest_ref = st.text_input(
                "⚖️ Référence du dossier à contester",
                placeholder="Ex: CLM-41625",
            )
            submitted_c = st.form_submit_button("⚖️ Générer la lettre")
            if submitted_c and contest_ref.strip():
                st.session_state["_quick_action"] = f"Contester le dossier {contest_ref.strip().upper()}"
                st.session_state.pop("_contest_input_mode", None)
                st.rerun()

    # ── Documents générés (persistants entre les reruns) ─────────────────────
    if st.session_state.get('_appeal_pdfs'):
        for idx, appeal in enumerate(st.session_state['_appeal_pdfs']):
            col_pdf, col_x = st.columns([5, 1])
            with col_pdf:
                st.download_button(
                    label=f"📄 Télécharger : {appeal['doc_type']} — {appeal['claim_ref']}",
                    data=appeal['bytes'],
                    file_name=appeal['filename'],
                    mime="application/pdf",
                    key=f"appeal_dl_persistent_{idx}",
                    type="primary",
                    use_container_width=True,
                )
            with col_x:
                if st.button("✕", key=f"dismiss_pdf_{idx}", help="Fermer"):
                    st.session_state['_appeal_pdfs'].pop(idx)
                    st.rerun()

    st.divider()

    # ── Zone d'upload de preuves ──────────────────────────────────────────────
    with st.expander("📎 Déposer une preuve de livraison (POD)", expanded=False):
        uploaded_file = st.file_uploader(
            "Glissez un fichier ici (PDF, PNG, JPG, JPEG)",
            type=["pdf", "png", "jpg", "jpeg"],
            key="pod_uploader",
        )
        claim_ref_upload = st.text_input(
            "Référence dossier (optionnel)",
            placeholder="CLM-xxxxx",
            key="pod_claim_ref",
        )
        if uploaded_file is not None:
            col_a, col_b = st.columns([3, 1])
            col_a.info(f"Fichier sélectionné : **{uploaded_file.name}** ({uploaded_file.size // 1024} Ko)")
            if col_b.button("✅ Envoyer", key="pod_send_btn"):
                import pathlib, mimetypes
                from datetime import datetime as _dt

                file_bytes = uploaded_file.read()

                # ── 1. Sauvegarde disque ──────────────────────────────
                save_dir = pathlib.Path("data/uploads/pod")
                save_dir.mkdir(parents=True, exist_ok=True)
                ts = _dt.now().strftime("%Y%m%d_%H%M%S")
                safe_name = f"{ts}_{uploaded_file.name.replace(' ', '_')}"
                save_path = save_dir / safe_name
                save_path.write_bytes(file_bytes)

                # ── 2. Enregistrement en base (email_attachments) ─────
                attachment_id = None
                client_email = st.session_state.get("client_email", "")
                claim_ref = claim_ref_upload.strip().upper() or None
                mime_type = mimetypes.guess_type(uploaded_file.name)[0] or "application/octet-stream"
                try:
                    from src.database.database_manager import get_db_manager
                    db = get_db_manager()
                    attachment_id = db.create_email_attachment(
                        client_email=client_email,
                        claim_reference=claim_ref,
                        attachment_filename=uploaded_file.name,
                        attachment_path=str(save_path),
                        file_size=len(file_bytes),
                        mime_type=mime_type,
                        email_subject="POD manuel via assistant",
                        email_from=client_email,
                        email_received_at=_dt.now().isoformat(),
                    )
                    if claim_ref and attachment_id:
                        db.link_attachment_to_claim(attachment_id, claim_ref)
                except Exception as db_err:
                    st.warning(f"⚠️ Enregistrement DB partiel : {db_err}")

                # ── 3. OCR + analyse IA ───────────────────────────────
                ocr_status = ""
                detected_reason = None
                try:
                    from src.scrapers.ocr_processor import OCRProcessor
                    ocr = OCRProcessor()
                    extracted = ocr.extract_all_from_file(file_bytes, uploaded_file.name)
                    raw_text = extracted.get("text", "") if isinstance(extracted, dict) else str(extracted)
                    if raw_text and len(raw_text) > 20:
                        analysis = ocr.analyze_rejection_text(raw_text)
                        reason_key = analysis.get("reason_key", "")
                        advice = analysis.get("advice", "")
                        confidence = analysis.get("confidence", 0)
                        if claim_ref and reason_key:
                            try:
                                db.update_claim_ai_analysis(claim_ref, reason_key, advice)
                            except Exception:
                                pass
                        if reason_key:
                            detected_reason = reason_key
                            ocr_status = (
                                f"\n\n🔍 **Analyse OCR** : motif détecté **{reason_key}** "
                                f"(confiance {int(confidence * 100)}%)\n> {advice}"
                            )
                        else:
                            ocr_status = "\n\n🔍 **OCR** : texte extrait, motif non identifié."
                    else:
                        ocr_status = "\n\n🔍 **OCR** : aucun texte exploitable extrait."
                except Exception as ocr_err:
                    ocr_status = f"\n\n🔍 **OCR** : analyse non disponible ({ocr_err})."

                # ── 4. Message de confirmation ────────────────────────
                ref_label = f" pour **{claim_ref}**" if claim_ref else ""
                db_label = f" (ID #{attachment_id})" if attachment_id else ""
                notice = (
                    f"📎 Preuve déposée{ref_label} : `{uploaded_file.name}`{db_label}.  \n"
                    f"✅ Enregistré en base et lié au dossier."
                    f"{ocr_status}"
                )
                st.session_state.messages.append({"role": "assistant", "content": notice})
                
                # Enchaînement automatique
                if detected_reason:
                    if claim_ref:
                        # On a la ref : on demande à l'IA de générer le document
                        st.session_state["_quick_action"] = f"Génère la lettre de contestation PDF pour le litige {claim_ref} en utilisant le motif '{detected_reason}' détecté sur la preuve."
                    else:
                        # Pas de ref : message texte direct + boutons d'action (économie de quota)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": f"💡 J'ai identifié le motif **{detected_reason}** sur votre preuve. Pour quelle réclamation (numéro commençant par `CLM-`) souhaitez-vous générer une lettre de contestation ?",
                            "proactive_options": [
                                {
                                    "label": "📄 Générer une lettre (J'ai la Réf)", 
                                    "action": f"Génère la lettre de contestation PDF pour le litige CLM-XXXX en utilisant le motif '{detected_reason}'"
                                },
                                {
                                    "label": "📁 Créer un nouveau dossier",
                                    "action": f"Je souhaite créer un nouveau dossier avec le motif: {detected_reason}"
                                }
                            ]
                        })
                
                st.success("✅ Preuve enregistrée et analysée !")
                st.rerun()


    # ── Historique ────────────────────────────────────────────────────────────
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Affichage des boutons d'actions proactives (seulement pour le dernier message)
            if i == len(st.session_state.messages) - 1 and "proactive_options" in message:
                cols = st.columns(len(message["proactive_options"]))
                for col_idx, opt in enumerate(message["proactive_options"]):
                    if cols[col_idx].button(opt["label"], key=f"proact_{i}_{col_idx}"):
                        st.session_state["_quick_action"] = opt["action"]
                        st.rerun()

    # ── Input : saisie manuelle ou raccourci ──────────────────────────────────
    prompt = st.chat_input("Votre question ou action…")

    # Injecter le raccourci cliqué comme prompt
    if not prompt and "_quick_action" in st.session_state:
        prompt = st.session_state.pop("_quick_action")

    if not prompt:
        return

    # ── Validation ────────────────────────────────────────────────────────────
    prompt = prompt.strip()
    MAX_PROMPT_LENGTH = 600
    if len(prompt) > MAX_PROMPT_LENGTH:
        st.error(f"⚠️ Question trop longue (maximum {MAX_PROMPT_LENGTH} caractères)")
        return
    if len(prompt) < 3:
        st.warning("⚠️ Veuillez poser une question plus détaillée")
        return

    dangerous_patterns = ["ignore previous", "system:", "admin_override", "\n\n\n"]
    if any(p in prompt.lower() for p in dangerous_patterns):
        st.warning("⚠️ Cette question contient des éléments suspects.")
        return

    # ── Rate limiting ─────────────────────────────────────────────────────────
    COOLDOWN_SECONDS = 2.0
    if 'last_request_time' in st.session_state:
        elapsed = time.time() - st.session_state.last_request_time
        if elapsed < COOLDOWN_SECONDS:
            st.warning(f"⏳ Veuillez patienter {COOLDOWN_SECONDS - elapsed:.1f}s.")
            return
    st.session_state.last_request_time = time.time()

    # ── Interception Proactive (Bypass IA) ───────────────────────────────────
    if prompt.startswith("Génère la lettre de contestation PDF pour le litige CLM-XXXX"):
        detected_reason = prompt.split("motif '")[1].split("'")[0] if "motif '" in prompt else "inconnu"
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        reply = f"📝 **J'ai bien noté le motif '{detected_reason}'.**\n\n👉 **Veuillez taper uniquement votre numéro de réclamation** (ex: `CLM-12345`) dans la barre de discussion pour que je puisse générer la lettre."
        st.session_state.messages.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.markdown(reply)
            
        st.session_state["_pending_action"] = {"type": "generate_letter", "reason": detected_reason}
        return

    if prompt.startswith("Je souhaite créer un nouveau dossier avec le motif:"):
        detected_reason = prompt.split("motif: ")[1] if "motif: " in prompt else "inconnu"
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        reply = f"✅ **Nouveau dossier (Motif: {detected_reason})**\n\n👉 Veuillez vous rendre dans l'onglet **Créer un Dossier** depuis le menu de gauche pour renseigner les détails."
        st.session_state.messages.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.markdown(reply)
        return

    # Suite d'une action mise en attente (ex: attente du numéro CLM)
    if "_pending_action" in st.session_state and st.session_state["_pending_action"]["type"] == "generate_letter":
        clm_match = re.search(r'CLM-[\w-]+', prompt.upper())
        if clm_match:
            claim_ref = clm_match.group(0)
            reason = st.session_state["_pending_action"]["reason"]
            
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
                
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                message_placeholder.markdown(f"🔧 Exécution de l'action : Génération du PDF pour **{claim_ref}**...\n\n")
                client_email = st.session_state.get('client_email', None)
                
                try:
                    from src.database.database_manager import get_db_manager
                    from src.ai.appeal_generator import AppealGenerator
                    import base64
                    
                    db = get_db_manager()
                    claim = db.get_claim(claim_ref)
                    
                    if not claim:
                        reply = f"❌ Erreur : La réclamation **{claim_ref}** n'existe pas."
                    else:
                        dispute_data = {
                            'claim_reference': claim_ref,
                            'tracking_number': claim.get('tracking_number', 'N/A'),
                            'carrier': claim.get('carrier', 'le transporteur'),
                            'amount_requested': claim.get('amount_requested', 0),
                            'order_date': str(claim.get('order_date', 'N/A')),
                            'client_name': client_email or 'Client',
                            'client_email': client_email or '',
                            'recipient_name': claim.get('customer_name', 'le destinataire'),
                            'status': claim.get('status', '')
                        }
                        
                        # Utilisation de l'IA (AppealGenerator) pour rédiger la lettre
                        gen = AppealGenerator()
                        letter_text = gen.generate(dispute_data, reason)
                        
                        # Génération du PDF
                        pdf_bytes = AppealGenerator.generate_pdf(letter_text, f"contestation_{claim_ref}.pdf")
                        
                        if pdf_bytes:
                            pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
                            st.session_state['_appeal_pdf'] = {
                                "ref": claim_ref,
                                "b64": pdf_base64
                            }
                            reply = f"✅ Lettre de contestation générée avec succès pour **{claim_ref}**.\n\n"
                        else:
                            reply = f"❌ Erreur lors de l'assemblage du PDF.\n"
                except Exception as e:
                    reply = f"❌ Erreur technique lors de la génération : {e}"
                    
                message_placeholder.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
                
            del st.session_state["_pending_action"]
            st.rerun()
            return
        else:
            # L'utilisateur n'a pas tapé un CLM valide, on l'avertit
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
                
            warning_reply = "⚠️ Je n'ai pas reconnu de numéro de réclamation valide. Veuillez saisir un numéro commençant par `CLM-` (ex: `CLM-41625`)."
            st.session_state.messages.append({"role": "assistant", "content": warning_reply})
            with st.chat_message("assistant"):
                st.markdown(warning_reply)
            return

    # ── Confirmation pour actions sensibles ──────────────────────────────────
    is_sensitive = any(kw in prompt.lower() for kw in ['relancer', 'relance', 'payé', 'paiement', 'mark', 'marquer'])
    has_clm_ref  = bool(re.search(r'CLM-[\w-]+', prompt.upper()))

    if is_sensitive and has_clm_ref:
        confirm_key = f"confirm_{len(st.session_state.messages)}"
        if not st.session_state.get(confirm_key):
            clm_ref = re.search(r'CLM-[\w-]+', prompt.upper()).group(0)
            action_label = "envoyer une relance" if "relance" in prompt.lower() else "enregistrer ce paiement"
            st.warning(f"⚠️ Vous êtes sur le point de **{action_label}** pour **{clm_ref}**.")
            col1, col2 = st.columns(2)
            if col1.button("✅ Confirmer", key=f"ok_{confirm_key}"):
                st.session_state[confirm_key] = True
                st.rerun()
            col2.button("❌ Annuler", key=f"cancel_{confirm_key}")
            return

    # ── Envoyer le message ────────────────────────────────────────────────────
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    client_email = st.session_state.get('client_email', None)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        csv_data = None

        try:
            response_stream = st.session_state.chatbot_manager.generate_response_stream(
                prompt,
                st.session_state.messages[:-1],
                client_email=client_email
            )

            try:
                for chunk in response_stream:
                    full_response += chunk
                    message_placeholder.markdown(full_response + "▌")
                    time.sleep(0.008)

                    # Détecter CSV dans la réponse
                    csv_match = re.search(r'```csv\n(.*?)\n```', full_response, re.DOTALL)
                    if csv_match:
                        csv_data = csv_match.group(1)
                        st.session_state['csv_export_data'] = csv_data

            except Exception as stream_err:
                if "404" in str(stream_err) and "gemini" in str(stream_err).lower():
                    st.warning("⚠️ Session expirée. Ré-initialisation de l'assistant…")
                    st.session_state.chatbot_manager = ChatbotManager()
                    st.info("🔄 Assistant mis à jour. Renvoyez votre question.")
                    return
                raise stream_err

            message_placeholder.markdown(full_response)

        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
                error_msg = "⚠️ **Système IA temporairement surchargé.** Le quota gratuit de l'assistant (Gemini Free Tier) est limité. Veuillez patienter environ une minute avant de redemander."
            else:
                error_msg = f"❌ Erreur technique : {error_str}"
            message_placeholder.error(error_msg)
            full_response = error_msg

    st.session_state.messages.append({"role": "assistant", "content": full_response})

    # ── Bouton téléchargement CSV ────────────────────────────────────────────
    if st.session_state.get('csv_export_data'):
        from datetime import datetime
        st.download_button(
            label="📥 Télécharger le CSV",
            data=st.session_state.csv_export_data,
            file_name=f"reclamations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            key=f"csv_dl_{len(st.session_state.messages)}"
        )
        st.session_state.pop('csv_export_data', None)

    # ── Bouton téléchargement PDF (persistant entre les reruns) ────────────
    # Le PDF est accumulé dans _appeal_pdfs (liste) — jamais effacé au rerun
    if st.session_state.get('_appeal_pdf'):
        appeal = st.session_state.pop('_appeal_pdf')
        if '_appeal_pdfs' not in st.session_state:
            st.session_state['_appeal_pdfs'] = []
        st.session_state['_appeal_pdfs'].append(appeal)
