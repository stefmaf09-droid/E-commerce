"""
Multi-store management interface for client dashboard.
Provides UI for adding, viewing, and deleting stores.
"""

import streamlit as st
import json
import sqlite3
from cryptography.fernet import Fernet
from pathlib import Path
from src.auth.credentials_manager import CredentialsManager


def render_multi_store_management():
    """Complete multi-store management interface."""
    
    st.markdown("### 🏪 Gestion de vos Magasins")
    
    manager = CredentialsManager()
    client_email = st.session_state.get('client_email', '')
    stores = manager.get_all_stores(client_email)
    
    platform_icons = {
        'shopify': '🛍️',
        'woocommerce': '🛒', 
        'prestashop': '💼',
        'magento': '🏬',
        'bigcommerce': '🏪',
        'wix': '✨'
    }
    
    # === LISTE DES MAGASINS CONNECTÉS ===
    if stores:
        st.markdown("#### 📋 Vos Magasins Connectés")
        
        for store in stores:
            icon = platform_icons.get(store['platform'], '🏪')
            
            with st.expander(f"{icon} {store['store_name']} ({store['platform'].capitalize()})", expanded=False):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**Plateforme:** {store['platform'].capitalize()}")
                    st.markdown(f"**URL:** {store.get('credentials', {}).get('shop_url', '')}")
                    st.caption(f"ID: #{store['id']}")
                
                with col2:
                    if st.button(f"🗑️ Supprimer", key=f"del_{store['id']}", width='stretch'):
                        manager.delete_credentials(client_email, store['id'])
                        st.success("✅ Supprimé !")
                        st.rerun()
        
        st.markdown("---")
    
    # === AJOUTER UN NOUVEAU MAGASIN ===
    st.markdown("#### ➕ Ajouter un Nouveau Magasin")
    
    with st.form("add_new_store"):
        # Selection plateforme et nom
        col1, col2 = st.columns(2)
        
        with col1:
            platform = st.selectbox(
                "Plateforme",
                ['shopify', 'woocommerce', 'prestashop', 'magento', 'bigcommerce', 'wix'],
                format_func=lambda x: f"{platform_icons.get(x, '🏪')} {x.capitalize()}"
            )
        
        with col2:
            store_name = st.text_input("Nom du magasin", placeholder="Ex: Ma Boutique Paris")
        
        # URL
        shop_url = st.text_input("URL du magasin", placeholder="Ex: monshop.myshopify.com")
        
        # Credentials selon plateforme
        st.markdown("**Identifiants API**")
        
        if platform == 'shopify':
            api_key = st.text_input("API Key", type="password")
            api_password = st.text_input("API Password", type="password")
            
        elif platform == 'woocommerce':
            consumer_key = st.text_input("Consumer Key", type="password")
            consumer_secret = st.text_input("Consumer Secret", type="password")
            
        elif platform == 'prestashop':
            api_key = st.text_input("Webservice Key", type="password")
            api_password = None
            
        elif platform == 'magento':
            api_token = st.text_input("API Token", type="password")
            api_key = api_token
            api_password = None
            
        elif platform == 'bigcommerce':
            client_id = st.text_input("Client ID")
            access_token = st.text_input("Access Token", type="password")
            api_key = client_id
            api_password = access_token
            
        elif platform == 'wix':
            api_key = st.text_input("API Key", type="password")
            site_id = st.text_input("Site ID")
            api_password = site_id
        
        # Submit button
        submitted = st.form_submit_button("🔗 Connecter ce Magasin", width='stretch')
        
        if submitted:
            if not store_name or not shop_url:
                st.error("⚠️ Veuillez remplir le nom et l'URL du magasin")
            else:
                # Build credentials
                credentials = {'shop_url': shop_url}
                
                if platform == 'shopify':
                    credentials['api_key'] = api_key
                    credentials['api_password'] = api_password
                elif platform == 'woocommerce':
                    credentials['consumer_key'] = consumer_key
                    credentials['consumer_secret'] = consumer_secret
                elif platform in ['prestashop', 'magento']:
                    credentials['api_key'] = api_key
                elif platform == 'bigcommerce':
                    credentials['client_id'] = api_key
                    credentials['access_token'] = api_password
                elif platform == 'wix':
                    credentials['api_key'] = api_key
                    credentials['site_id'] = api_password
                
                # Save using direct SQL (old manager doesn't support store_name)
                try:
                    key_file = Path("config/.secret_key")
                    with open(key_file, 'rb') as f:
                        key = f.read()
                    cipher = Fernet(key)
                    
                    encrypted = cipher.encrypt(json.dumps(credentials).encode())
                    
                    conn = sqlite3.connect("database/credentials.db")
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        INSERT OR REPLACE INTO credentials 
                        (client_id, platform, store_name, credentials_encrypted, updated_at)
                        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (client_email, platform, store_name, encrypted))
                    
                    conn.commit()
                    conn.close()
                    
                    st.success(f"✅ {store_name} connecté avec succès !")
                    st.balloons()
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Erreur lors de la connexion: {e}")
    
    # Info help
    st.info("💡 **Besoin d'aide ?** Consultez la documentation de votre plateforme pour obtenir vos identifiants API.")
