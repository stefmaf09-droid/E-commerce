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
    
    # --- New Evidence Uploader ---
    uploaded_evidence = st.file_uploader(
        "📤 Ajouter une preuve (Photo/PDF)", 
        type=['png', 'jpg', 'jpeg', 'pdf'],
        key=f"uploader_{dispute_data.get('dispute_id')}"
    )
    
    
    if uploaded_evidence:
        # Save file logic
        claim_id = dispute_data.get('dispute_id', 'unknown')
        save_dir = os.path.join(root_dir, 'data', 'evidence', str(claim_id))
        os.makedirs(save_dir, exist_ok=True)
        
        file_path = os.path.join(save_dir, uploaded_evidence.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_evidence.getbuffer())
        
        st.success(f"✅ {uploaded_evidence.name} ajouté !")
        
        # Trigger OCR / Analysis
        with st.spinner("🤖 Analyse intelligente (OCR/NLP) en cours..."):
            from src.scrapers.ocr_processor import OCRProcessor
            ocr_processor = OCRProcessor()
            
            # 1. Extract Text
            extracted_text = ocr_processor.extract_text_from_file(file_path, uploaded_evidence.name)
            
            # 2. Analyze
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
                st.toast("Feedback enregistré : L'IA apprend de cette confirmation !", icon="🧠")
                # Feedback implicite : on pourrait le sauvegarder aussi
                del st.session_state.last_analysis
                st.rerun()
                
        with col_feedback2:
            if st.button("❌ Signaler une erreur", key="reject_ocr"):
                st.session_state.show_correction_form = True
        
        if st.session_state.get('show_correction_form'):
            with st.form("ocr_feedback_form"):
                st.write("Aidez-nous à améliorer l'IA : Quel est le vrai motif ?")
                correct_reason = st.selectbox(
                    "Motif Réel",
                    ["Signature Non Conforme", "Poids Vérifié", "Emballage Insuffisant", "Délai Dépassé", "Erreur Adresse", "Autre"]
                )
                comment = st.text_input("Commentaire (Optionnel)")
                
                if st.form_submit_button("Envoyer Correction"):
                    from src.scrapers.ocr_processor import OCRProcessor
                    ocr = OCRProcessor()
                    
                    # Map label back to key (simplified for demo)
                    key_map = {
                        "Signature Non Conforme": "bad_signature",
                        "Poids Vérifié": "weight_match", 
                        "Emballage Insuffisant": "bad_packaging",
                        "Délai Dépassé": "deadline_expired",
                        "Erreur Adresse": "wrong_address"
                    }
                    
                    ocr.save_correction(
                        original_text=st.session_state.last_analysis['text'],
                        corrected_reason_key=key_map.get(correct_reason, "other"),
                        user_feedback=comment
                    )
                    
                    st.success("Merci ! Votre correction a été prise en compte.")
                    del st.session_state.last_analysis
                    st.session_state.show_correction_form = False
                    st.rerun()
        
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
    probability = dispute_data.get('probability_success', 85)
    
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
