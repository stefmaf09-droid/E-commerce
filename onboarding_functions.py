"""
Onboarding UI functions for step-by-step client setup.
"""

import streamlit as st
from auth.credentials_manager import CredentialsManager
from payments.manual_payment_manager import ManualPaymentManager


def render_step_store_setup(client_email):
    """Step 1: Store Connection Setup."""
    st.markdown("## 🏪 Connectez votre boutique e-commerce")
    st.markdown("### Étape 1 sur 3")
    
    st.info("📦 **Configurez votre première boutique** pour commencer à récupérer vos litiges automatiquement.")
    
    with st.form("store_setup_form"):
        st.markdown("**🏪 Informations de la boutique**")
        platform = st.selectbox(
            "Plateforme e-commerce",
            ["Shopify", "WooCommerce", "PrestaShop", "Magento", "BigCommerce", "Wix"],
            help="Sélectionnez votre plateforme"
        )
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            country = st.selectbox("Pays de la boutique", ["France 🇫🇷", "USA 🇺🇸", "UK 🇬🇧", "Suisse 🇨🇭", "Canada 🇨🇦"], index=0)
            country_code = country.split(' ')[1].replace('🇫🇷', 'FR').replace('🇺🇸', 'US').replace('🇬🇧', 'UK').replace('🇨🇭', 'CH').replace('🇨🇦', 'CA')
        with col_c2:
            currency = st.selectbox("Devise principale", ["EUR (€)", "USD ($)", "GBP (£)", "CHF (CHF)", "CAD (C$)"], index=0)
            currency_code = currency.split(' ')[0]
        
        st.write("---")
        st.markdown(f"**🔑 Configuration API {platform}**")
        st.caption(f"Consultez la documentation {platform} pour obtenir vos clés API")
        
        store_name = st.text_input("Nom de votre boutique", placeholder="Ma Boutique")
        store_url = st.text_input("URL de votre boutique", placeholder="https://maboutique.com")
        
        if platform == "Shopify":
            with st.expander("❓ Où trouver mes identifiants Shopify ?"):
                st.markdown("""
                1. Connectez-vous à votre interface **Shopify Admin**.
                2. Allez dans **Paramètres** > **Applis et canaux de vente**.
                3. Cliquez sur **Développer des applications**.
                4. Créez une application et accordez les accès scope `read_orders` et `read_shipping`.
                5. Installez l'app pour obtenir votre **Access Token**.
                """)
            api_key = st.text_input("Shop URL", placeholder="maboutique.myshopify.com")
            api_secret = st.text_input("Access Token", type="password")
        elif platform == "WooCommerce":
            with st.expander("❓ Où trouver mes identifiants WooCommerce ?"):
                st.markdown("""
                1. Allez dans **WooCommerce** > **Réglages** > **Avancé**.
                2. Cliquez sur **REST API**.
                3. Cliquez sur **Ajouter une clé**.
                4. Donnez des droits de **Lecture/Écriture**.
                5. Copiez la **Consumer Key** et le **Consumer Secret**.
                """)
            api_key = st.text_input("Consumer Key", placeholder="ck_xxxxx")
            api_secret = st.text_input("Consumer Secret", type="password", placeholder="cs_xxxxx")
        elif platform == "PrestaShop":
            with st.expander("❓ Où trouver mes identifiants PrestaShop ?"):
                st.markdown("""
                1. Allez dans **Paramètres avancés** > **Webservice**.
                2. Cliquez sur **Ajouter une clé de webservice**.
                3. Cliquez sur **Générer** pour créer votre clé.
                4. Cochez les permissions pour `orders` et `order_details` (GET/POST).
                5. Enregistrez et copiez la clé.
                """)
            api_key = st.text_input("Webservice Key", placeholder="Votre clé PrestaShop")
            api_secret = st.text_input("Password (si requis)", type="password", placeholder="Laisser vide si pas de mot de passe")
        elif platform == "Magento":
            with st.expander("❓ Où trouver mes identifiants Magento ?"):
                st.markdown("""
                1. Allez dans **System** > **Extensions** > **Integrations**.
                2. Cliquez sur **Add New Integration**.
                3. Donnez accès aux ressources "Sales" et "Orders".
                4. Cliquez sur **Activate** pour obtenir vos tokens.
                5. Copiez l'**Access Token**.
                """)
            api_key = st.text_input("Access Token", type="password", placeholder="Votre token Magento")
            api_secret = st.text_input("Store Code", placeholder="default")
        elif platform == "Wix":
            with st.expander("❓ Où trouver mes identifiants Wix ?"):
                st.markdown("""
                1. Allez sur le **Wix Dev Center**.
                2. Créez une application pour votre site.
                3. Dans **Permissions**, ajoutez l'accès aux commandes (Orders).
                4. Copiez l'**API Key** et l'**App ID**.
                """)
            api_key = st.text_input("API Key", type="password")
            api_secret = st.text_input("Site ID / App ID")
        else:
            api_key = st.text_input("API Key / Client ID", placeholder="Votre clé API")
            api_secret = st.text_input("API Secret / Client Secret", type="password", placeholder="Votre secret API")
        
        submitted = st.form_submit_button("➡️ Continuer", width='stretch', type="primary")
        
        if submitted:
            # Validation
            if not all([store_name, store_url, api_key, api_secret]):
                st.error("❌ Veuillez remplir tous les champs")
                return False
            
            # Save store credentials
            manager = CredentialsManager()
            store_id = f"{store_name.lower().replace(' ', '_')}_{platform.lower()}"
            
            success = manager.save_credentials(
                email=client_email,
                platform=platform,
                credentials = {
                    'api_key': api_key,
                    'api_secret': api_secret,
                    'shop_url': api_key if platform == "Shopify" else None,
                    'country': country_code,
                    'currency': currency_code
                },
                store_url=store_url,
                store_name=store_name,
                store_id=store_id
            )
            
            if success:
                st.success("✅ Boutique connectée avec succès !")
                return True
            else:
                st.error("❌ Erreur lors de la connexion de la boutique")
                return False
    
    return False


def render_step_bank_info(client_email):
    """Step 2: Bank Information Setup."""
    st.markdown("## 💳 Vos Versements & Modèle Success Fee")
    st.markdown("### Étape 2 sur 3")
    
    st.markdown("""
        <div style='background-color: #eff6ff; padding: 20px; border-radius: 12px; border: 1px solid #bfdbfe; margin-bottom: 25px;'>
            <h4 style='color: #1e40af; margin-top: 0;'>💰 Comment vous êtes payé</h4>
            <p style='color: #1e40af;'>Notre modèle est basé sur la performance :</p>
            <ul style='color: #1e40af;'>
                <li><strong>80% pour vous</strong> : Vous recevez la grande majorité des sommes récupérées.</li>
                <li><strong>20% de Success Fee</strong> : Nous ne nous rémunérons que si nous gagnons pour vous.</li>
                <li><strong>Zéro frais fixe</strong> : Aucun abonnement, aucun frais d'installation.</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)
    
    payment_manager = ManualPaymentManager()
    bank_info = payment_manager.get_client_bank_info(client_email)
    
    if bank_info and bank_info['iban']:
        iban_raw = bank_info['iban']
        masked_iban = f"{iban_raw[:4]} {'*' * (len(iban_raw)-8)} {iban_raw[-4:]}"
        
        st.success(f"✅ **IBAN Configuré** : {masked_iban}")
        st.info("Vos futurs remboursements seront versés sur ce compte.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Modifier l'IBAN"):
                st.session_state.edit_iban_onboarding = True
        with col2:
            # The original "Confirmer et Continuer" button is replaced by the new "Terminer la configuration" button below
            pass
        
        st.write("---")
        st.markdown("### ⚖️ Mandat de Gestion & Légalité")
        with st.expander("📄 Lire le Mandat de Gestion (IMPORTANT)"):
            try:
                with open("docs/MANDAT_GESTION.md", "r", encoding="utf-8") as f:
                    st.markdown(f.read())
            except FileNotFoundError:
                st.error("Le fichier MANDAT_GESTION.md est introuvable.")
        
        accepted_mandate = st.checkbox("J'accepte le Mandat de Gestion et autorise Recours E-commerce à percevoir les fonds en mon nom conformément à la clause 2.")
        
        if st.button("🚀 Terminer la configuration", type="primary", width='stretch'):
            if not accepted_mandate:
                st.warning("⚠️ Vous devez accepter le mandat de gestion pour continuer.")
            else:
                # Assuming the intent is to proceed to the next step if mandate is accepted
                return True
                
        if st.session_state.get('edit_iban_onboarding', False):
            with st.form("edit_iban_onboarding_form"):
                new_iban = st.text_input("Nouvel IBAN")
                if st.form_submit_button("💾 Enregistrer"):
                    if new_iban:
                        payment_manager.add_client_bank_info(client_email, new_iban.replace(" ", "").upper())
                        st.session_state.edit_iban_onboarding = False
                        st.rerun()
    else:
        st.warning("⚠️ Aucun IBAN enregistré. Nous en avons besoin pour vous reverser vos fonds.")
        with st.form("bank_info_onboarding_form"):
            iban = st.text_input("Saisissez votre IBAN (FR...)", placeholder="FR76...")
            if st.form_submit_button("➡️ Enregistrer et Continuer", type="primary"):
                if iban:
                    payment_manager.add_client_bank_info(client_email, iban.replace(" ", "").upper())
                    return True
                else:
                    st.error("L'IBAN est requis pour enregistrer. Ou cliquez sur 'Passer' ci-dessous.")
        
        if st.button("⏭️ Passer cette étape (provisoire)"):
            return True
    
    return False
    
    return False


def render_step_welcome(client_email):
    """Step 3: Welcome & Getting Started."""
    st.markdown("## 🎉 Bienvenue sur votre espace !")
    st.markdown("### Étape 3 sur 3")
    
    st.success("✅ **Votre compte est configuré !**")
    
    st.markdown("""
    ### 🚀 Vous êtes prêt à récupérer vos litiges !
    
    Voici ce que vous pouvez faire dès maintenant :
    
    #### 📊 **Tableau de bord**
    - Visualisez tous vos litiges en temps réel
    - Suivez le statut de vos réclamations
    - Consultez vos statistiques de récupération
    
    #### 📸 **Preuves Photos**
    - Uploadez les photos de vos colis endommagés
    - Soumettez automatiquement vos réclamations
    - Laissez notre système gérer les échanges avec les transporteurs
    
    #### ⚙️ **Paramètres**
    - Ajoutez d'autres boutiques
    - Gérez vos transporteurs
    - Configurez vos préférences
    
    ---
    
    ### 💡 **Conseil de démarrage**
    
    Nous vous recommandons de commencer par :
    1. **Explorer le tableau de bord** pour comprendre l'interface
    2. **Ajouter des transporteurs personnalisés** si besoin (onglet Paramètres)
    3. **Uploader vos premières photos** de litiges (onglet Preuves Photos)
    
    ---
    
    ### 📞 **Besoin d'aide ?**
    
    Notre équipe support est disponible :
    - 📧 Email : support@recours-ecommerce.fr
    - 💬 Chat : Disponible dans le dashboard
    - 📚 Documentation : [Guide complet](https://docs.recours-ecommerce.fr)
    """)
    
    if st.button("🎯 Accéder au dashboard", width='stretch', type="primary"):
        return True
    
    return False


def render_onboarding(client_email, onboarding_manager):
    """Main onboarding coordinator."""
    # Get current step
    current_step = onboarding_manager.get_current_step(client_email)
    
    # Progress bar
    steps = ["store_setup", "bank_info", "welcome"]
    progress = (steps.index(current_step) + 1) / len(steps)
    
    st.progress(progress, text=f"Progression de l'onboarding : {int(progress * 100)}%")
    st.markdown("---")
    
    # Navigation state
    if 'onboarding_navigation' not in st.session_state:
        st.session_state.onboarding_navigation = 'forward'
    
    # Render current step
    step_completed = False
    
    if current_step == "store_setup":
        step_completed = render_step_store_setup(client_email)
    elif current_step == "bank_info":
        step_completed = render_step_bank_info(client_email)
    elif current_step == "welcome":
        step_completed = render_step_welcome(client_email)
    
    # Handle step completion
    if step_completed:
        onboarding_manager.mark_step_complete(client_email, current_step)
        
        # Check if onboarding is complete
        if onboarding_manager.is_onboarding_complete(client_email):
            onboarding_manager.mark_complete(client_email)
            st.rerun()
        else:
            # Move to next step
            st.rerun()
    
    # Back button (except for first step)
    if current_step != "store_setup":
        st.markdown("---")
        if st.button("⬅️ Retour à l'étape précédente"):
            # Get previous step
            current_idx = steps.index(current_step)
            if current_idx > 0:
                previous_step = steps[current_idx - 1]
                # Unmark current step
                onboarding_manager.mark_step_incomplete(client_email, current_step)
                st.rerun()
