import streamlit as st
import os
from datetime import datetime
from src.email.attachment_manager import AttachmentManager
from src.database.database_manager import get_db_manager

def render_attachments_page():
    st.title("📎 Gestion des Pièces Jointes")
    st.markdown("Consultez et gérez les documents extraits automatiquement de vos emails transporteurs.")
    
    # Initialize Manager
    manager = AttachmentManager()
    db = get_db_manager()
    client_email = st.session_state.get('client_email', 'demo@refundly.ai')
    
    # Header Actions
    col1, col2 = st.columns([6, 2])
    with col2:
        if st.button("🔄 Synchroniser Emails", use_container_width=True):
            with st.spinner("Recherche de nouvelles pièces jointes..."):
                result = manager.sync_emails(client_email)
                if result['success']:
                    st.success(result['message'])
                else:
                    st.error(result['message'])
    
    # Load Attachments
    attachments = manager.get_attachments(client_email)
    
    if not attachments:
        st.info("Aucune pièce jointe trouvée. Cliquez sur 'Synchroniser Emails' pour en chercher.")
        return

    # Tabs for organization
    tab1, tab2 = st.tabs(["📋 Par Réclamation", "📂 Toutes les pièces"])
    
    with tab1:
        # Group by claim_reference
        grouped = {}
        orphans = []
        for att in attachments:
            ref = att.get('claim_reference')
            if ref:
                if ref not in grouped: grouped[ref] = []
                grouped[ref].append(att)
            else:
                orphans.append(att)
        
        for ref, files in grouped.items():
            with st.expander(f"Réclamation : {ref} ({len(files)} fichiers)"):
                for f in files:
                    display_attachment_row(f, manager)
        
        if orphans:
            st.markdown("---")
            st.subheader("❓ Non assignées")
            for f in orphans:
                display_attachment_row(f, manager, show_assign=True)

    with tab2:
        st.dataframe(attachments, use_container_width=True)

def display_attachment_row(f, manager, show_assign=False):
    cols = st.columns([4, 2, 2, 2])
    with cols[0]:
        st.markdown(f"**{f['attachment_filename']}**")
        st.caption(f"De: {f['email_from']} | Objet: {f['email_subject']}")
    
    with cols[1]:
        size_kb = round(f['file_size'] / 1024, 1)
        st.text(f"{size_kb} KB")
        st.caption(f"{f['mime_type']}")
        
    with cols[2]:
        if st.button("👁️ Aperçu", key=f"view_{f['id']}"):
            st.toast("Aperçu non disponible en démo local")
            
    with cols[3]:
        # Simple file download simulator
        if os.path.exists(f['attachment_path']):
            with open(f['attachment_path'], "rb") as file:
                st.download_button(
                    label="⬇️ Télécharger",
                    data=file,
                    file_name=f['attachment_filename'],
                    mime=f['mime_type'],
                    key=f"dl_{f['id']}"
                )
        else:
            st.error("Fichier introuvable")

    if show_assign:
        with st.container():
            col_a, col_b = st.columns([3, 1])
            with col_a:
                claim_ref = st.text_input("Référence Réclamation", placeholder="CLM-XXX", key=f"input_{f['id']}")
            with col_b:
                if st.button("Lier", key=f"link_{f['id']}"):
                    if claim_ref:
                        manager.link_to_claim(f['id'], claim_ref)
                        st.success("Lié !")
                        st.rerun()
                    else:
                        st.warning("Entrez une réf")
