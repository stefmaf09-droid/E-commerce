"""
Settings page for client dashboard.

This module handles all settings-related functionality including:
- Multi-store management (add, sync, delete stores)
- Platform information (connection details, API keys)
- Bank account management (IBAN, BIC, account holder)

Functions:
    render_settings_page: Main entry point for settings page
    render_store_management: Handle multi-store CRUD operations
    render_platform_info: Display platform connection details
    render_bank_info: Manage bank account information
    _render_bank_form: Helper for bank info form rendering
"""

from typing import Optional, Dict, Any, List
import streamlit as st
import os
import sys

# Path configuration
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(root_dir, 'src'))
sys.path.insert(0, root_dir)

from auth.credentials_manager import CredentialsManager
from utils.i18n import get_i18n_text, get_browser_language



def render_settings_page() -> None:
    """
    Render complete settings page with all sections.
    
    Displays three main sections:
    1. Store Management - CRUD operations for e-commerce stores
    2. Platform Info - Connection details and API credentials
    3. Bank Info - IBAN and payment account management
    
    Returns:
        None
    
    Side Effects:
        - Renders Streamlit UI components
        - May trigger database updates via user interactions
    """
    lang = get_browser_language()
    st.markdown(f'<div class="section-header">⚙️ {get_i18n_text("settings_header", lang)}</div>', unsafe_allow_html=True)
    
    # Multi-store management
    render_store_management()
    
    st.markdown("---")
    
    # Platform information
    render_platform_info()
    
    st.markdown("---")
    
    # Bank information
    render_bank_info()
    
    st.markdown("---")
    
    # Stripe Onboarding (Previously Dormant)
    from src.ui.stripe_onboarding import render_stripe_onboarding
    client_email = st.session_state.get('client_email', '')
    render_stripe_onboarding(client_email)

    st.markdown("---")
    
    # Email Notification Preferences
    render_notification_preferences()
    
    st.markdown("---")
    
    # Email templates
    render_email_templates_section()



def render_store_management() -> None:
    """
    Render store management section with CRUD capabilities.
    
    Allows users to:
    - View all connected e-commerce stores
    - Synchronize orders from specific stores
    - Delete stores (with confirmation)
    - Add new stores via platform-specific forms
    
    Supports platforms: Shopify, WooCommerce, PrestaShop, Magento, BigCommerce, Wix
    
    Returns:
        None
    
    Raises:
        None (handles errors internally with st.error)
    
    Side Effects:
        - Reads from credentials database
        - May modify store configuration
        - Triggers order synchronization
    
    Note:
        Migrated from legacy client_dashboard.py:1146-1227
    """
    lang = get_browser_language()
    st.markdown(f"### 🏪 {get_i18n_text('store_management', lang)}")
    st.caption(get_i18n_text('store_management_caption', lang))
    
    client_email = st.session_state.get('client_email', '')
    manager = CredentialsManager()
    
    # Get all stores
    if hasattr(manager, 'get_all_stores'):
        client_stores = manager.get_all_stores(client_email)
    else:
        single_store = manager.get_credentials(client_email)
        client_stores = [single_store] if single_store else []
    
    # Display existing stores
    if client_stores:
        st.markdown(f"**📋 {get_i18n_text('connected_stores', lang)}**")
        
        for idx, store in enumerate(client_stores):
            col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
            
            platform_icons = {
                'shopify': '🛍️', 'woocommerce': '🛒', 'prestashop': '💼',
                'magento': '🏬', 'bigcommerce': '🏪', 'wix': '✨'
            }
            icon = platform_icons.get(store.get('platform', '').lower(), '🏪')
            
            with col1:
                st.write(f"{icon} **{store.get('store_name', 'N/A')}**")
            with col2:
                st.caption(f"{store.get('platform', 'N/A').capitalize()}")
            with col3:
                if st.button("🔄", key=f"sync_{idx}", help=get_i18n_text('sync', lang)):
                    st.toast(f"🔄 {get_i18n_text('sync', lang)}...")
            with col4:
                if st.button("🗑️", key=f"delete_{idx}", help=get_i18n_text('delete', lang)):
                    if st.session_state.get(f'confirm_delete_{idx}'):
                        # Audit du 26/08/2026 (suite) : `CredentialsManager`
                        # n'a jamais eu de méthode `delete_store` — le
                        # `hasattr` était donc toujours False, la boutique
                        # n'était JAMAIS réellement supprimée, mais le
                        # message "✅ Boutique supprimée" s'affichait quand
                        # même (faux succès) et elle réapparaissait au
                        # rerun suivant. La vraie méthode est
                        # delete_credentials(client_id, store_id), avec
                        # l'id réel de la ligne (pas l'index d'affichage).
                        store_id = store.get('id')
                        deleted = manager.delete_credentials(client_id=client_email, store_id=store_id) if store_id else False
                        st.session_state.pop(f'confirm_delete_{idx}', None)
                        if deleted:
                            st.success(f"✅ {get_i18n_text('store_deleted', lang)}")
                        else:
                            st.error("❌ Erreur lors de la suppression de la boutique.")
                        st.rerun()
                    else:
                        st.session_state[f'confirm_delete_{idx}'] = True
                        st.warning(f"⚠️ {get_i18n_text('confirm_delete', lang)}")
    else:
        st.info(get_i18n_text('no_stores', lang))
    
    st.markdown("---")
    
    # Add new store
    with st.expander(f"➕ {get_i18n_text('add_store', lang)}"):
        with st.form("add_store_form"):
            st.markdown(f"**{get_i18n_text('connect_store', lang)}**")
            
            platform = st.selectbox(
                get_i18n_text('platform', lang),
                ["Shopify", "WooCommerce", "PrestaShop", "Magento", "BigCommerce", "Wix"]
            )
            
            store_name = st.text_input(get_i18n_text('store_name', lang), placeholder="Ma Nouvelle Boutique")
            store_url = st.text_input(get_i18n_text('url', lang), placeholder="https://maboutique.com")
            
            if platform == "Shopify":
                api_key = st.text_input("Shop URL", placeholder="maboutique.myshopify.com")
                api_secret = st.text_input("Access Token", type="password")
            elif platform == "WooCommerce":
                api_key = st.text_input("Consumer Key", placeholder="ck_xxxxx")
                api_secret = st.text_input("Consumer Secret", type="password")
            else:
                api_key = st.text_input("API Key", placeholder="Votre clé API")
                api_secret = st.text_input("API Secret", type="password")
            
            submitted = st.form_submit_button(f"✅ {get_i18n_text('add_this_store', lang)}", width='stretch')
            
            if submitted:
                if not store_name or not api_key or not api_secret:
                    st.error(f"⚠️ {get_i18n_text('all_fields_required', lang)}")
                else:
                    credentials = {
                        'shop_url': store_url if platform == "Shopify" else api_key,
                        'access_token': api_secret,
                        'store_name': store_name,
                    }
                    
                    if platform == "WooCommerce":
                        credentials['consumer_key'] = api_key
                        credentials['consumer_secret'] = api_secret
                    
                    # Add store
                    if hasattr(manager, 'add_store'):
                        success = manager.add_store(
                            client_id=client_email,
                            platform=platform.lower(),
                            credentials=credentials
                        )
                    else:
                        # Fallback to store_credentials
                        success = manager.store_credentials(
                            client_id=client_email,
                            platform=platform.lower(),
                            credentials=credentials
                        )
                    
                    if success:
                        st.success(get_i18n_text('store_added_success', lang).format(store_name=store_name))
                        st.rerun()
                    else:
                        st.error(f"❌ {get_i18n_text('error_adding_store', lang)}")


def render_platform_info() -> None:
    """
    Render e-commerce platform connection information.
    
    Displays:
    - Platform type (Shopify, WooCommerce, etc.)
    - Store name and URL
    - Connection status
    - Masked API credentials (for security)
    
    Returns:
        None
    
    Side Effects:
        - Reads from session state (selected_store)
        - Reads from credentials manager
    
    Security:
        API keys are masked showing only first 8 and last 4 characters
    
    Note:
        Migrated from legacy client_dashboard.py:1229-1284
    """
    lang = get_browser_language()
    st.markdown(f"### 🔌 {get_i18n_text('platform_info', lang)}")
    st.caption(get_i18n_text('platform_info_caption', lang))
    
    client_email = st.session_state.get('client_email', '')
    selected_store = st.session_state.get('selected_store')
    
    if not selected_store:
        # Try to get store from credentials manager
        manager = CredentialsManager()
        creds = manager.get_credentials(client_email)
        if creds:
            selected_store = creds
    
    if selected_store:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Plateforme**")
            platform = selected_store.get('platform', 'N/A').capitalize()
            st.info(f"📦 {platform}")
            
            st.markdown("**Nom de la boutique**")
            store_name = selected_store.get('store_name', 'N/A')
            st.write(store_name)
        
        with col2:
            st.markdown("**URL de la boutique**")
            shop_url = selected_store.get('shop_url', selected_store.get('store_url', 'N/A'))
            st.code(shop_url, language=None)
            
            st.markdown("**Statut de connexion**")
            st.success("✅ Connecté")
        
        # API Key info (masked for security)
        with st.expander("🔑 Identifiants API"):
            api_key = selected_store.get('consumer_key', selected_store.get('api_key', 'N/A'))
            if api_key and api_key != 'N/A':
                masked_key = api_key[:8] + '...' + api_key[-4:]
                st.code(masked_key, language=None)
            else:
                st.caption("Aucune clé API enregistrée")
            
            st.caption("🔒 Les identifiants complets sont chiffrés et stockés en sécurité")
    else:
        st.warning("⚠️ Aucune boutique sélectionnée. Veuillez d'abord connecter une boutique.")


def render_bank_info() -> None:
    """
    Render bank account information management interface.
    
    Allows users to:
    - View existing bank details (IBAN masked for security)
    - Add new bank account information
    - Update existing bank details
    
    Required for:
        Receiving 80% share of recovered dispute amounts
    
    Returns:
        None
    
    Raises:
        Exception: Caught and displayed via st.caption if bank info loading fails
    
    Side Effects:
        - Reads from payments.manual_payment_manager
        - May write new bank information to database
    
    Security:
        IBAN is masked (first 4 + last 4 digits shown)
    
    Note:
        Migrated from legacy client_dashboard.py:1286-1357
    """
    lang = get_browser_language()
    st.markdown(f"### 💳 {get_i18n_text('bank_info', lang)}")
    st.caption(get_i18n_text('bank_info_caption', lang))
    
    client_email = st.session_state.get('client_email', '')
    
    # Get existing bank info
    try:
        from payments.manual_payment_manager import ManualPaymentManager
        manager = ManualPaymentManager()
        bank_info = manager.get_client_bank_info(client_email)
    except Exception as e:
        bank_info = None
        st.caption(f"⚠️ Impossible de charger les infos bancaires: {str(e)}")
    
    if bank_info:
        # Display existing bank info
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**IBAN**")
            iban = bank_info.get('iban', 'Non renseigné')
            # Mask IBAN for security (show only last 4)
            if iban and iban != 'Non renseigné':
                masked_iban = iban[:4] + ' **** **** ' + iban[-4:]
                st.info(f"🏦 {masked_iban}")
            else:
                st.warning("⚠️ Non renseigné")
            
            st.markdown("**Titulaire du compte**")
            holder = bank_info.get('account_holder_name', 'Non renseigné')
            st.write(holder)
        
        with col2:
            st.markdown("**BIC/SWIFT**")
            bic = bank_info.get('bic', 'Non renseigné')
            st.info(f"🔢 {bic}")
            
            st.markdown("**Banque**")
            bank_name = bank_info.get('bank_name', 'Non renseigné')
            st.write(bank_name)
        
        st.success("✅ Informations bancaires enregistrées")
        
        # Update bank info
        with st.expander("✏️ Modifier mes coordonnées bancaires"):
            _render_bank_form(client_email, bank_info)
    else:
        # No bank info yet
        st.info("💡 Vous n'avez pas encore renseigné vos coordonnées bancaires")
        st.markdown("**Pourquoi c'est important ?**")
        st.write("Pour recevoir vos remboursements automatiquement, nous avons besoin de votre IBAN.")
        
        with st.expander("➕ Ajouter mes coordonnées bancaires", expanded=True):
            _render_bank_form(client_email, None)


def _render_bank_form(client_email: str, existing_info: Optional[Dict[str, Any]] = None) -> None:
    """
    Helper function to render bank information form.
    
    Args:
        client_email: Email of the client for whom to save bank info
        existing_info: Optional dict containing existing bank details
                      Keys: 'iban', 'bic', 'account_holder_name', 'bank_name'
    
    Returns:
        None
    
    Side Effects:
        - Renders Streamlit form
        - On submission, writes to payments database
        - Shows success/error messages
        - Triggers page rerun on success
    
    Validation:
        - IBAN is required
        - Account holder name is required
        - BIC and bank name are optional
    """
    with st.form("bank_info_form"):
        default_iban = existing_info.get('iban', '') if existing_info else ''
        default_bic = existing_info.get('bic', '') if existing_info else ''
        default_holder = existing_info.get('account_holder_name', '') if existing_info else ''
        default_bank = existing_info.get('bank_name', '') if existing_info else ''
        
        iban = st.text_input("IBAN", value=default_iban, placeholder="FR76 0000 0000 0000 0000 0000 000")
        bic = st.text_input("BIC/SWIFT", value=default_bic, placeholder="ABCDEFGH")
        holder_name = st.text_input("Titulaire du compte", value=default_holder, placeholder="Nom de votre entreprise")
        bank_name = st.text_input("Nom de la banque", value=default_bank, placeholder="Banque Populaire")
        
        submitted = st.form_submit_button("💾 Enregistrer", width='stretch', type="primary")
        
        if submitted:
            if not iban or not holder_name:
                st.error("⚠️ L'IBAN et le titulaire sont obligatoires")
            else:
                try:
                    from payments.manual_payment_manager import ManualPaymentManager
                    payment_manager = ManualPaymentManager()
                    success = payment_manager.add_client_bank_info(
                        client_email=client_email,
                        iban=iban.replace(" ", "").upper(),
                        bic=bic.upper() if bic else None,
                        account_holder_name=holder_name,
                        bank_name=bank_name if bank_name else "Banque Source"
                    )
                    
                    if success:
                        st.success("✅ Coordonnées bancaires enregistrées avec succès !")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ Erreur lors de l'enregistrement")
                except Exception as e:
                    st.error(f"❌ Erreur: {str(e)}")


def render_notification_preferences() -> None:
    """
    Render email notification preferences section.
    
    Allows users to:
    - Enable/disable specific notification types
    - Choose frequency (Immediate, Daily, Weekly digest)
    - Prevent notification overload
    
    Preferences are stored in clients.notification_preferences (JSON)
    """
    lang = get_browser_language()
    st.markdown(f"### 📧 {get_i18n_text('notification_prefs', lang)}")
    st.caption(get_i18n_text('notification_prefs_caption', lang))
    
    client_email = st.session_state.get('client_email', '')
    
    # Load current preferences
    import json
    from database.database_manager import get_db_manager
    
    db = get_db_manager()
    conn = db.get_connection()
    
    try:
        cursor = conn.cursor()
        # Audit du 26/08/2026 : placeholder '?' codé en dur — cassait avec une
        # vraie erreur de syntaxe SQL dès que db.db_type == 'postgres' (psycopg2
        # attend '%s'), confirmé en test live ("Erreur de chargement : erreur de
        # syntaxe..." affiché tel quel à l'utilisateur). DatabaseManager expose
        # justement `.placeholder` pour ce cas (déjà utilisé par _execute()) ;
        # on s'en sert ici puisqu'on passe par un curseur brut.
        cursor.execute(f"SELECT notification_preferences FROM clients WHERE email = {db.placeholder}", (client_email,))
        result = cursor.fetchone()
        
        if result and result[0]:
            current_prefs = json.loads(result[0])
        else:
            # Default preferences
            current_prefs = {
                'claim_created': True,
                'claim_updated': True,
                'claim_accepted': True,
                'payment_received': True,
                'deadline_warning': True,
                'frequency': 'immediate'
            }
    except Exception as e:
        st.caption(f"⚠️ Erreur de chargement: {e}")
        current_prefs = {
            'claim_created': True,
            'claim_updated': True,
            'claim_accepted': True,
            'payment_received': True,
            'deadline_warning': True,
            'frequency': 'immediate'
        }
    finally:
        conn.close()
    
    # Preferences form
    with st.form("notification_preferences_form"):
        st.markdown("**📬 Types de notifications**")
        st.caption("Décochez les notifications que vous ne souhaitez pas recevoir")
        
        col1, col2 = st.columns(2)
        
        with col1:
            claim_created = st.checkbox(
                "✉️ Nouveau litige créé",
                value=current_prefs.get('claim_created', True),
                help="Email confirmant la création d'un nouveau litige"
            )
            claim_updated = st.checkbox(
                "🔄 Mise à jour du litige",
                value=current_prefs.get('claim_updated', True),
                help="Email lorsque le transporteur répond"
            )
            claim_accepted = st.checkbox(
                "✅ Litige accepté",
                value=current_prefs.get('claim_accepted', True),
                help="Email lorsque votre réclamation est acceptée"
            )
        
        with col2:
            payment_received = st.checkbox(
                "💰 Paiement reçu",
                value=current_prefs.get('payment_received', True),
                help="Email confirmant le transfert de fonds"
            )
            deadline_warning = st.checkbox(
                "⚠️ Deadline proche (J-3)",
                value=current_prefs.get('deadline_warning', True),
                help="Rappel 3 jours avant l'expiration"
            )
        
        st.markdown("---")
        st.markdown("**⏱️ Fréquence d'envoi**")
        
        frequency = st.radio(
            "Choisissez comment recevoir vos notifications",
            options=['immediate', 'daily', 'weekly'],
            format_func=lambda x: {
                'immediate': '📨 Immédiat (dès que l\'événement se produit)',
                'daily': '📅 Quotidien (résumé une fois par jour à 9h)',
                'weekly': '📆 Hebdomadaire (résumé le lundi matin)'
            }[x],
            index=['immediate', 'daily', 'weekly'].index(current_prefs.get('frequency', 'immediate')),
            horizontal=False
        )
        
        st.info("💡 **Astuce** : Si vous recevez beaucoup de litiges, le mode 'Quotidien' vous évitera d'être submergé d'emails.")
        
        submitted = st.form_submit_button("💾 Enregistrer mes préférences", type="primary", use_container_width=True)
        
        if submitted:
            # Build preferences dict
            new_prefs = {
                'claim_created': claim_created,
                'claim_updated': claim_updated,
                'claim_accepted': claim_accepted,
                'payment_received': payment_received,
                'deadline_warning': deadline_warning,
                'frequency': frequency
            }
            
            # Save to database
            try:
                conn = db.get_connection()
                cursor = conn.cursor()
                # Audit du 26/08/2026 : même correction que pour la lecture
                # ci-dessus — placeholder dynamique selon le backend actif.
                cursor.execute(
                    f"UPDATE clients SET notification_preferences = {db.placeholder} WHERE email = {db.placeholder}",
                    (json.dumps(new_prefs), client_email)
                )
                conn.commit()
                conn.close()
                
                st.success("✅ Préférences enregistrées avec succès !")
                st.balloons()
                
                # Show summary
                enabled_count = sum([claim_created, claim_updated, claim_accepted, payment_received, deadline_warning])
                freq_label = {'immediate': 'Immédiat', 'daily': 'Quotidien', 'weekly': 'Hebdomadaire'}[frequency]
                st.info(f"📊 **{enabled_count}/5** notifications activées · Fréquence : **{freq_label}**")
                
            except Exception as e:
                st.error(f"❌ Erreur lors de l'enregistrement : {str(e)}")


def render_email_templates_section() -> None:
    """
    Render email templates customization section.
    
    Links to the dedicated email templates page for full editing.
    Shows quick preview of customization status.
    """
    st.markdown("### 📧 Templates d'Emails")
    st.caption("Personnalisez le contenu des emails d'escalade automatiques")
    
    client_email = st.session_state.get('client_email', '')
    
    # Quick info
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.info("💡 Vous pouvez personnaliser les emails envoyés automatiquement lors des escalades (demande de statut, avertissement, mise en demeure).")
    
    with col2:
        # Check if client has custom templates
        try:
            from src.database.email_template_manager import EmailTemplateManager
            manager = EmailTemplateManager()
            
            # Try to get client ID from session
            client_id = st.session_state.get('client_id')
            if client_id:
                custom_templates = manager.get_all_templates(client_id)
                if custom_templates:
                    st.success(f"✅ {len(custom_templates)} template(s) personnalisé(s)")
                else:
                    st.caption("📋 Templates par défaut")
        except Exception:
            st.caption("📋 Templates par défaut")
    
    # Link to full templates page
    st.markdown("**Actions disponibles:**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✏️ Modifier les templates", width='stretch', type="primary"):
            st.session_state['active_page'] = 'Email Templates'
            st.rerun()
    
    with col2:
        with st.popover("👁️ Prévisualiser"):
            st.markdown("**Types de templates:**")
            st.markdown("- 📨 Demande de statut (J+7)")
            st.markdown("- ⚠️ Avertissement (J+14)")
            st.markdown("- ⚖️ Mise en demeure (J+21)")
    
    with col3:
        with st.popover("ℹ️ Variables"):
            st.caption("Variables disponibles dans les templates:")
            st.code("{claim_reference}", language="text")
            st.code("{carrier}", language="text")
            st.code("{amount}", language="text")
            st.caption("+ 7 autres variables...")


