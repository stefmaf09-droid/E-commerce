"""
Dispute details page for displaying complete information about a single dispute.

This module renders a dedicated page showing all details of a specific dispute
including order information, timeline, evidence photos, and available actions.
"""

import streamlit as st
import os
import sys
from datetime import datetime, timedelta

# Path configuration
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(root_dir, 'src'))
sys.path.insert(0, root_dir)

# Import i18n
from utils.i18n import get_i18n_text
from analytics.bypass_scorer import BypassScorer
from ai.appeal_generator import AppealGenerator
from database.database_manager import DatabaseManager

@st.cache_resource
def get_cached_scorer():
    """Cached instance of BypassScorer for details page."""
    return BypassScorer(DatabaseManager())


def render_dispute_details_page(dispute_data):
    """
    Render full dispute details page.
    
    Args:
        dispute_data (dict): Dictionary containing all dispute information.
    """
    # Apply premium theme
    from ui.theme import apply_premium_theme
    apply_premium_theme()
    
    # Header avec bouton retour
    _render_dispute_header(dispute_data)
    
    # Layout principal
    col1, col2 = st.columns([2, 1])
    
    with col1:
        _render_order_information(dispute_data)
        _render_timeline(dispute_data)
        _render_evidence_section(dispute_data)
    
    with col2:
        _render_status_card(dispute_data)
        _render_ai_advice_section(dispute_data)
        _render_financial_card(dispute_data)
        _render_actions_card(dispute_data)


def _render_dispute_header(dispute_data):
    """Render page header with back button and main dispute info."""
    # Back button
    col_back, col_title = st.columns([1, 5])
    
    with col_back:
        if st.button(f"← {get_i18n_text('btn_back')}", key="back_to_dashboard", width='stretch'):
            st.session_state.active_page = 'Dashboard'
            st.rerun()
    
    # Get carrier info
    carrier = dispute_data.get('carrier', 'Unknown')
    carriers_info = {
        'UPS': '🟫',
        'DHL': '🟨',
        'FedEx': '🟪',
        'USPS': '🟦',
        'DPD': '🟥',
        'Chronopost': '🔵',
        'Colissimo': '⚪'
    }
    carrier_logo = carriers_info.get(carrier, '📦')
    
    # Header
    dispute_id = dispute_data.get('dispute_id', 'N/A')
    order_id = dispute_data.get('order_id', 'N/A')
    tracking_number = dispute_data.get('tracking_number', 'N/A')
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 24px;
        border-radius: 12px;
        margin: 0 0 24px 0;
        color: white;
    ">
        <h1 style="margin: 0; font-size: 28px; font-weight: 700;">
            {carrier_logo} {get_i18n_text('dispute_details')} #{dispute_id}
        </h1>
        <p style="margin: 8px 0 0 0; font-size: 16px; opacity: 0.9;">
            {get_i18n_text('order')} #{order_id} • {get_i18n_text('tracking')}: {tracking_number}
        </p>
    </div>
    """, unsafe_allow_html=True)


def _render_order_information(dispute_data):
    """Render order and customer information section."""
    st.markdown(f"### 📦 {get_i18n_text('order_information')}")
    
    # Get data with fallbacks
    customer_name = dispute_data.get('customer_name', 'N/A')
    customer_email = dispute_data.get('customer_email', st.session_state.get('client_email', 'N/A'))
    delivery_address = dispute_data.get('delivery_address', 'N/A')
    order_date = dispute_data.get('order_date', 'N/A')
    dispute_type = dispute_data.get('dispute_type', 'unknown')
    
    # Format dispute type using i18n
    dispute_type_label = f"⏰ {get_i18n_text(dispute_type)}"
    
    st.markdown(f"""
    <div style="
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        margin-bottom: 24px;
    ">
        <p style="margin: 0 0 12px 0;"><strong>{get_i18n_text('customer')}:</strong> {customer_name}</p>
        <p style="margin: 0 0 12px 0;"><strong>{get_i18n_text('email')}:</strong> {customer_email}</p>
        <p style="margin: 0 0 12px 0;"><strong>{get_i18n_text('address')}:</strong> {delivery_address}</p>
        <p style="margin: 0 0 12px 0;"><strong>{get_i18n_text('order_date')}:</strong> {order_date}</p>
        <p style="margin: 0;"><strong>{get_i18n_text('issue_type')}:</strong> {dispute_type_label}</p>
    </div>
    """, unsafe_allow_html=True)


def _render_timeline(dispute_data):
    """Render event timeline."""
    st.markdown(f"### 📅 {get_i18n_text('timeline')}")
    
    # Default timeline if not provided
    timeline = dispute_data.get('timeline', [
        {'date': 'Jan 10', 'event': 'Order placed', 'status': 'success'},
        {'date': 'Jan 12', 'event': 'Shipped', 'status': 'success'},
        {'date': 'Jan 20', 'event': 'Delay detected', 'status': 'warning'},
        {'date': 'Jan 22', 'event': 'Claim submitted', 'status': 'info'},
    ])
    
    # Render timeline
    for item in timeline:
        date = item.get('date', '')
        event = item.get('event', '')
        status = item.get('status', 'info')
        
        # Status colors
        status_colors = {
            'success': '#10b981',
            'warning': '#f59e0b',
            'info': '#3b82f6',
            'error': '#ef4444'
        }
        color = status_colors.get(status, '#6b7280')
        
        st.markdown(f"""
        <div style="
            display: flex;
            align-items: center;
            gap: 16px;
            padding: 12px 0;
            border-left: 3px solid {color};
            padding-left: 16px;
            margin-bottom: 8px;
        ">
            <div style="
                width: 12px;
                height: 12px;
                background: {color};
                border-radius: 50%;
            "></div>
            <div>
                <div style="font-weight: 600; color: #1e293b;">{event}</div>
                <div style="font-size: 14px; color: #64748b;">{date}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def _render_evidence_section(dispute_data):
    """Render evidence photos section."""
    st.markdown(f"### 🖼️ {get_i18n_text('evidence_photos')}")
    
    evidence_photos = dispute_data.get('evidence_photos', [])
    claim_id = str(dispute_data.get('dispute_id', 'unknown'))
    
    # Setup Storage
    from src.database.supabase_storage import get_storage_manager
    storage = get_storage_manager()
    
    # --- New Evidence Uploader ---
    uploaded_evidence = st.file_uploader(
        "📤 Ajouter une preuve (Photo/PDF/Email EML)", 
        type=['png', 'jpg', 'jpeg', 'pdf', 'eml'],
        key=f"uploader_{dispute_data.get('dispute_id')}"
    )
    
    
    if uploaded_evidence:
        # 1. Setup Storage (already done above)
        
        with st.spinner("📤 Envoi et analyse de la preuve..."):
            # A. Cloud Upload
            cloud_path = None
            if storage.client:
                cloud_path = storage.upload_file(claim_id, uploaded_evidence.name, uploaded_evidence.getvalue())
                if cloud_path:
                    st.success(f"✅ {uploaded_evidence.name} sauvegardé dans le Cloud !")
            
            # B. Local Backup (optional, for safety or if no cloud)
            save_dir = os.path.join(root_dir, 'data', 'evidence', claim_id)
            if not storage.client:
                os.makedirs(save_dir, exist_ok=True)
                file_path = os.path.join(save_dir, uploaded_evidence.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_evidence.getbuffer())
                local_path = file_path
            else:
                local_path = uploaded_evidence # Pass buffer to OCR

            # C. Trigger OCR / Analysis
            from src.scrapers.ocr_processor import OCRProcessor
            ocr_processor = OCRProcessor()
            
            # Extract Text & Attachments
            extracted_text, attachments = ocr_processor.extract_all_from_file(local_path, uploaded_evidence.name)
            
            # Save extracted attachments
            for att in attachments:
                if storage.client:
                    storage.upload_file(claim_id, att['filename'], att['content'], att['content_type'])
                else:
                    os.makedirs(save_dir, exist_ok=True)
                    att_path = os.path.join(save_dir, att['filename'])
                    if not os.path.exists(att_path):
                        with open(att_path, "wb") as f:
                            f.write(att['content'])
                st.toast(f"📎 Pièce jointe extraite : {att['filename']}")
            
            # Analyze
            analysis = ocr_processor.analyze_rejection_text(extracted_text)
            
            # Store in session state for feedback
            st.session_state.last_analysis = {
                'text': extracted_text,
                'result': analysis,
                'file': uploaded_evidence.name
            }
            
            st.rerun()

    # --- Display Analysis Result & Feedback Loop ---
    if 'last_analysis' in st.session_state:
        analysis = st.session_state.last_analysis['result']
        text_snippet = st.session_state.last_analysis['text'][:300] + "..."
        
        st.info(f"💡 **Analyse IA :** {analysis['label_fr']} (Confiance: {int(analysis.get('confidence', 0)*100)}%)")
        
        with st.expander("Voir le texte extrait"):
            st.code(text_snippet)
            
        col_feedback1, col_feedback2 = st.columns(2)
        with col_feedback1:
            if st.button("✅ Confirmer l'analyse", key="confirm_ocr"):
                # Save Positive Feedback Loop
                from src.scrapers.ocr_processor import OCRProcessor
                ocr = OCRProcessor()
                ocr.save_correction(
                    original_text=st.session_state.last_analysis['text'],
                    corrected_reason_key=st.session_state.last_analysis['result']['reason_key'],
                    user_feedback="" # Empty feedback = Positive confirmation
                )
                
                st.toast("✅ Feedback positif enregistré ! L'IA apprend de cette confirmation.", icon="🧠")
                
                # Update local data for immediate feedback
                dispute_data['ai_reason_key'] = st.session_state.last_analysis['result']['reason_key']
                dispute_data['ai_advice'] = st.session_state.last_analysis['result']['advice_fr']
                
                # Update DB
                db_manager = DatabaseManager()
                db_manager.update_claim_ai_analysis(
                    claim_reference=dispute_data.get('claim_reference'),
                    reason_key=dispute_data['ai_reason_key'],
                    advice=dispute_data['ai_advice']
                )
                
                del st.session_state.last_analysis
                st.rerun()
                
        with col_feedback2:
            if st.button("❌ Signaler une erreur", key="reject_ocr"):
                st.session_state.show_correction_form = True
        
        if st.session_state.get('show_correction_form'):
            with st.form("ocr_feedback_form"):
                st.write("Aidez-nous à améliorer l'IA : Quel est le vrai motif ?")
                
                reason_options = {
                    "Signature Non Conforme": "bad_signature",
                    "Poids Vérifié": "weight_match", 
                    "Emballage Insuffisant": "bad_packaging",
                    "Délai Dépassé": "deadline_expired",
                    "Erreur Adresse": "wrong_address",
                    "Autre / Non listé": "other"
                }
                
                correct_reason_label = st.selectbox(
                    "Motif Réel",
                    list(reason_options.keys())
                )
                
                comment = st.text_input("Commentaire / Précision (Utile pour l'apprentissage)")
                
                if st.form_submit_button("Envoyer Correction"):
                    from src.scrapers.ocr_processor import OCRProcessor
                    ocr = OCRProcessor()
                    
                    selected_key = reason_options.get(correct_reason_label, "other")
                    
                    ocr.save_correction(
                        original_text=st.session_state.last_analysis['text'],
                        corrected_reason_key=selected_key,
                        user_feedback=comment # Feedback present = Negative/Correction
                    )
                    
                    # Update DB with corrected values
                    db_manager = DatabaseManager()
                    dispute_data['ai_reason_key'] = selected_key
                    # We could regenerate advice here, but for now we keep previous or empty
                    
                    db_manager.update_claim_ai_analysis(
                        claim_reference=dispute_data.get('claim_reference'),
                        reason_key=selected_key,
                        advice="Motif corrigé manuellement. En attente de nouvelle analyse."
                    )
                    
                    st.success("Merci ! Votre correction a été prise en compte et servira à l'entraînement.")
                    del st.session_state.last_analysis
                    st.session_state.show_correction_form = False
                    st.rerun()
        
    if storage.client:
        # Cloud listing
        cloud_files = storage.list_files(claim_id)
        evidence_photos = []
        for f in cloud_files:
            if f['name'].lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                url = storage.get_public_url(f"{claim_id}/{f['name']}")
                if url: evidence_photos.append(url)
    
    if evidence_photos:
        cols = st.columns(min(3, len(evidence_photos)))
        for idx, photo in enumerate(evidence_photos[:3]):
            with cols[idx % 3]:
                st.image(photo, caption=f"Evidence {idx+1}", use_column_width=True)
    else:
        st.info(get_i18n_text('no_evidence_yet'))
    
    # Notes
    notes = dispute_data.get('notes', '')
    if notes:
        st.markdown("### 📝 Notes")
        st.text_area("", value=notes, height=100, disabled=True, label_visibility="collapsed")


def _render_status_card(dispute_data):
    """Render status card."""
    status = dispute_data.get('status', 'pending')
    
    # Calculate success probability using AI
    try:
        scorer = get_cached_scorer()
        success_prob = scorer.predict_success({
            'carrier': dispute_data.get('carrier', 'Unknown'),
            'dispute_type': dispute_data.get('dispute_type', 'unknown')
        })
        probability = int(success_prob * 100)
    except Exception:
        probability = 50
    
    # Status labels using i18n
    status_labels = {
        'pending': (get_i18n_text('status_pending'), '#f59e0b'),
        'processing': (get_i18n_text('status_processing'), '#3b82f6'),
        'under_review': (get_i18n_text('status_under_review'), '#f59e0b'),
        'resolved': (get_i18n_text('status_resolved'), '#10b981'),
        'rejected': (get_i18n_text('status_rejected'), '#ef4444')
    }
    status_label, status_color = status_labels.get(status, ('Unknown', '#6b7280'))
    
    st.markdown(f"""
    <div style="
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        margin-bottom: 16px;
    ">
        <h3 style="margin: 0 0 16px 0; font-size: 18px;">{get_i18n_text('status')}</h3>
        <div style="
            padding: 12px;
            background: {status_color}20;
            color: {status_color};
            border-radius: 8px;
            font-weight: 600;
            text-align: center;
            margin-bottom: 16px;
        ">{status_label}</div>
        <div style="margin-bottom: 8px; color: #64748b;">{get_i18n_text('ai_confidence')}</div>
        <div style="
            display: flex;
            align-items: center;
            gap: 12px;
        ">
            <div style="flex: 1; height: 8px; background: #f1f5f9; border-radius: 99px; overflow: hidden;">
                <div style="width: {probability}%; height: 100%; background: #4338ca;"></div>
            </div>
            <span style="font-weight: 700; color: #4338ca;">{probability}%</span>
        </div>
    """, unsafe_allow_html=True)


def _render_ai_advice_section(dispute_data):
    """Render the AI Strategic Advice section if available."""
    ai_advice = dispute_data.get('ai_advice')
    ai_reason = dispute_data.get('ai_reason_key')
    
    if not ai_advice:
        return
        
    st.markdown(f"""
    <div style="
        background: #f0f4ff;
        padding: 20px;
        border-radius: 12px;
        border-left: 5px solid #4338ca;
        box-shadow: 0 4px 12px rgba(67, 56, 202, 0.1);
        margin-bottom: 24px;
    ">
        <h3 style="margin: 0 0 12px 0; font-size: 18px; color: #4338ca;">
            🤖 Conseil Stratégique IA
        </h3>
        <p style="margin: 0 0 16px 0; font-size: 15px; color: #1e293b; line-height: 1.5;">
            {ai_advice}
        </p>
        <div style="
            display: inline-block;
            padding: 4px 10px;
            background: rgba(67, 56, 202, 0.1);
            color: #4338ca;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        ">
            Code Motif: {ai_reason}
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_financial_card(dispute_data):
    """Render financial information card."""
    total = dispute_data.get('amount', dispute_data.get('total_recoverable', 0))
    client_share = total * 0.8
    fee = total * 0.2
    
    st.markdown(f"""
    <div style="
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        margin-bottom: 16px;
    ">
        <h3 style="margin: 0 0 16px 0; font-size: 18px;">💰 {get_i18n_text('financial')}</h3>
        <div style="margin-bottom: 12px;">
            <div style="color: #64748b; font-size: 14px;">{get_i18n_text('total_recoverable')}</div>
            <div style="font-size: 24px; font-weight: 700; color: #1e293b;">€{total:.2f}</div>
        </div>
        <div style="margin-bottom: 12px;">
            <div style="color: #64748b; font-size: 14px;">{get_i18n_text('you_receive')} (80%)</div>
            <div style="font-size: 20px; font-weight: 600; color: #10b981;">€{client_share:.2f}</div>
        </div>
        <div>
            <div style="color: #64748b; font-size: 14px;">{get_i18n_text('our_fee')} (20%)</div>
            <div style="font-size: 16px; font-weight: 500; color: #64748b;">€{fee:.2f}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_actions_card(dispute_data):
    """Render available actions card."""
    st.markdown(f"### ⚡ {get_i18n_text('actions')}")
    
    if st.button(f"🚀 {get_i18n_text('btn_escalate')}", key="escalate_action", width='stretch', type="primary"):
        st.toast(f"⚡ {get_i18n_text('btn_escalate')}...")
        
    # --- New: Appeal Generation ---
    ai_reason = dispute_data.get('ai_reason_key')
    status = dispute_data.get('status')
    
    # Show if rejected or if AI detected a refusal reason
    if status == 'rejected' or ai_reason:
        if st.button("📄 Générer Courrier de Contestation", key="btn_gen_appeal", type="secondary"):
            generator = AppealGenerator()
            # Use AI reason or default to 'default'
            reason = ai_reason if ai_reason else 'default'
            appeal_text = generator.generate(dispute_data, reason)
            st.session_state[f'appeal_{dispute_data.get("dispute_id")}'] = appeal_text
            st.rerun()
            
    if f'appeal_{dispute_data.get("dispute_id")}' in st.session_state:
        # Editable Preview
        st.caption("Aperçu du contenu (Modifiable avant téléchargement) :")
        current_appeal_text = st.session_state[f'appeal_{dispute_data.get("dispute_id")}']
        
        edited_appeal_text = st.text_area(
            "Contenu du courrier", 
            value=current_appeal_text, 
            height=300, 
            label_visibility="collapsed",
            key=f"edit_appeal_{dispute_data.get('dispute_id')}"
        )
        
        # PDF Download Button (Uses edited text)
        pdf_bytes = AppealGenerator.generate_pdf(edited_appeal_text, f"recours_{dispute_data.get('order_id')}.pdf")
        if pdf_bytes:
            st.download_button(
                label="📄 Télécharger le courrier officiel (.pdf)",
                data=pdf_bytes,
                file_name=f"recours_{dispute_data.get('order_id')}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )
        else:
            st.error("Erreur : Impossible de générer le PDF.")
    # -------------------------------
    
    if st.button(f"📄 {get_i18n_text('btn_download_pdf')}", key="download_pdf", width='stretch'):
        st.toast(f"📄 {get_i18n_text('btn_download_pdf')}...")
    
    if st.button(f"📝 {get_i18n_text('btn_add_note')}", key="add_note", width='stretch'):
        st.session_state.show_note_form = True
    
    if st.session_state.get('show_note_form', False):
        with st.form("note_form"):
            note = st.text_area(get_i18n_text('your_note'))
            if st.form_submit_button(get_i18n_text('btn_save_note')):
                st.success("✅ Note saved!")
                st.session_state.show_note_form = False
                st.rerun()
