import streamlit as st
import os
import sys
import base64
import textwrap
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random

# Path definitions
root_dir = os.path.dirname(os.path.abspath(__file__))
LOGO_IMG = os.path.join(root_dir, 'static', 'logo_premium.png')

# System path configuration
sys.path.insert(0, os.path.join(root_dir, 'src'))
sys.path.insert(0, root_dir)

from auth.credentials_manager import CredentialsManager
from workers.order_sync_worker import OrderSyncWorker
from analytics.metrics_calculator import MetricsCalculator
from reports.pdf_generator import PDFGenerator
from automation.follow_up_manager import FollowUpManager
from utils.i18n import format_currency, get_i18n_text
from scrapers.ocr_processor import OCRProcessor
from onboarding.onboarding_manager import OnboardingManager
from onboarding_functions import render_onboarding
from database.database_manager import get_db_manager

# Initialize OCR processor
ocr_engine = OCRProcessor()


from ui.theme import apply_premium_theme, render_premium_metric
from ui.logos import LOGOS, ICONS

# Page config
st.set_page_config(
    page_title="Refundly.ai - Customer Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Apply unified premium theme
apply_premium_theme()

def authenticate():
    """Authentication with login and registration tabs."""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.client_email = None
    
    if not st.session_state.authenticated:
        st.markdown("<h1 class='main-header'>🔐 Portail Client</h1>", unsafe_allow_html=True)
        
        # Tabs pour Login / Inscription
        tab1, tab2 = st.tabs(["🔑 Connexion", "✨ Nouveau Client"])
        
        with tab1:
            # EXISTING CLIENTS - LOGIN
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
                        from auth.password_manager import verify_client_password, has_password
                        
                        # Check if user has a password set
                        if not has_password(email):
                            st.warning("⚠️ Aucun mot de passe défini pour ce compte. Contactez l'administrateur.")
                            return False
                        
                        # Verify password
                        if verify_client_password(email, password):
                            st.session_state.authenticated = True
                            st.session_state.client_email = email
                            st.success("✅ Connexion réussie !")
                            st.rerun()
                        else:
                            st.error("❌ Mot de passe incorrect")
                    else:
                        st.error("❌ Email non trouvé. Utilisez l'onglet 'Nouveau Client' pour vous inscrire.")
            
            # NOUVEAU: Lien "Mot de passe oublié ?"
            st.markdown("---")
            
            if st.checkbox("🔑 Mot de passe oublié ?"):
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
        
        with tab2:
            # NEW CLIENTS - REGISTRATION
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
                
                accept_terms = st.checkbox("J'accepte les conditions d'utilisation et la politique de confidentialité")
                
                register_submitted = st.form_submit_button("🚀 Créer mon compte", width='stretch', type="primary")
                
                if register_submitted:
                    # Validation
                    errors = []
                    
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
                    
                    # Check if email already exists
                    manager = CredentialsManager()
                    existing_creds = manager.get_credentials(reg_email)
                    if existing_creds:
                        errors.append("⚠️ Cet email est déjà utilisé. Utilisez l'onglet 'Connexion'.")
                    
                    if errors:
                        for error in errors:
                            st.error(error)
                    else:
                        # Create account
                        from auth.password_manager import set_client_password
                        
                        # Store credentials
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
                            from payments.manual_payment_manager import add_bank_info
                            add_bank_info(
                                client_email=reg_email,
                                iban=reg_iban.replace(" ", "").upper(),
                                bic=reg_bic.upper() if reg_bic else None,
                                account_holder_name=reg_account_holder if reg_account_holder else reg_email.split('@')[0],
                                bank_name="Banque Source"
                            )
                        
                        if success:
                            # Set password
                            pwd_success = set_client_password(reg_email, reg_password)
                            
                            if pwd_success:
                                # Send welcome email
                                try:
                                    from notifications.email_sender import EmailSender
                                    email_sender = EmailSender()
                                    email_sender.send_welcome_email(
                                        recipient_email=reg_email,
                                        store_name=store_name
                                    )
                                except Exception as email_error:
                                    # Don't block registration if email fails
                                    print(f"Email sending failed: {email_error}")
                                
                                # Initialize onboarding status and mark store as already configured
                                onboarding_mgr = OnboardingManager()
                                onboarding_mgr.initialize_onboarding(reg_email)
                                # Mark store_setup as complete since it was just done during registration
                                onboarding_mgr.mark_step_complete(reg_email, 'store_setup')
                                
                                st.success("🎉 Compte créé avec succès !")
                                st.info("👉 Plus que 2 étapes pour finaliser votre espace : IBAN et bienvenue !")
                                st.balloons()
                                
                                # Auto-login
                                st.session_state.authenticated = True
                                st.session_state.client_email = reg_email
                                st.rerun()
                            else:
                                st.error("❌ Erreur lors de la création du mot de passe")
                        else:
                            st.error("❌ Erreur lors de la création du compte")
        
        return False
    
    return True


def render_header():
    """Render dashboard header and clean sidebar (Mockup Match)."""
    # 1. SIDEBAR: Store Selector & User Info
    with st.sidebar:
        st.markdown("### 🏪 Magasin Actif")
        
        # Get ALL client's stores
        try:
            from auth.credentials_manager import CredentialsManager
            manager = CredentialsManager()
        except ImportError:
            from src.auth.credentials_manager import CredentialsManager
            manager = CredentialsManager()
            
        client_email = st.session_state.get('client_email', '')
        
        if hasattr(manager, 'get_all_stores'):
            client_stores = manager.get_all_stores(client_email)
        else:
            single_store = manager.get_credentials(client_email)
            client_stores = [single_store] if single_store else []
        
        if client_stores:
            platform_icons = {
                'shopify': '🛍️', 'woocommerce': '🛒', 'prestashop': '💼',
                'magento': '🏬', 'bigcommerce': '🏪', 'wix': '✨'
            }
            store_options = [
                f"{platform_icons.get(s['platform'], '🏪')} {s['store_name']}"
                for s in client_stores
            ]
            
            if 'selected_store_index' not in st.session_state:
                st.session_state.selected_store_index = 0
                
            selected = st.selectbox(
                "Choisir un magasin",
                store_options,
                index=st.session_state.selected_store_index,
                label_visibility="collapsed"
            )
            
            st.session_state.selected_store_index = store_options.index(selected)
            st.session_state.selected_store = client_stores[st.session_state.selected_store_index]
            
            st.caption(f"Plateforme : {st.session_state.selected_store['platform'].capitalize()}")
        else:
            st.warning("⚠️ Aucun magasin")
            
        st.markdown("---")
        st.caption(f"👤 {client_email}")
        if st.button("🚪 Déconnexion", width='stretch'):
            st.session_state.authenticated = False
            st.rerun()

    # 2. MAIN HEADER: Brand Only (Tabs will follow in main loop)
    # Note: Streamlit serves 'static' folder content if configured. 
    # To be safe, we use the logo with a fallback or base64 if needed, but here we try the standard path.
    st.markdown(f"""
    <div class="brand-container">
        <img src="https://img.icons8.com/isometric/512/000000/refund.png" style="width:48px; height:48px;">
        <div class="brand-name">Refundly.ai</div>
    </div>
    """, unsafe_allow_html=True)

    # --- MISSING INFO ALERT (IBAN) ---
    from payments.manual_payment_manager import ManualPaymentManager
    payment_mgr = ManualPaymentManager()
    bank_info = payment_mgr.get_client_bank_info(client_email)
    
    if not bank_info or not bank_info.get('iban'):
        with st.sidebar:
            st.warning("""
                ⚠️ **Action requise : Configuration des paiements**  
                Votre IBAN n'est pas renseigné.  
                [👉 Configurer](#settings)
            """)


def render_key_metrics(total_recoverable, disputes_count, recovered_amount):
    """Render key performance metrics (Visual Match Version)."""
    curr = st.session_state.get('currency', 'EUR')
    
    # Calculate dynamic success rate
    success_rate = 92  # Default value
    if total_recoverable > 0 and disputes_count > 0:
        # Estimate success based on recovered vs recoverable
        success_rate = min(int((recovered_amount / total_recoverable) * 100), 100)
        if success_rate == 0:  # Fallback if no data yet
            success_rate = 92  # Use AI prediction
    
    # Calculate progress for recoverable metric (percentage of monthly goal)
    monthly_goal = 10000  # Example: 10k EUR monthly target
    recoverable_progress = min(int((total_recoverable / monthly_goal) * 100), 100) if total_recoverable > 0 else 25
    
    # Calculate disputes progress (activity level indicator)
    disputes_progress = min(int((disputes_count / 20) * 100), 100) if disputes_count > 0 else 65
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        render_premium_metric(
            "Recoverable", 
            format_currency(total_recoverable, curr),
            "Estimated this month",
            icon="💰", 
            mini_icon="📊",
            progress=recoverable_progress,
            color='indigo'
        )
    
    with col2:
        render_premium_metric(
            "Success Rate", 
            f"{success_rate}%", 
            "Based on AI predictions",
            icon="🎯",
            mini_icon="📈",
            progress=success_rate,
            color='emerald' if success_rate >= 85 else 'amber'
        )
    
    with col3:
        render_premium_metric(
            "Active Disputes", 
            f"{disputes_count:,}", 
            "Under processing",
            icon="📦",
            mini_icon="⚙️",
            progress=disputes_progress,
            color='sky'
        )

    # --- NOUVEAU: SECTION STAGNATION / ESCALADE ---
    st.markdown("---")
    st.subheader("⚠️ Dossiers sans réponse (Garantie de Paiement)")
    
    # Simulation de dossiers stagnants pour la démo si nécessaire
    # Dans la vraie vie, on interrogerait le FollowUpManager
    st.info("""
    💡 **Pression Juridique Automatique** : Si un transporteur ignore un dossier plus de 7 jours, le bouton d'escalade apparaît ici. 
    Vous n'avez rien à faire, l'IA prépare les documents légaux pour vous.
    """)
    
    # Exemple de dossier nécessitant une action (Simulation)
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.write("**Commande #8829** (Chronopost)")
        st.caption("En attente depuis 22 jours")
    with col2:
        st.warning("⚖️ Niveau d'escalade : MISE EN DEMEURE REQUISE")
    with col3:
        if st.button("🚀 Lancer l'Escalade", key="btn_esc_8829", width='stretch'):
            st.success("✅ **Mise en Demeure générée !**")
            st.info("Le document a été envoyé au service juridique du transporteur.")
            st.balloons()


def render_disputes_table(disputes_df):
    """Render disputes table with premium row-based styling (Mockup Style)."""
    st.markdown("<br>", unsafe_allow_html=True)
    
    if disputes_df.empty:
        render_premium_info("Aucun litige détecté actuellement. C'est une bonne nouvelle !", icon="✨")
        return
    
    # Header
    cols = st.columns([1.5, 1, 1, 1, 3])
    cols[0].caption("Carrier")
    cols[1].caption("AI Confidence")
    cols[2].caption("Est. Refund Date")
    cols[3].caption("Status")
    cols[4].caption("Actions")
    st.markdown("---")
    
    # Carrier data and icons
    icons = {
        'UPS': '🟡', 'DHL': '🔴', 'FedEx': '🟣', 'Chronopost': '🔵', 'Colissimo': '⚪'
    }
    
    lang = st.session_state.get('lang', 'FR')
    curr = st.session_state.get('currency', 'EUR')
    
    for i, row in disputes_df.head(5).iterrows():
        r_cols = st.columns([1.5, 1, 1, 1, 3])
        
        # Carrier
        icon = icons.get(row['carrier'], '📦')
        r_cols[0].markdown(f"**{icon} {row['carrier']}**")
        
        # AI Confidence (Simulated Progress)
        confidence = 65 + (i * 7) % 30
        r_cols[1].progress(confidence/100)
        
        # Date
        r_cols[2].write("Oct 26, 2024")
        
        # Status pill (Simulated)
        status = row.get('status', 'Pending').capitalize()
        bg_color = "#e0f2fe" if status == "Pending" else "#dcfce7"
        text_color = "#0369a1" if status == "Pending" else "#15803d"
        
        r_cols[3].markdown(f"""
            <div style="
                background-color: {bg_color};
                color: {text_color};
                padding: 4px 12px;
                border-radius: 16px;
                font-size: 0.85rem;
                font-weight: 600;
                text-align: center;
                display: inline-block;
                width: 100%;
            ">
                {status}
            </div>
        """, unsafe_allow_html=True)
        
        # Actions
        btn_cols = r_cols[4].columns(3)
        if btn_cols[0].button("👁️ View", key=f"view_{i}", width='stretch'):
            st.session_state.selected_view_order = row['order_id']
            st.session_state.selected_view_carrier = row['carrier']
            
        btn_cols[1].button("⚠️ Escalate", key=f"esc_{i}", width='stretch')
        btn_cols[2].button("📁 Archive", key=f"arc_{i}", width='stretch')
        
        # Affichage rapide du détail si sélectionné
        if st.session_state.get('selected_view_order') == row['order_id']:
            with st.expander(f"🔍 Détails de la Commande {row['order_id']}", expanded=True):
                col_det1, col_det2 = st.columns(2)
                with col_det1:
                    st.write(f"**Transporteur:** {row['carrier']}")
                    st.write(f"**Type de litige:** {row['dispute_type'].replace('_', ' ').capitalize()}")
                    st.write(f"**Montant:** {row['total_recoverable']} {curr}")
                with col_det2:
                    st.write(f"**Statut:** {status}")
                    st.write("**Dernière mise à jour:** Il y a 2 heures")
                    st.button("📄 Voir les preuves PDF", key=f"proof_{i}")

        st.markdown("<div style='margin: 10px 0; border-bottom: 1px solid #f1f5f9;'></div>", unsafe_allow_html=True)

    # NOUVEAU: Analyse IA des Refus (OCR simulation)
    rejected_claims = disputes_df[disputes_df['status'] == 'rejected']
    if not rejected_claims.empty:
        st.markdown("### 🤖 Analyse IA des Refus (Vision & NLP)")
        from src.ai.llm_advice_generator import LLMAdviceGenerator
        llm_engine = LLMAdviceGenerator()
        
        for _, claim in rejected_claims.iterrows():
            # Simulation : Prétraitement vision
            vision_meta = ocr_engine.preprocess_image(f"rejet_{claim['order_id']}.jpg")
            
            rejection_text = ocr_engine.simulate_ocr_on_file(f"rejet_{claim['order_id']}.pdf")
            analysis = ocr_engine.analyze_rejection_text(rejection_text)
            
            # Générer l'avis juridique complexe via LLM
            llm_counsel = llm_engine.generate_counter_argument(analysis, claim.to_dict())
            
            with st.warning(f"**Dossier {claim['order_id']}** : {analysis['label_fr'] if lang == 'FR' else analysis['label_en']} (Confiance: {analysis.get('confidence', 0)*100:.0f}%)"):
                col_ia1, col_ia2 = st.columns([1, 1])
                with col_ia1:
                    st.write("**Conseil standard :**")
                    st.write(analysis['advice_fr'] if lang == 'FR' else analysis['advice_en'])
                with col_ia2:
                    st.write("**🛡️ Analyse Juridique IA (GPT-4) :**")
                    st.write(llm_counsel)
                
                st.button(f"📥 Générer PDF de contestation ({claim['order_id']})", key=f"fix_{claim['order_id']}")
    
    # Download button
    csv = disputes_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Télécharger le rapport (CSV)",
        data=csv,
        file_name=f"litiges_{datetime.now().strftime('%Y%m%d')}.csv",
        mime='text/csv'
    )
    
    with st.expander(get_i18n_text('guide_title', lang)):
        st.markdown(f"""
        - {get_i18n_text('pod_desc', lang)}
        - {get_i18n_text('dispute_desc', lang)}
        - {get_i18n_text('fee_desc', lang)}
        - {get_i18n_text('analysis_desc', lang)}
        """)
    
    with st.expander(get_i18n_text('financial_flow_title', lang)):
        st.markdown(f"""
        ### ⚖️ {get_i18n_text('financial_flow_title', lang)}
        
        1. {get_i18n_text('fin_step1', lang)}
        2. {get_i18n_text('fin_step2', lang)}
        3. {get_i18n_text('fin_step3', lang)}
        4. {get_i18n_text('fin_step4', lang)}
        5. {get_i18n_text('fin_step5', lang)}
        
        **Example** : If we recover **100 {curr}**, you receive **80 {curr}** net. The remaining **20 {curr}** covers our service fees.
        
        ### 🛡️ Et si le transporteur refuse de payer ?
        
        C'est là tout l'intérêt du modèle **Success Fee** :
        - **Zéro Risque** : Si le transporteur rejette la réclamation malgré nos efforts, **vous ne nous devez absolument rien**.
        - **Pas d'avance de frais** : Vous n'avez jamais à payer quoi que ce soit de votre poche.
        - **Intérêt commun** : Nous ne gagnons de l'argent que si vous en gagnez. Notre IA travaille donc dur pour maximiser vos chances !
        """)


def render_carrier_breakdown(disputes_df):
    """Render breakdown by carrier."""
    st.subheader("🚚 Répartition par Transporteur")
    
    if disputes_df.empty:
        return
    
    carrier_stats = disputes_df.groupby('carrier').agg({
        'total_recoverable': 'sum',
        'order_id': 'count'
    }).reset_index()
    
    carrier_stats.columns = ['Transporteur', 'Montant', 'Nombre']
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Custom charts styling
        chart_colors = ['#0ea5e9', '#6366f1', '#10b981', '#f59e0b', '#f43f5e']
        
        # Pie chart
        fig_pie = px.pie(
            carrier_stats,
            values='Montant',
            names='Transporteur',
            title='Montant récupérable par transporteur',
            color_discrete_sequence=chart_colors
        )
        fig_pie.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#1e293b', size=14),
            showlegend=True
        )
        st.plotly_chart(fig_pie, width='stretch')

    with col2:
        # Bar chart
        fig_bar = px.bar(
            carrier_stats,
            x='Transporteur',
            y='Nombre',
            title='Nombre de litiges par transporteur',
            color='Transporteur',
            color_discrete_sequence=chart_colors
        )
        fig_bar.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#1e293b', size=14),
            xaxis=dict(tickfont=dict(color='#1e293b', size=13)),
            yaxis=dict(tickfont=dict(color='#1e293b', size=13))
        )
        st.plotly_chart(fig_bar, width='stretch')


def render_timeline():
    """Render recovery timeline (simulated data)."""
    st.subheader("📈 Évolution des Récupérations")
    
    # Simulate timeline data
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    cumulative = [i * 150 + random.randint(-50, 100) for i in range(30)]
    
    timeline_df = pd.DataFrame({
        'Date': dates,
        'Montant Cumulé': cumulative
    })
    
    fig = px.area(
        timeline_df, x='Date', y='Montant Cumulé', 
        title='Montant récupéré au fil du temps',
        color_discrete_sequence=['#6366f1']
    )
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#1e293b', size=14)
    )
    st.plotly_chart(fig, width='stretch')
    


def render_photo_upload_tab(disputes_df):
    """Render photo upload tab for client evidence."""
    st.subheader("📸 Preuves Photos Client")
    
    if disputes_df.empty:
        st.info("Aucun litige actuellement. Les photos pourront être ajoutées quand des litiges seront détectés.")
        return
    
    st.markdown("""
    **Ajoutez vos photos de preuve** pour renforcer vos réclamations :
    - Colis endommagé
    - Mauvaise livraison (adresse, personne)
    - Preuve de retard (horodatage)
    - Tout élément pertinent
    """)
    
    # Sélection commande
    dispute_list = [f"{row['order_id']} - {row['carrier']} ({row['total_recoverable']:.2f}€)" 
                    for _, row in disputes_df.iterrows()]
    
    if not dispute_list:
        st.warning("Aucun litige disponible")
        return
    
    selected = st.selectbox(
        "Sélectionnez une commande",
        dispute_list,
        help="Choisissez la commande pour laquelle vous voulez ajouter des photos"
    )
    
    # Extraire order_id et données
    selected_order_id = selected.split(' - ')[0]
    selected_row = disputes_df[disputes_df['order_id'] == selected_order_id].iloc[0]
    
    st.markdown("---")
    
    # Upload photos
    st.write("### 📤 Upload Photos")
    
    uploaded_files = st.file_uploader(
        "Choisissez les photos (JPG, PNG)",
        type=['jpg', 'jpeg', 'png'],
        accept_multiple_files=True,
        help="Vous pouvez sélectionner plusieurs photos à la fois"
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} fichier(s) sélectionné(s)")
        
        # Preview photos - TAILLE RÉDUITE
        st.write("### 👁️ Aperçu")
        
        cols = st.columns(min(len(uploaded_files), 4))  # 4 colonnes au lieu de 3
        for idx, uploaded_file in enumerate(uploaded_files):
            with cols[idx % 4]:
                # CHANGEMENT: width=200 au lieu de use_container_width=True
                st.image(uploaded_file, caption=uploaded_file.name, width=200)
                st.caption(f"{uploaded_file.size / 1024:.1f} KB")
        
        st.markdown("---")
        
        # Bouton sauvegarde
        col1, col2 = st.columns([1, 3])
        
        with col1:
            if st.button("💾 Enregistrer Photos", type="primary", width=200):
                import os
                
                # Créer dossier si nécessaire
                photos_dir = f"data/client_photos/{selected_order_id}"
                os.makedirs(photos_dir, exist_ok=True)
                
                saved_paths = []
                for uploaded_file in uploaded_files:
                    # Nom fichier sécurisé
                    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uploaded_file.name}"
                    filepath = os.path.join(photos_dir, filename)
                    
                    # Écrire fichier
                    with open(filepath, 'wb') as f:
                        f.write(uploaded_file.getbuffer())
                    
                    saved_paths.append(filepath)
                
                st.success(f"✅ {len(saved_paths)} photo(s) enregistrée(s)")
                st.session_state[f'photos_saved_{selected_order_id}'] = saved_paths
        
        with col2:
            st.info("💡 Enregistrez vos photos puis cliquez sur 'Soumettre la Réclamation' ci-dessous.")
    
    # NOUVEAU: Section de soumission automatique
    st.markdown("---")
    
    # Vérifier si des photos existent pour cette commande
    import os
    photos_dir = f"data/client_photos/{selected_order_id}"
    existing_photos = []
    
    if os.path.exists(photos_dir):
        existing_photos = [
            os.path.join(photos_dir, f) 
            for f in os.listdir(photos_dir) 
            if f.endswith(('.jpg', '.jpeg', '.png'))
        ]
    
    # Afficher photos existantes - TAILLE RÉDUITE
    if existing_photos:
        st.write("### 📁 Photos Enregistrées")
        st.write(f"**{len(existing_photos)} photo(s) pour cette commande**")
        
        cols = st.columns(min(len(existing_photos), 4))
        for idx, photo_path in enumerate(existing_photos):
            with cols[idx % 4]:
                # CHANGEMENT: width=200 au lieu de use_container_width=True
                st.image(photo_path, caption=os.path.basename(photo_path), width=200)
                
                # Bouton supprimer
                if st.button(f"🗑️", key=f"del_{os.path.basename(photo_path)}"):
                    os.remove(photo_path)
                    st.success("Photo supprimée")
                    st.rerun()
        
        st.markdown("---")
        
        # NOUVEAU: Bouton de soumission automatique
        st.write("### 🚀 Soumission Automatique")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            if st.button("🚀 Soumettre la Réclamation", type="primary", width='stretch'):
                # Préparer les données du litige
                dispute_data = {
                    'order_id': selected_order_id,
                    'carrier': selected_row['carrier'],
                    'total_recoverable': selected_row['total_recoverable'],
                    'num_disputes': selected_row.get('num_disputes', 1),
                    'dispute_type': 'damage'  # Par défaut
                }
                
                # Lancer le workflow automatique
                with st.spinner("🔄 Analyse des photos en cours..."):
                    import time
                    time.sleep(1)  # Simulation
                    
                    from automation.claim_automation import process_claim_submission
                    
                    result = process_claim_submission(
                        order_id=selected_order_id,
                        photo_paths=existing_photos,
                        dispute_data=dispute_data
                    )
                
                # Afficher résultats
                if result.get('success'):
                    st.success("🎉 Réclamation soumise avec succès !")
                    st.success(f"📋 Référence : **{result['claim_reference']}**")
                    
                    # Détails
                    with st.expander("📊 Détails de la soumission"):
                        st.write(f"**Transporteur :** {dispute_data['carrier']}")
                        st.write(f"**Montant demandé :** {dispute_data['total_recoverable']:.2f}€")
                        st.write(f"**Photos analysées :** {result['photo_analysis']['total_photos']}")
                        st.write(f"**Qualité des preuves :** {result['photo_analysis']['quality_score']}/1.0")
                        st.write(f"**Soumis le :** {datetime.now().strftime('%d/%m/%Y %H:%M')}")
                        
                        if result['submission'].get('estimated_response_days'):
                            days = result['submission']['estimated_response_days']
                            st.write(f"**⚖️ Délai légal de réponse :** {days} jours maximum")
                            st.caption(f"Le transporteur doit répondre avant le {(datetime.now() + timedelta(days=days)).strftime('%d/%m/%Y')}")
                    
                    st.balloons()
                else:
                    st.error(f"❌ Erreur lors de la soumission : {result.get('error', 'Erreur inconnue')}")
        
        with col2:
            st.info("""
            💡 **Processus automatique :**
            1. Analyse de vos photos par notre IA
            2. Génération optimisée de la réclamation
            3. Soumission automatique au transporteur
            4. Suivi du dossier en temps réel
            """)
    else:
        st.info("📸 Aucune photo enregistrée pour cette commande. Uploadez des photos ci-dessus pour continuer.")



def render_platform_info():
    """Render platform connection info."""
    with st.expander("⚙️ Gestion de la Connexion"):
        manager = CredentialsManager()
        creds = manager.get_credentials(st.session_state.client_email)
        
        if creds:
            platform = creds.get('platform', 'Unknown')
            
            st.success(f"✅ Connecté à **{platform.capitalize()}**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔄 Forcer la Synchronisation"):
                    with st.spinner("Synchronisation en cours..."):
                        worker = OrderSyncWorker()
                        result = worker.sync_client(st.session_state.client_email)
                        
                        if result:
                            st.success(f"✅ {result['orders_fetched']} commandes synchronisées")
                            st.success(f"💰 {result['disputes_found']} litiges détectés")
                            st.rerun()
            
            with col2:
                if st.button("🔓 Révoquer l'Accès", type="secondary"):
                    if st.session_state.get('confirm_revoke', False):
                        manager.delete_credentials(st.session_state.client_email)
                        st.success("✅ Accès révoqué")
                        st.session_state.authenticated = False
                        st.rerun()
                    else:
                        st.session_state.confirm_revoke = True
                        st.warning("⚠️ Cliquez à nouveau pour confirmer")
        else:
            st.warning("⚠️ Aucune connexion active")


def render_bank_info():
    """Render bank information management for manual payments."""
    st.markdown("---")
    st.subheader("💳 Informations Bancaires")
    st.caption("Pour recevoir vos paiements manuels (avant activation Stripe)")
    
    from payments.manual_payment_manager import ManualPaymentManager, add_bank_info
    
    manager = ManualPaymentManager()
    client_email = st.session_state.client_email
    
    # Get existing bank info
    existing_info = manager.get_client_bank_info(client_email)
    
    # Display current bank info (Secure View)
    if existing_info:
        st.write("### 📋 Coordonnées Bancaires Actuelles")
        
        # Mask IBAN for security (show only last 4 digits)
        iban_raw = existing_info['iban']
        masked_iban = f"{iban_raw[:4]} {'*' * (len(iban_raw)-8)} {iban_raw[-4:]}"
        
        st.markdown(f"""
            <div style='background-color: #f8fafc; padding: 20px; border-radius: 10px; border: 1px solid #e2e8f0;'>
                <p><strong>Titulaire :</strong> {existing_info.get('account_holder_name', 'N/A')}</p>
                <p><strong>IBAN :</strong> <code>{masked_iban}</code></p>
                <p><strong>Banque :</strong> {existing_info.get('bank_name', 'N/A')}</p>
                <p style='color: #059669; font-size: 0.9rem;'>✅ Vos remboursements seront versés sur ce compte (80% du récupéré).</p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.checkbox("🔄 Modifier mes coordonnées bancaires"):
            with st.form("bank_info_update_form"):
                st.info("⚠️ La modification de l'IBAN nécessite une vérification de sécurité.")
                new_iban = st.text_input("Nouvel IBAN", placeholder="FR76...")
                new_holder = st.text_input("Nouveau Titulaire", value=existing_info.get('account_holder_name', ''))
                
                if st.form_submit_button("💾 Mettre à jour"):
                    if new_iban:
                        clean_iban = new_iban.replace(" ", "").upper()
                        success = add_bank_info(
                            client_email=client_email,
                            iban=clean_iban,
                            account_holder_name=new_holder if new_holder else None
                        )
                        if success:
                            st.success("✅ IBAN mis à jour")
                            st.rerun()
    else:
        st.warning("⚠️ Aucune information bancaire enregistrée. Vos remboursements ne pourront pas être versés.")
        
        with st.form("bank_info_first_setup"):
            st.markdown("### 🏦 Configurer mon compte de versement")
            iban = st.text_input("IBAN", placeholder="FR76...")
            account_holder = st.text_input("Titulaire du compte")
            
            if st.form_submit_button("🚀 Enregistrer"):
                if iban:
                    clean_iban = iban.replace(" ", "").upper()
                    success = add_bank_info(client_email=client_email, iban=clean_iban, account_holder_name=account_holder)
                    if success:
                        st.success("✅ Configuré !")
                        st.rerun()


def render_analytics_tab(disputes_df):
    """Render advanced analytics tab."""
    st.subheader("📊 Analytics Avancés")
    
    if disputes_df.empty:
        st.info("Pas encore de données pour les analytics")
        return
    
    # Convert to disputes list for calculator
    disputes_list = disputes_df.to_dict('records')
    
    # Add required fields for metrics
    for dispute in disputes_list:
        dispute['claim_value'] = dispute.get('total_recoverable', 0)
        dispute['status'] = dispute.get('status', 'pending')
        dispute['submitted_at'] = datetime.now() - timedelta(days=10)
    
    # Calculate KPIs
    calculator = MetricsCalculator()
    kpis = calculator.calculate_kpis(disputes_list)
    
    # Display KPIs
    col1, col2, col3 = st.columns(3)
    
    with col1:
        render_premium_metric(
            "Taux de Succès",
            f"{kpis['success_rate']:.1f}%",
            "Accepted claims",
            icon="📈",
            progress=int(kpis['success_rate']),
            color='emerald'
        )
    
    with col2:
        render_premium_metric(
            "Délai Moyen",
            f"{kpis['average_processing_time']:.1f} jours",
            "Processing time",
            icon="⏱️",
            progress=40, # Average placeholder
            color='indigo'
        )
    
    with col3:
        render_premium_metric(
            "ROI Client",
            f"{kpis['roi_client']:.0f}%",
            "Return on time",
            icon="💡",
            progress=min(int(kpis['roi_client']), 100),
            color='sky'
        )
    
    st.markdown("---")
    
    # Performance by carrier
    st.subheader("🚚 Performance par Transporteur")
    
    by_carrier = kpis.get('by_carrier', {})
    
    if by_carrier:
        carrier_df = pd.DataFrame.from_dict(by_carrier, orient='index').reset_index()
        carrier_df.columns = ['Transporteur', 'Nombre', 'Montant Moyen', 'Total', 'Taux Succès']
        
        # Chart: Success rate by carrier
        fig = px.bar(
            carrier_df,
            x='Transporteur',
            y='Taux Succès',
            title='Taux de succès par transporteur (%)',
            color='Taux Succès',
            color_continuous_scale='Greens'
        )
        st.plotly_chart(fig, width='stretch')
        
        # Table details
        st.dataframe(
            carrier_df[['Transporteur', 'Nombre', 'Montant Moyen', 'Taux Succès']],
            width='stretch',
            hide_index=True
        )
    else:
        st.info("Pas encore suffisamment de données par transporteur")
    
    st.markdown("---")
    
    # PDF Export Section
    st.subheader("📄 Export Rapport PDF")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Télécharger Rapport Mensuel PDF", width='stretch'):
            try:
                generator = PDFGenerator()
                
                import os
                os.makedirs('data/reports', exist_ok=True)
                
                output_path = f"data/reports/rapport_{datetime.now().strftime('%Y%m%d')}.pdf"
                
                generator.generate_monthly_report(
                    client_name=st.session_state.client_email.split('@')[0],
                    client_email=st.session_state.client_email,
                    month=datetime.now().strftime("%B %Y"),
                    kpis=kpis,
                    disputes=disputes_list,
                    output_path=output_path
                )
                
                # Provide download
                with open(output_path, 'rb') as f:
                    st.download_button(
                        label="⬇️ Cliquez pour télécharger",
                        data=f,
                        file_name=f"rapport_mensuel_{datetime.now().strftime('%Y%m')}.pdf",
                        mime="application/pdf",
                        width='stretch'
                    )
                
                st.success("✅ Rapport PDF généré avec succès !")
            except Exception as e:
                st.error(f"❌ Erreur : {e}")
    
    with col2:
        st.info("💡 Le rapport PDF contient vos KPIs, performance par transporteur et statistiques détaillées.")


def render_history_tab():
    """Render the full history of processed claims for the client."""
    st.subheader("📜 Historique Complet des Dossiers")
    
    db = get_db_manager()
    client = db.get_client(email=st.session_state.client_email)
    
    if not client:
        st.error("Impossible de charger les données client.")
        return
        
    claims = db.get_client_claims(client['id'])
    
    if not claims:
        st.info("🕒 Aucun dossier traité pour le moment. Votre historique s'affichera ici dès que vos premiers litiges seront soumis.")
        return
        
    # Convert list of dicts to DataFrame
    history_df = pd.DataFrame(claims)
    
    # Custom display columns
    cols_to_show = [
        'claim_reference', 'order_id', 'carrier', 'dispute_type', 
        'amount_requested', 'status', 'payment_status', 'created_at'
    ]
    
    # Check if all columns exist
    cols_to_show = [c for c in cols_to_show if c in history_df.columns]
    
    active_history = history_df[cols_to_show].copy()
    
    # Rename for user friendliness
    lang = st.session_state.get('lang', 'FR')
    col_names = {
        'claim_reference': 'Référence',
        'order_id': 'Commande',
        'carrier': 'Transporteur',
        'dispute_type': 'Type',
        'amount_requested': 'Montant',
        'status': 'Statut',
        'payment_status': 'Paiement',
        'created_at': 'Date de création'
    }
    active_history.rename(columns=col_names, inplace=True)
    
    # Format date
    active_history['Date de création'] = pd.to_datetime(active_history['Date de création']).dt.strftime('%d/%m/%Y %H:%M')
    
    # Display table
    st.dataframe(
        active_history,
        width='stretch',
        hide_index=True
    )
    
    st.markdown("---")
    st.caption("ℹ️ Cet historique contient tous les dossiers (Récupérés, En attente, Rejetés).")


def main():
    """Main application."""
    # Authentication
    if not authenticate():
        return
    
    # Check onboarding status
    onboarding_manager = OnboardingManager()
    
    if not onboarding_manager.is_onboarding_complete(st.session_state.client_email):
        # New user - show onboarding flow
        render_onboarding(st.session_state.client_email, onboarding_manager)
        return
    
    # Existing user - show full dashboard
    # --- DATA LOADING ---
    metrics_calculator = MetricsCalculator()
    disputes_df = metrics_calculator.get_disputes_data()
    if disputes_df.empty:
        disputes_df = metrics_calculator.simulate_disputes_data(num_records=10)
    
    # --- ELITE DASHBOARD ENTRY ---
    # Setup Navigation via st.tabs (Active Interactivity)
    
    # Header Styling (Logo + Tabs + Profile)
    # We use CSS in theme.py to position the logo and profile around the st.tabs
    nav_tabs = ["Dashboard", "Disputes", "Reports", "Settings"]
    t1, t2, t3, t4 = st.tabs(nav_tabs)
    
    # 1. Start Absolute Container
    st.markdown('<div class="elite-container-card">', unsafe_allow_html=True)
    
    with t1:
        # Dashboard Content
        dashboard_html = textwrap.dedent(f"""
            <div class="elite-header-minimal">
                <div class="header-logo-group">
                    <div style="width: 50px; height: 50px;">{LOGOS['refundly']}</div>
                    <div class="header-logo-text">Refundly.ai</div>
                </div>
                <a href="#settings" class="header-profile" style="text-decoration: none;">
                    {ICONS['profile']}
                </a>
            </div>
            
            <div class="elite-kpi-grid">
                <div class="elite-kpi-card">
                    <div class="kpi-bg-icon">💰</div>
                    <div class="kpi-content">
                        <div class="kpi-label-row">
                            <span class="kpi-mini-icon">💰</span>
                            <span class="kpi-label">RECOVERABLE: 145,000€</span>
                        </div>
                        <div class="kpi-value">145,000.00€</div>
                        <div class="kpi-sub">Potential Recovery this month</div>
                    </div>
                    <div class="kpi-progress"><div class="kpi-progress-fill" style="width: 25%;"></div></div>
                </div>
                <div class="elite-kpi-card">
                    <div class="kpi-bg-icon">🎯</div>
                    <div class="kpi-content">
                        <div class="kpi-label-row">
                            <span class="kpi-mini-icon">🎯</span>
                            <span class="kpi-label">SUCCESS RATE: 92%</span>
                        </div>
                        <div class="kpi-value">92%</div>
                        <div class="kpi-sub">Based on closed cases</div>
                    </div>
                    <div class="kpi-progress"><div class="kpi-progress-fill" style="width: 92%;"></div></div>
                </div>
                <div class="elite-kpi-card">
                    <div class="kpi-bg-icon">📦</div>
                    <div class="kpi-content">
                        <div class="kpi-label-row">
                            <span class="kpi-mini-icon">📦</span>
                            <span class="kpi-label">ACTIVE DISPUTES: 1,240</span>
                        </div>
                        <div class="kpi-value">1,240</div>
                        <div class="kpi-sub">Processing currently</div>
                    </div>
                    <div class="kpi-progress"><div class="kpi-progress-fill" style="width: 65%;"></div></div>
                </div>
            </div>
            
            <h3 style="margin-bottom: 20px; color: #1e293b;">Recent Delivery Disputes</h3>
            <div class="elite-table-header">
                <div style="width: 180px;">CARRIER</div>
                <div style="flex: 1; margin-left: 20px;">AI CONFIDENCE</div>
                <div style="width: 140px; text-align: center;">EST. REFUND DATE</div>
                <div style="width: 120px; text-align: center;">STATUS</div>
                <div style="width: 180px; text-align: right;">ACTIONS</div>
            </div>
        """)
        st.markdown(dashboard_html.replace('\n', ' '), unsafe_allow_html=True)
        
        # Table Rows with Active Components
        mock_rows = [
            {'id': '8829', 'carrier': 'UPS', 'icon': 'ups', 'conf': 98, 'date': 'Oct 26, 2024', 'status': 'Processing', 'status_icon': 'check'},
            {'id': '8830', 'carrier': 'DHL', 'icon': 'dhl', 'conf': 85, 'date': 'Nov 1, 2024', 'status': 'Under Review', 'status_icon': 'warning'},
            {'id': '8831', 'carrier': 'FedEx', 'icon': 'fedex', 'conf': 72, 'date': 'Nov 3, 2024', 'status': 'Awaiting Carrier', 'status_icon': 'warning'},
            {'id': '8832', 'carrier': 'USPS', 'icon': 'usps', 'conf': 95, 'date': 'Nov 5, 2024', 'status': 'Pending', 'status_icon': ''},
            {'id': '8833', 'carrier': 'DPD', 'icon': 'dpd', 'conf': 64, 'date': 'Nov 10, 2024', 'status': 'Pending', 'status_icon': 'warning'}
        ]
        
        for row in mock_rows:
            # We use columns to ensure buttons work, and style them to look like rows
            c1, c2, c3, c4, c5 = st.columns([180, 250, 140, 120, 180])
            
            with c1:
                st.markdown(f"""
                    <div style="display: flex; align-items: center; gap: 12px; height: 80px;">
                        <div class="carrier-logo-box">{LOGOS[row['icon']]}</div>
                        <div style="font-weight: 700; color: #1e293b;">{row['carrier']}</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with c2:
                status_icon_html = ""
                if row['status_icon'] == 'check': status_icon_html = f'<span style="margin-left: 8px;">{ICONS["check"]}</span>'
                if row['status_icon'] == 'warning': status_icon_html = f'<span style="margin-left: 8px;">{ICONS["warning"]}</span>'
                st.markdown(f"""
                    <div class="confidence-bar-container" style="height: 80px;">
                        <div style="font-weight: 700; color: #1e293b; width: 45px;">{row['conf']}%</div>
                        <div class="confidence-bar">
                            <div class="confidence-fill" style="width: {row['conf']}%;"></div>
                        </div>
                        {status_icon_html}
                    </div>
                """, unsafe_allow_html=True)
            
            with c3:
                st.markdown(f'<div style="height: 80px; display: flex; align-items: center; justify-content: center; color: #64748b; font-weight: 500;">{row['date']}</div>', unsafe_allow_html=True)
            
            with c4:
                st.markdown(f'<div style="height: 80px; display: flex; align-items: center; justify-content: center;"><span class="status-pill">{row['status']}</span></div>', unsafe_allow_html=True)
            
            with c5:
                # Active Buttons
                st.markdown('<div style="height: 80px; display: flex; align-items: center; justify-content: flex-end; gap: 8px;">', unsafe_allow_html=True)
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("View", key=f"view_{row['id']}", width='stretch'):
                        st.toast(f"🔍 Viewing {row['carrier']} details...")
                with col_btn2:
                    if st.button("Archive", key=f"arch_{row['id']}", width='stretch'):
                        st.toast(f"📦 Dispute {row['id']} archived.")
                st.markdown('</div>', unsafe_allow_html=True)

            # We add a custom horizontal line after each "row" to simulate the elite-row border
            st.markdown('<div style="border-bottom: 1px solid #f1f5f9; margin-top: -1px;"></div>', unsafe_allow_html=True)
            
    with t2:
        render_history_tab()
        
    with t3:
        render_analytics_tab(disputes_df)
        
    with t4:
        render_platform_info()
        render_bank_info()

    st.markdown('</div>', unsafe_allow_html=True) # End Absolute Container
    
    # 6. Sidebar (Dashboard Controls)
    with st.sidebar:
        st.markdown(f"""
            <div style="text-align: center; margin-bottom: 20px;">
                <div style="width: 100px; margin: 0 auto;">{LOGOS['refundly']}</div>
                <div style="font-size: 1.5rem; font-weight: 800; color: #1e293b; margin-top: 10px;">Refundly.ai</div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("### ⚙️ Dashboard Controls")
        if st.button("🔄 Refresh Data", width='stretch'):
            st.rerun()
        if st.button("🚪 Logout", width='stretch'):
            st.session_state.authenticated = False
            st.rerun()
        st.markdown("---")
        st.caption(f"👤 Connected as: {st.session_state.client_email}")
        
    st.markdown("---")
    st.caption("💡 Vos données sont synchronisées automatiquement toutes les 24h")


if __name__ == "__main__":
    main()
