"""
Authentication functions for Streamlit dashboards.

This module contains all authentication-related functions including login,
registration, and password reset functionality.
"""

import streamlit as st
import os
import sys

# Path configuration
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(root_dir, 'src'))
sys.path.insert(0, root_dir)

from auth.credentials_manager import CredentialsManager
from onboarding.onboarding_manager import OnboardingManager


def authenticate():
    """
    Authentication with login and registration tabs.
    
    Returns:
        bool: True if user is authenticated, False otherwise.
    """
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.client_email = None
    
    if not st.session_state.authenticated:
        st.markdown("<h1 class='main-header'>🔐 Portail Client</h1>", unsafe_allow_html=True)
        
        # Tabs pour Login / Inscription
        tab1, tab2 = st.tabs(["🔑 Connexion", "✨ Nouveau Client"])
        
        with tab1:
            _render_login_form()
        
        with tab2:
            _render_registration_form()
        
        return False
    
    return True


def _render_login_form():
    """Render the login form."""
    st.markdown("### Connexion à votre compte")
    
    with st.form("login_form"):
        email = st.text_input("Email", placeholder="votre@email.com")
        password = st.text_input("Mot de passe", type="password", placeholder="Votre mot de passe")
        submitted = st.form_submit_button("Se connecter", width='stretch')
        
        if submitted:
            # CORRECTION SÉCURITÉ: Email ET password obligatoires
            if not email or not password:
                st.error("⚠️ Veuillez renseigner l'email ET le mot de passe")
                return False
            
            # Check if user exists
            manager = CredentialsManager()
            creds = manager.get_credentials(email)
            
            if creds:
                # SÉCURITÉ: Vérification du mot de passe avec bcrypt
                from auth.password_manager import verify_client_password, has_password, get_user_role
                
                # Check if user has a password set
                if not has_password(email):
                    st.warning("⚠️ Aucun mot de passe défini pour ce compte. Contactez l'administrateur.")
                    return False
                
                # Verify password
                if verify_client_password(email, password):
                    st.session_state.authenticated = True
                    st.session_state.client_email = email
                    
                    # Fetch and store user role
                    role = get_user_role(email)
                    st.session_state.role = role
                    
                    # Fetch client_id for logging
                    from src.database.database_manager import DatabaseManager
                    db = DatabaseManager()
                    client = db.get_client(email=email)
                    if client:
                        st.session_state.client_id = client['id']
                        
                        # Log Login Activity
                        from src.utils.activity_logger import ActivityLogger
                        ActivityLogger.log(
                            client_id=client['id'],
                            action='login',
                            details={'role': role},
                            ip_address='127.0.0.1' 
                        )
                    
                    st.success(f"✅ Connexion réussie ! (Rôle: {role})")
                    st.rerun()
                else:
                    st.error("❌ Mot de passe incorrect")
            else:
                st.error("❌ Email non trouvé. Utilisez l'onglet 'Nouveau Client' pour vous inscrire.")
    
    # NOUVEAU: Lien "Mot de passe oublié ?"
    st.markdown("---")
    
    if st.checkbox("🔑 Mot de passe oublié ?"):
        _render_password_reset_form()


def _render_password_reset_form():
    """Render the password reset form."""
    st.markdown("### Réinitialisation du mot de passe")
    
    with st.form("reset_password_form"):
        reset_email = st.text_input("Votre email", placeholder="votre@email.com")
        new_password = st.text_input("Nouveau mot de passe", type="password", placeholder="Min. 6 caractères")
        confirm_password = st.text_input("Confirmer le mot de passe", type="password", placeholder="Retapez votre mot de passe")
        reset_submitted = st.form_submit_button("Réinitialiser le mot de passe", width='stretch')
        
        if reset_submitted:
            # Validation
            if not reset_email or not new_password or not confirm_password:
                st.error("⚠️ Tous les champs sont obligatoires")
            elif new_password != confirm_password:
                st.error("⚠️ Les mots de passe ne correspondent pas")
            elif len(new_password) < 6:
                st.error("⚠️ Le mot de passe doit contenir au moins 6 caractères")
            else:
                # Vérifier que l'email existe
                manager = CredentialsManager()
                creds = manager.get_credentials(reset_email)
                
                if creds:
                    # Réinitialiser le mot de passe
                    from auth.password_manager import set_client_password
                    
                    success = set_client_password(reset_email, new_password)
                    
                    if success:
                        st.success("✅ Mot de passe réinitialisé avec succès !")
                        st.info("Vous pouvez maintenant vous connecter avec votre nouveau mot de passe.")
                    else:
                        st.error("❌ Erreur lors de la réinitialisation")
                else:
                    st.error("❌ Email non trouvé. Vérifiez votre adresse email.")
    
    st.info("💡 En production, un email de vérification serait envoyé. Pour cette version, le mot de passe est directement réinitialisé.")


def _render_registration_form():
    """Render the registration form."""
    st.markdown("### Connectez votre boutique e-commerce")
    
    st.info("🎯 **Nouveau client ?** Connectez votre boutique en 3 étapes simples !")
    
    with st.form("registration_form"):
        st.markdown("**📧 Vos informations**")
        reg_email = st.text_input("Email professionnel", placeholder="contact@maboutique.com")
        reg_password = st.text_input("Créer un mot de passe", type="password", placeholder="Min. 6 caractères")
        reg_password_confirm = st.text_input("Confirmer le mot de passe", type="password", placeholder="Retapez votre mot de passe")
        
        st.markdown("**💰 Vos Informations de Paiement**")
        st.info("""
            🎯 **Modèle Success Fee (80/20)** :
            - Nous récupérons l'argent pour vous.
            - Vous recevez **80% du montant**.
            - Nous prélevons **20% de commission** uniquement sur les sommes récupérées.
            - **Aucun frais fixe, aucun abonnement.**
        """)
        
        reg_iban = st.text_input("IBAN (pour vos versements)", placeholder="FR76 0000 0000 ... (Optionnel)")
        reg_account_holder = st.text_input("Titulaire du compte", placeholder="Nom de votre entreprise")
        reg_bic = st.text_input("BIC/SWIFT (optionnel)", placeholder="ABCDEFGH")
        
        st.caption("💡 Vous pourrez renseigner votre IBAN plus tard depuis votre tableau de bord.")
        
        st.markdown("**🏪 Votre boutique**")
        platform = st.selectbox(
            "Plateforme e-commerce",
            ["Shopify", "WooCommerce", "PrestaShop", "Magento", "BigCommerce", "Wix"],
            help="Sélectionnez votre plateforme"
        )
        
        store_name = st.text_input("Nom de votre boutique", placeholder="Ma Boutique")
        store_url = st.text_input("URL de votre boutique", placeholder="https://maboutique.com")
        
        st.markdown("**🔑 Identifiants API**")
        st.caption(f"Consultez la documentation {platform} pour obtenir vos clés API")
        
        # Platform-specific fields
        api_key, api_secret = _render_platform_fields(platform)
        
        accept_terms = st.checkbox("J'accepte les conditions d'utilisation et la politique de confidentialité")
        
        register_submitted = st.form_submit_button("🚀 Créer mon compte", width='stretch', type="primary")
        
        if register_submitted:
            _process_registration(
                reg_email, reg_password, reg_password_confirm, store_name, store_url,
                platform, api_key, api_secret, reg_iban, reg_account_holder, reg_bic, accept_terms
            )


def _render_platform_fields(platform):
    """
    Render platform-specific API fields.
    
    Args:
        platform (str): The e-commerce platform name.
        
    Returns:
        tuple: (api_key, api_secret) values.
    """
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
    
    return api_key, api_secret


def register_client(reg_email, reg_password, reg_password_confirm, store_name, store_url,
                    platform, api_key, api_secret, reg_iban, reg_account_holder, reg_bic, accept_terms,
                    credentials_manager: CredentialsManager = None,
                    password_setter=None,
                    onboarding_manager: OnboardingManager = None,
                    email_sender=None):
    """Register a new client (testable helper).

    Returns:
        dict: { 'success': bool, 'errors': list }
    """
    errors = []

    # Basic validations
    if not reg_email or not reg_password or not reg_password_confirm:
        errors.append("⚠️ Tous les champs sont obligatoires")

    if reg_password != reg_password_confirm:
        errors.append("⚠️ Les mots de passe ne correspondent pas")

    if len(reg_password) < 6:
        errors.append("⚠️ Le mot de passe doit contenir au moins 6 caractères")

    if not store_name or not store_url:
        errors.append("⚠️ Veuillez renseigner le nom et l'URL de votre boutique")

    if not api_key or not api_secret:
        errors.append("⚠️ Veuillez renseigner vos identifiants API")

    if not accept_terms:
        errors.append("⚠️ Vous devez accepter les conditions d'utilisation")

    # Managers defaults
    manager = credentials_manager or CredentialsManager()

    existing_creds = manager.get_credentials(reg_email)
    if existing_creds:
        errors.append("⚠️ Cet email est déjà utilisé. Utilisez l'onglet 'Connexion'.")

    if errors:
        return { 'success': False, 'errors': errors }

    # Build credentials dict
    credentials = {
        'shop_url': store_url if platform == "Shopify" else api_key,
        'access_token': api_secret,
        'store_name': store_name,
    }

    if platform == "WooCommerce":
        credentials['consumer_key'] = api_key
        credentials['consumer_secret'] = api_secret

    success = manager.store_credentials(
        client_id=reg_email,
        platform=platform.lower(),
        credentials=credentials
    )

    # Store bank info ONLY if provided
    if reg_iban:
        try:
            from payments.manual_payment_manager import add_bank_info
            add_bank_info(
                client_email=reg_email,
                iban=reg_iban.replace(" ", "").upper(),
                bic=reg_bic.upper() if reg_bic else None,
                account_holder_name=reg_account_holder if reg_account_holder else reg_email.split('@')[0],
                bank_name="Banque Source"
            )
        except Exception:
            # Non-fatal
            pass

    if not success:
        return { 'success': False, 'errors': ["❌ Erreur lors de la création du compte"] }

    # Set password
    pwd_setter = password_setter or (lambda email, pwd: __import__('auth.password_manager', fromlist=['set_client_password']).set_client_password(email, pwd))
    pwd_success = pwd_setter(reg_email, reg_password)

    if not pwd_success:
        return { 'success': False, 'errors': ["❌ Erreur lors de la création du mot de passe"] }

    # Send welcome email (best effort)
    if email_sender:
        try:
            email_sender.send_welcome_email(recipient_email=reg_email, store_name=store_name)
        except Exception:
            pass

    # Initialize onboarding
    onboard_mgr = onboarding_manager or OnboardingManager()
    try:
        onboard_mgr.initialize_onboarding(reg_email)
        onboard_mgr.mark_step_complete(reg_email, 'store_setup')
    except Exception:
        # best effort
        pass

    return { 'success': True, 'errors': [] }


def _process_registration(reg_email, reg_password, reg_password_confirm, store_name, store_url,
                          platform, api_key, api_secret, reg_iban, reg_account_holder, reg_bic, accept_terms):
    """Process the registration form submission (UI wrapper)."""
    result = register_client(
        reg_email, reg_password, reg_password_confirm, store_name, store_url,
        platform, api_key, api_secret, reg_iban, reg_account_holder, reg_bic, accept_terms
    )

    if not result['success']:
        for error in result['errors']:
            st.error(error)
        return

    # Success path: configure session and redirect to client dashboard
    st.success("🎉 Compte créé avec succès !")
    st.info("👉 Plus que 2 étapes pour finaliser votre espace : IBAN et bienvenue !")
    st.balloons()

    # Auto-login
    st.session_state.authenticated = True
    st.session_state.client_email = reg_email
    st.session_state.role = 'client'  # Default role for new users

    # Set flags to open portal and redirect to dashboard inline
    st.session_state.show_portal = True
    st.session_state.redirect_to_dashboard = True

    # Rerun to apply the redirect
    st.rerun()
