import streamlit as st
import json
import os

# Path to the templates file
TEMPLATE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'appeal_templates.json')

def load_templates():
    """Load templates from JSON file."""
    if os.path.exists(TEMPLATE_FILE):
        with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_templates(templates):
    """Save templates to JSON file."""
    with open(TEMPLATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(templates, f, indent=4, ensure_ascii=False)

def render_templates_page():
    """Render the appeal letter templates management page."""
    st.title("📝 Gestion des Modèles de Lettres de Contestation")
    st.markdown("Personnalisez les modèles de lettres de contestation (appeals) générés par l'IA pour contester les refus des transporteurs.")

    # 1. Cheat Sheet for Variables
    with st.expander("ℹ️  Variables disponibles (insérez-les dans votre texte)"):
        st.markdown("""
        | Variable | Description |
        |---|---|
        | `{tracking_number}` | Numéro de suivi du colis |
        | `{claim_reference}` | Référence du dossier (Shop) |
        | `{ship_date}` | Date d'expédition |
        | `{recipient_name}` | Nom du destinataire |
        | `{client_name}` | Nom de votre boutique (Expéditeur) |
        | `{client_email}` | Votre email de contact |
        | `{claim_amount}` | Montant réclamé (€) |
        | `{refusal_reason}` | Motif du refus (détecté par IA) |
        | `{status_desc}` | Statut actuel du colis |
        | `{weight}` | Poids du colis (si disponible) |
        """)

    # 2. Template Selector
    templates = load_templates()
    
    if not templates:
        st.error("Aucun modèle trouvé ! Veuillez vérifier le fichier de configuration.")
        return

    # Map technical keys to friendly names
    friendly_names = {
        'bad_signature': '🛑 Signature non conforme',
        'weight_match': '⚖️ Poids conforme (Spoliation)',
        'bad_packaging': '📦 Emballage insuffisant',
        'deadline_expired': '⏳ Hors délai',
        'default': '📄 Modèle par défaut / Autre'
    }

    # Reverse mapping for logic
    name_to_key = {v: k for k, v in friendly_names.items()}
    # Add any keys not in friendly_names (custom ones?)
    for k in templates.keys():
        if k not in friendly_names:
            friendly_names[k] = k
            name_to_key[k] = k

    selected_name = st.selectbox(
        "Sélectionnez le modèle à modifier :",
        options=[friendly_names.get(k, k) for k in templates.keys()]
    )
    
    selected_key = name_to_key.get(selected_name, selected_name)

    # 3. Editor
    st.markdown("---")
    st.subheader(f"Édition : {selected_name}")
    
    current_content = templates[selected_key]
    
    new_content = st.text_area(
        "Contenu du modèle",
        value=current_content,
        height=500,
        help="Modifiez le texte ici. N'oubliez pas de sauvegarder."
    )

    # 4. Save Action
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("💾 Sauvegarder", type="primary"):
            if new_content != current_content:
                templates[selected_key] = new_content
                save_templates(templates)
                st.toast("Modèle sauvegardé avec succès !", icon="✅")
                st.rerun()
            else:
                st.info("Aucune modification détectée.")
    
    with col2:
        if st.button("🔄 Rétablir défaut"):
             st.toast("Fonctionnalité 'Rétablir' à venir...", icon="🚧")

    # Preview simulation (Optional, maybe later)
    # st.markdown("### Aperçu Simulé")
    # ...
