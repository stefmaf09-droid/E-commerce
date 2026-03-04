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
    Authentication with 2-column layout: value proposition left, form right.

    Returns:
        bool: True if user is authenticated, False otherwise.
    """
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.client_email = None
        
        # Reconexion automatique (Protection perte F5)
        qp = st.query_params
        if "token" in qp:
            saved_email = qp.get("token")
            from src.auth.password_manager import get_user_role, has_password
            
            # Simple vérification d'existence pour la démo / F5 reload
            if has_password(saved_email):
                st.session_state.authenticated = True
                st.session_state.client_email = saved_email
                st.session_state.role = get_user_role(saved_email)
                st.session_state.show_portal = True
                
                # Fetch onboarding status securely
                try:
                    from src.onboarding.onboarding_manager import OnboardingManager
                    mgr = OnboardingManager(saved_email)
                    st.session_state.onboarding_complete = mgr.is_onboarding_complete(saved_email)
                except Exception:
                    st.session_state.onboarding_complete = True  # fail-safe


    if not st.session_state.authenticated:
        _inject_auth_css()

        # ── FLOATING SUCCESS BADGES (animated) ──────────────────────────
        st.markdown("""
<div class="floating-badge badge-left" style="animation-delay: 0s;">
  <div class="badge-icon" style="background: #dcfce7;">💰</div>
  <div>
    <div class="badge-title">Remboursement reçu</div>
    <div class="badge-amount">+45,00 € Chronopost</div>
  </div>
</div>
<div class="floating-badge badge-right" style="animation-delay: 1.5s;">
  <div class="badge-icon" style="background: #d1fae5;">✅</div>
  <div>
    <div class="badge-title">Demande approuvée</div>
    <div class="badge-amount">UPS • +89,90 €</div>
  </div>
</div>
        """, unsafe_allow_html=True)

        # ── HERO SECTION ─────────────────────────────────────────────────
        st.markdown("""
<div class="auth-hero">
  <div class="auth-hero-pill">✨ Zéro risque • Commission uniquement sur les remboursements</div>
  <h1>On récupère <span class="highlight">ton argent</span><br>à ta place</h1>
  <p class="subtitle">
    Colis perdus, endommagés, retards de livraison…
    Refundly analyse, détecte et réclame <strong>automatiquement</strong> ce qui t'est dû.
  </p>
</div>
        """, unsafe_allow_html=True)

        # ── LOGIN / REGISTER FORM (centered) ─────────────────────────────
        _, col_form, _ = st.columns([1.2, 2, 1.2])
        with col_form:
            st.markdown('<div class="auth-form-card">', unsafe_allow_html=True)
            tab1, tab2 = st.tabs(["🔑 Connexion", "✨ Créer un compte"])
            with tab1:
                _render_login_form()
            with tab2:
                _render_registration_form()
            st.markdown('</div>', unsafe_allow_html=True)

        # ── TRUST BADGES ─────────────────────────────────────────────────
        st.markdown("""
<div class="trust-badges">
  <div class="trust-badge-item"><span class="icon">⚡</span> Analyse en 2 minutes</div>
  <div class="trust-badge-item"><span class="icon">🔒</span> Données sécurisées</div>
  <div class="trust-badge-item"><span class="icon">📈</span> +2M€ récupérés</div>
</div>
        """, unsafe_allow_html=True)

        # ── STATS CARDS ──────────────────────────────────────────────────
        st.markdown("""
<div class="auth-stats">
  <div class="auth-stat-card">
    <div class="stat-icon">💰</div>
    <div class="stat-value">127€</div>
    <div class="stat-label">Montant moyen récupéré</div>
  </div>
  <div class="auth-stat-card">
    <div class="stat-icon">⚡</div>
    <div class="stat-value">15 min</div>
    <div class="stat-label">Temps moyen par demande</div>
  </div>
  <div class="auth-stat-card">
    <div class="stat-icon">✅</div>
    <div class="stat-value">94%</div>
    <div class="stat-label">Taux de succès</div>
  </div>
</div>
        """, unsafe_allow_html=True)

        # ── FEATURES GRID ────────────────────────────────────────────────
        st.markdown("""
<div class="auth-features">
  <div class="auth-feature-card">
    <div class="auth-feature-icon" style="background: #7c3aed;">🧠</div>
    <h4>IA avancée</h4>
    <p>Détection automatique des opportunités de remboursement sur vos colis.</p>
  </div>
  <div class="auth-feature-card">
    <div class="auth-feature-icon" style="background: #0d9488;">🔒</div>
    <h4>100% sécurisé</h4>
    <p>Vos données sont chiffrées et ne sont jamais partagées avec des tiers.</p>
  </div>
  <div class="auth-feature-card">
    <div class="auth-feature-icon" style="background: #0284c7;">⏱️</div>
    <h4>Gain de temps</h4>
    <p>Plus besoin de gérer les réclamations manuellement.</p>
  </div>
  <div class="auth-feature-card">
    <div class="auth-feature-icon" style="background: #ea580c;">🛡️</div>
    <h4>Zéro risque</h4>
    <p>Pas de remboursement = pas de frais. Vous payez uniquement sur le succès.</p>
  </div>
  <div class="auth-feature-card">
    <div class="auth-feature-icon" style="background: #dc2626;">🔔</div>
    <h4>Notifications</h4>
    <p>Restez informé à chaque étape de vos demandes de remboursement.</p>
  </div>
  <div class="auth-feature-card">
    <div class="auth-feature-icon" style="background: #16a34a;">📊</div>
    <h4>Tableau de bord</h4>
    <p>Suivez tous vos litiges et remboursements en un coup d'œil.</p>
  </div>
</div>
        """, unsafe_allow_html=True)

        return False

    return True


def _inject_auth_css():
    """Premium CSS inspired by refundly.fr landing page design."""
    st.markdown(
        """
<style>
/* ===== GLOBAL AUTH PAGE ===== */
.stApp {
    background: linear-gradient(180deg, #f0fdf9 0%, #ecfeff 30%, #f0f9ff 70%, #eff6ff 100%) !important;
}

/* ===== HERO SECTION ===== */
.auth-hero {
    text-align: center;
    padding: 40px 20px 20px;
    max-width: 800px;
    margin: 0 auto;
}
.auth-hero-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(13, 148, 136, 0.08);
    border: 1px solid rgba(13, 148, 136, 0.2);
    border-radius: 50px;
    padding: 8px 20px;
    font-size: 0.85rem;
    color: #0d9488;
    font-weight: 600;
    margin-bottom: 24px;
}
.auth-hero h1 {
    font-size: 3.2rem;
    font-weight: 900;
    line-height: 1.15;
    color: #111827;
    margin: 0 0 20px;
    letter-spacing: -1px;
}
.auth-hero h1 .highlight {
    color: #0d9488;
}
.auth-hero .subtitle {
    font-size: 1.05rem;
    color: #6b7280;
    line-height: 1.6;
    max-width: 600px;
    margin: 0 auto 32px;
}

/* ===== TRUST BADGES ===== */
.trust-badges {
    display: flex;
    justify-content: center;
    gap: 32px;
    margin: 20px 0 32px;
    flex-wrap: wrap;
}
.trust-badge-item {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.88rem;
    color: #6b7280;
}
.trust-badge-item .icon {
    font-size: 1.1rem;
    color: #0d9488;
}

/* ===== KPI STAT CARDS ===== */
.auth-stats {
    display: flex;
    justify-content: center;
    gap: 20px;
    margin: 24px auto 32px;
    max-width: 720px;
    flex-wrap: wrap;
}
.auth-stat-card {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    padding: 24px 28px;
    min-width: 200px;
    flex: 1;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    transition: transform 0.2s, box-shadow 0.2s;
}
.auth-stat-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}
.auth-stat-card .stat-icon {
    font-size: 1.8rem;
    margin-bottom: 8px;
}
.auth-stat-card .stat-value {
    font-size: 2rem;
    font-weight: 800;
    color: #111827;
    margin: 4px 0;
}
.auth-stat-card .stat-label {
    font-size: 0.82rem;
    color: #9ca3af;
    font-weight: 500;
}

/* ===== FLOATING BADGES ===== */
.floating-badge {
    position: fixed;
    display: flex;
    align-items: center;
    gap: 10px;
    background: white;
    border-radius: 14px;
    padding: 12px 16px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    font-size: 0.82rem;
    z-index: 10;
    animation: floatBadge 3s ease-in-out infinite;
    border: 1px solid #f3f4f6;
}
.floating-badge .badge-icon {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    flex-shrink: 0;
}
.floating-badge .badge-title {
    font-weight: 600;
    color: #374151;
    font-size: 0.78rem;
}
.floating-badge .badge-amount {
    color: #0d9488;
    font-weight: 700;
    font-size: 0.82rem;
}
.badge-left {
    left: 3%;
    top: 18%;
}
.badge-right {
    right: 3%;
    top: 30%;
}
.badge-bottom-left {
    left: 5%;
    bottom: 25%;
}
@keyframes floatBadge {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-8px); }
}

/* ===== AUTH FORM CARD ===== */
.auth-form-card {
    background: white;
    border-radius: 20px;
    padding: 32px 28px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.08);
    border: 1px solid rgba(0,0,0,0.06);
    max-width: 440px;
    margin: 0 auto;
}

/* ===== FEATURES GRID ===== */
.auth-features {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    max-width: 800px;
    margin: 32px auto;
}
.auth-feature-card {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    padding: 24px 20px;
    text-align: left;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    transition: transform 0.2s, box-shadow 0.2s;
}
.auth-feature-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}
.auth-feature-icon {
    width: 44px;
    height: 44px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
    margin-bottom: 14px;
    color: white;
}
.auth-feature-card h4 {
    font-size: 0.95rem;
    font-weight: 700;
    color: #111827;
    margin: 0 0 6px;
}
.auth-feature-card p {
    font-size: 0.82rem;
    color: #6b7280;
    line-height: 1.5;
    margin: 0;
}

/* ===== BUTTON OVERRIDE ===== */
.stButton button {
    background: #0f766e !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 12px 28px !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 2px 8px rgba(13, 148, 136, 0.25) !important;
}
.stButton button:hover {
    background: #0d9488 !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 16px rgba(13, 148, 136, 0.35) !important;
}

/* ===== STREAMLIT OVERRIDES ===== */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Tabs */
[data-testid="stTab"] {
    font-weight: 600 !important;
    color: #6b7280 !important;
}
[data-testid="stTab"][aria-selected="true"] {
    color: #0d9488 !important;
    border-bottom-color: #0d9488 !important;
}
</style>
        """,
        unsafe_allow_html=True,
    )


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
                    
                    # —— Check onboarding status ————————————————
                    try:
                        from src.onboarding.onboarding_manager import OnboardingManager
                        mgr = OnboardingManager(email)
                        st.session_state.onboarding_complete = mgr.is_onboarding_complete(email)
                    except Exception:
                        st.session_state.onboarding_complete = True  # fail-safe: don't block login
                    # ————————————————————————————————————
                    
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
    """Render minimal registration form — email + password only.
    Store connection, IBAN, and API keys are collected in the onboarding wizard.
    """
    st.markdown("### ✨ Créer votre compte")
    st.caption("En 30 secondes — le reste se configure dans l'assistant après connexion.")

    with st.form("registration_form"):
        reg_email = st.text_input(
            "📧 Email professionnel",
            placeholder="contact@maboutique.com",
        )
        reg_password = st.text_input(
            "🔒 Mot de passe",
            type="password",
            placeholder="Min. 6 caractères",
        )
        reg_password_confirm = st.text_input(
            "🔒 Confirmer le mot de passe",
            type="password",
            placeholder="Retapez votre mot de passe",
        )

        accept_terms = st.checkbox(
            "J'accepte les [conditions d'utilisation](https://refundly.fr/cgu) et la politique de confidentialité"
        )

        register_submitted = st.form_submit_button(
            "🚀 Créer mon compte gratuitement",
            use_container_width=True,
            type="primary",
        )

    if register_submitted:
        # Basic validation
        if not reg_email or not reg_password or not reg_password_confirm:
            st.error("⚠️ Tous les champs sont obligatoires.")
            return
        if reg_password != reg_password_confirm:
            st.error("⚠️ Les mots de passe ne correspondent pas.")
            return
        if len(reg_password) < 6:
            st.error("⚠️ Le mot de passe doit comporter au moins 6 caractères.")
            return
        if not accept_terms:
            st.warning("⚠️ Veuillez accepter les conditions d'utilisation.")
            return

        # Register with minimal info
        _process_registration(
            reg_email, reg_password, reg_password_confirm,
            store_name="", store_url="",
            platform="", api_key="", api_secret="",
            reg_iban="", reg_account_holder="", reg_bic="",
            accept_terms=accept_terms,
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
    st.session_state.onboarding_complete = False  # Ensure new users go to wizard

    # Fetch client_id for analytics and logging (mirrors login flow)
    try:
        from src.database.database_manager import DatabaseManager
        db = DatabaseManager()
        client = db.get_client(email=reg_email)
        if client:
            st.session_state.client_id = client['id']
    except Exception:
        pass  # Non-fatal — analytics will gracefully show "Session invalide" if missing

    # Set flags to open portal and redirect to dashboard inline
    st.session_state.show_portal = True
    st.session_state.redirect_to_dashboard = True

    # Rerun to apply the redirect
    st.rerun()
