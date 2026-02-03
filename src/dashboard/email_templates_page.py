"""
Email Templates Page - Interface pour personnaliser les templates d'emails.

Permet aux clients de modifier les templates d'emails d'escalade utilisés
par le système automatique.
"""

import streamlit as st
from streamlit_quill import st_quill
from src.database.email_template_manager import EmailTemplateManager


def render_email_templates_page():
    """Rend la page de gestion des templates d'emails."""
    
    if 'client_email' not in st.session_state:
        st.warning("⚠️ Vous devez être connecté pour accéder à cette page.")
        return
    
    client_id = st.session_state.client_email
    template_manager = EmailTemplateManager()
    
    st.title("📧 Templates d'Emails Personnalisables")
    st.markdown("Personnalisez le contenu des emails envoyés automatiquement lors des escalades.")
    
    # Info sur les variables disponibles
    with st.expander("ℹ️ Variables disponibles", expanded=False):
        st.markdown("""
        Utilisez ces variables dans vos templates (elles seront automatiquement remplacées) :
        
        - `{claim_reference}` - Référence de la réclamation
        - `{carrier}` - Nom du transporteur
        - `{tracking_number}` - Numéro de suivi
        - `{amount}` - Montant réclamé
        - `{currency}` - Devise (EUR, USD, etc.)
        - `{customer_name}` - Nom du client final
        - `{delivery_address}` - Adresse de livraison  
        - `{dispute_type}` - Type de litige
        - `{company_name}` - Votre nom d'entreprise
        - `{order_id}` - Numéro de commande
        """)
    
    # Sélection du type de template
    col1, col2 = st.columns(2)
    
    with col1:
        template_type = st.selectbox(
            "Type de template",
            options=['status_request', 'warning', 'formal_notice'],
            format_func=lambda x: {
                'status_request': '📨 Demande de statut (J+7)',
                'warning': '⚠️ Avertissement (J+14)',
                'formal_notice': '⚖️ Mise en demeure (J+21)'
            }[x]
        )
    
    with col2:
        language = st.selectbox(
            "Langue",
            options=['FR', 'EN'],
            format_func=lambda x: {'FR': '🇫🇷 Français', 'EN': '🇬🇧 English'}[x]
        )
    
    
    # Récupérer le template actuel
    current_template = template_manager.get_template(template_type, language, client_id)
    
    # Variable insertion helpers
    st.markdown("### 🎯 Insertion rapide de variables")
    st.caption("Cliquez pour copier une variable dans votre presse-papier")
    
    var_cols = st.columns(5)
    var_cols2 = st.columns(5)
    variables = [
        ("{claim_reference}", "📋 Référence"),
        ("{carrier}", "🚚 Transporteur"),
        ("{tracking_number}", "🔢 Suivi"),
        ("{amount} {currency}", "💰 Montant"),
        ("{customer_name}", "👤 Client"),
        ("{date}", "📅 Date"),
        ("{location}", "📍 Lieu")
    ]
    
    for idx, (var, label) in enumerate(variables):
        if idx < 5:
            with var_cols[idx % 5]:
                if st.button(label, key=f"var_{idx}", width='stretch'):
                    st.code(var, language="text")
                    st.toast(f"✅ Copiez: {var}")
        else:
            with var_cols2[(idx - 5) % 5]:
                if st.button(label, key=f"var_{idx}", width='stretch'):
                    st.code(var, language="text")
                    st.toast(f"✅ Copiez: {var}")
    
    st.markdown("---")
    
    # Formulaire d'édition avec prévisualisation en direct
    st.markdown("### ✏️ Édition du template")
    
    # Créer deux colonnes: Édition et Prévisualisation
    edit_col, preview_col = st.columns([1, 1])
    
    with edit_col:
        st.markdown("#### 📝 Contenu")
        
        with st.form("template_form"):
            subject = st.text_input(
                "Sujet de l'email",
                value=current_template['subject'],
                help="Utilisez les variables ci-dessus, ex: Réclamation {claim_reference}"
            )
            
            
            # Éditeur visuel WYSIWYG avec Quill
            st.caption("✏️ Éditeur visuel - formatez votre email comme dans Word")
            
            # Configuration de la toolbar Quill
            quill_toolbar = [
                [{'header': [1, 2, 3, False]}],
                ['bold', 'italic', 'underline'],
                [{'list': 'ordered'}, {'list': 'bullet'}],
                [{'align': []}],
                ['clean']
            ]
            
            body = st_quill(
                value=current_template['body'],
                placeholder="Tapez votre email ici...",
                html=True,
                toolbar=quill_toolbar,
                key=f"quill_{template_type}_{language}"
            )
            
            # Mode avancé (HTML)
            with st.expander("⚙️ Mode Avancé (HTML)", expanded=False):
                st.caption("Pour les utilisateurs avancés seulement")
                body_html = st.text_area(
                    "Code HTML personnalisé",
                    value=body if body else current_template['body'],
                    height=200,
                    help="Éditez directement le code HTML de l'email"
                )
                if body_html != (body if body else current_template['body']):
                    body = body_html
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                save_btn = st.form_submit_button("💾 Sauvegarder", width='stretch', type="primary")
            
            with col2:
                reset_btn = st.form_submit_button("🔄 Réinitialiser", width='stretch')
            
            with col3:
                preview_btn = st.form_submit_button("👁️ Prévisualiser", width='stretch')
    
    with preview_col:
        st.markdown("#### 👁️ Prévisualisation en direct")
        st.caption("Aperçu de votre contenu formaté (variables non remplacées)")
        
        
        
        # Rendu du template avec le contenu exact de l'utilisateur
        preview_subject = subject
        # Quill peut retourner None au premier rendu
        preview_body = body if body is not None else current_template['body']
        
        # Afficher le sujet
        st.markdown(f"**Sujet:**")
        st.info(preview_subject)
        
        # Afficher le corps rendu en HTML
        st.markdown(f"**Corps (rendu HTML):**")
        
        # Wrapper pour styliser l'iframe
        st.markdown("""
        <style>
        .email-preview-container {
            border: 1px solid #dee2e6;
            border-radius: 8px;
            overflow: hidden;
            background: white;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Rendre le HTML de l'email dans un iframe
        st.components.v1.html(
            preview_body,
            height=400,
            scrolling=True
        )
    
    # Actions du formulaire
    if save_btn:
        success = template_manager.save_template(
            client_id=client_id,
            template_type=template_type,
            language=language,
            subject=subject,
            body_html=body
        )
        
        if success:
            st.success("✅ Template sauvegardé avec succès !")
            st.balloons()
        else:
            st.error("❌ Erreur lors de la sauvegarde du template.")
    
    if reset_btn:
        success = template_manager.delete_template(client_id, template_type, language)
        if success:
            st.success("✅ Template réinitialisé au modèle par défaut !")
            st.rerun()
        else:
            st.error("❌ Erreur lors de la réinitialisation.")
    
    # Statistiques
    st.markdown("---")
    st.markdown("### 📊 Vos templates personnalisés")
    
    all_templates = template_manager.get_all_templates(client_id)
    
    if all_templates:
        for template in all_templates:
            with st.expander(f"{template['template_type']} - {template['language']}"):
                st.markdown(f"**Créé le :** {template['created_at']}")
                st.markdown(f"**Modifié le :** {template['updated_at']}")
                st.code(template['subject'], language='text')
    else:
        st.info("ℹ️ Vous utilisez actuellement les templates par défaut. Modifiez-les ci-dessus pour les personnaliser.")


if __name__ == "__main__":
    render_email_templates_page()
