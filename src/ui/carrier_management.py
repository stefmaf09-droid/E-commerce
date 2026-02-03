"""
UI component for managing custom carriers in Settings tab.
"""

import streamlit as st
from src.utils.custom_carriers import CustomCarrierManager


def render_carrier_management():
    """Render custom carrier management interface."""
    
    st.markdown("### 🚚 Gestion des Transporteurs")
    
    manager = CustomCarrierManager()
    client_email = st.session_state.get('client_email', '')
    
    # Get all carriers
    all_carriers = manager.get_all_carriers(client_email)
    custom_carriers = manager.get_carriers(client_email)
    
    # Display carriers
    st.markdown("#### 📦 Transporteurs Disponibles")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Transporteurs Standards**")
        standard = ['Colissimo', 'Chronopost', 'Mondial Relay', 'DPD', 'UPS', 'DHL', 'GLS', 'Colis Privé', 'Relais Colis']
        for carrier in standard:
            st.text(f"✓ {carrier}")
    
    with col2:
        st.markdown(f"**Vos Transporteurs Personnalisés** ({len(custom_carriers)})")
        if custom_carriers:
            for carrier in custom_carriers:
                col_name, col_del = st.columns([4, 1])
                with col_name:
                    st.text(f"🏷️ {carrier['name']}")
                with col_del:
                    if st.button("🗑️", key=f"del_carrier_{carrier['name']}"):
                        manager.delete_carrier(client_email, carrier['name'])
                        st.success(f"✅ {carrier['name']} supprimé")
                        st.rerun()
        else:
            st.info("Aucun transporteur personnalisé pour le moment")
    
    st.markdown("---")
    
    # Add custom carrier
    st.markdown("#### ➕ Ajouter un Transporteur Personnalisé")
    
    st.info("💡 **Pourquoi ?** Si vous travaillez avec un petit transporteur local ou régional non listé ci-dessus, ajoutez-le ici pour qu'il apparaisse dans vos options de litiges.")
    
    with st.form("add_carrier_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            carrier_name = st.text_input(
                "Nom du transporteur",
                placeholder="Ex: Coursier Express Lyon",
                help="Nom du transporteur à ajouter"
            )
        
        with col2:
            carrier_phone = st.text_input(
                "Téléphone (optionnel)",
                placeholder="Ex: 01 23 45 67 89"
            )
        
        carrier_website = st.text_input(
            "Site web (optionnel)",
            placeholder="Ex: www.transporteur.com"
        )
        
        carrier_notes = st.text_area(
            "Notes (optionnel)",
            placeholder="Informations complémentaires sur ce transporteur...",
            max_chars=200
        )
        
        submitted = st.form_submit_button("➕ Ajouter ce Transporteur", width='stretch')
        
        if submitted:
            if not carrier_name:
                st.error("⚠️ Veuillez renseigner le nom du transporteur")
            else:
                carrier_info = {}
                if carrier_phone:
                    carrier_info['phone'] = carrier_phone
                if carrier_website:
                    carrier_info['website'] = carrier_website
                if carrier_notes:
                    carrier_info['notes'] = carrier_notes
                
                success = manager.add_carrier(client_email, carrier_name, carrier_info)
                
                if success:
                    st.success(f"✅ {carrier_name} ajouté avec succès !")
                    st.balloons()
                    st.rerun()
                else:
                    st.error(f"❌ {carrier_name} existe déjà")
