import streamlit as st
import os
import sys
import pandas as pd
from datetime import datetime, timedelta
from streamlit_option_menu import option_menu
from PIL import Image

# Path definitions
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(root_dir, 'src'))
sys.path.insert(0, root_dir)

from auth.credentials_manager import CredentialsManager
from analytics.metrics_calculator import MetricsCalculator
from onboarding.onboarding_manager import OnboardingManager
from onboarding_functions import render_onboarding
from ui.theme import apply_premium_theme, render_premium_metric
from ui.logos import LOGOS, ICONS
from src.dashboard.auto_refresh import AutoRefresh, setup_auto_refresh


# Import UI and authentication functions from dashboard module
from src.dashboard import (
    authenticate,
    render_navigation_header,
    render_disputes_table_modern,
    render_analytics_tab,
    render_carrier_breakdown,
    render_dispute_details_page,
    render_carrier_overview_page,
    render_settings_page,
    render_reports_page,
    render_stagnation_escalation_section,
)
from src.dashboard.assistant_page import render_assistant_page
from src.dashboard.attachments_page import render_attachments_page


# Page config
st.set_page_config(
    page_title="Recours E-commerce | Dashboard",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply unified premium theme
apply_premium_theme()

# --- MODE TEST / PROD ---
if 'env_mode' not in st.session_state:
    st.session_state.env_mode = 'TEST' # Par défaut en Test pour la sécurité

# --- Sidebar ---
with st.sidebar:
    # Toggle Environnement
    st.markdown("### 🌍 Environnement")
    env_col1, env_col2 = st.columns([1, 4])
    with env_col1:
        if st.session_state.env_mode == 'TEST':
            st.markdown("🔴")
        else:
            st.markdown("🟢")
    with env_col2:
        mode = st.radio(
            "Mode",
            ['TEST', 'RÉEL'],
            index=0 if st.session_state.env_mode == 'TEST' else 1,
            label_visibility="collapsed",
            horizontal=True
        )

    # Mise à jour du mode
    new_mode = 'TEST' if mode == 'TEST' else 'PROD'
    if new_mode != st.session_state.env_mode:
        st.session_state.env_mode = new_mode
        st.rerun()
        
    if st.session_state.env_mode == 'TEST':
        st.warning("🛠️ Mode Test Actif\n(Données fictives)")
    
    st.markdown("---")
    
    # Logo & Navigation
    logo_path = os.path.join(root_dir, "static", "refundly_logo.png")
    if os.path.exists(logo_path):
        try:
            image = Image.open(logo_path)
            st.image(image, width=180)
        except Exception as e:
            logger.error(f"Failed to load logo: {e}")
            st.warning("Logo temporairement indisponible")
    
    # Auto-Refresh Controls
    refresh_interval = AutoRefresh.render_controls()
    AutoRefresh.manual_refresh_button()



def main():
    """Main dashboard application with dispute details and carrier overview pages."""
    # Initialize and check authentication
    if not authenticate():
        return
    
    # Check if we're on detail pages (skip onboarding for detail pages)
    active_page = st.session_state.get('active_page', 'Dashboard')
    
    if active_page == 'Dispute Details':
        # Display dispute details page
        from src.dashboard.dispute_details_page import render_dispute_details_page
        dispute_data = st.session_state.get('selected_dispute', {})
        render_dispute_details_page(dispute_data)
        return
    
    elif active_page == 'Carrier Overview':
        # Display carrier overview page
        from src.dashboard.carrier_overview_page import render_carrier_overview_page
        carrier = st.session_state.get('selected_carrier', 'Unknown')
        render_carrier_overview_page(carrier)
        return
    
    # Onboarding check (only for main dashboard)
    onboarding_manager = OnboardingManager()
    
    if not onboarding_manager.is_onboarding_complete(st.session_state.client_email):
        # New user - show onboarding flow
        render_onboarding(st.session_state.client_email, onboarding_manager)
        return
    
    # Existing user - show full dashboard
    # --- DATA LOADING ---
    # --- DATA LOADING ---
    from database.database_manager import DatabaseManager, set_db_manager
    
    # Sélection de la BDD selon l'environnement
    if st.session_state.env_mode == 'TEST':
        db_path = os.path.join(root_dir, 'data', 'test_recours_ecommerce.db')
    else:
        db_path = os.path.join(root_dir, 'data', 'recours_ecommerce.db')
        
    # [OFFLINE MODE PATCH] Wrapp DB connection to handle local firewall issues
    try:
        db_manager = DatabaseManager(db_path=db_path)
        set_db_manager(db_manager)
        
        # Get current client and load their claims
        client = db_manager.get_client(email=st.session_state.client_email)
        client_id = client['id'] if client else None
        
        # Load claims data
        claims_data = []
        if client_id:
            claims = db_manager.get_client_claims(client_id)
            for claim in claims:
                claims_data.append({
                    'claim_reference': claim.get('claim_reference', 'N/A'),
                    'order_id': claim.get('order_id', 'N/A'),
                    'carrier': claim.get('carrier', 'Unknown'),
                    'status': claim.get('status', 'pending'),
                    'tracking_number': claim.get('tracking_number', 'N/A'),
                    'total_recoverable': claim.get('amount_requested', 0),
                    'accepted_amount': claim.get('accepted_amount', 0),
                    'submitted_at': claim.get('submitted_at', ''),
                    'dispute_type': claim.get('dispute_type', 'unknown'),
                    'payment_status': claim.get('payment_status', 'unpaid'),
                    'customer_name': claim.get('customer_name', 'N/A'),
                    'delivery_address': claim.get('delivery_address', 'N/A'),
                    'ai_reason_key': claim.get('ai_reason_key'),
                    'ai_advice': claim.get('ai_advice')
                })
        st.session_state.offline_mode = False

    except Exception as e:
        # Fallback for local dev with firewall issues
        st.warning(f"⚠️ **Mode Hors Ligne**: Impossible de joindre la base de données ({str(e)}). L'assistant et les menus restent accessibles.")
        st.session_state.offline_mode = True
        client_id = 999
        claims_data = [] 

    
    # Convert to DataFrame
    import pandas as pd
    disputes_df = pd.DataFrame(claims_data)
    
    # Calculate metrics (needed for Dashboard page)
    curr = st.session_state.get('currency', 'EUR')
    total_recoverable = disputes_df['total_recoverable'].sum() if not disputes_df.empty else 0
    disputes_count = len(disputes_df) if not disputes_df.empty else 0
    
    # Calculate recovered amount from accepted claims
    recovered_amount = 0
    if not disputes_df.empty:
        accepted_claims = disputes_df[disputes_df['status'] == 'accepted']
        recovered_amount = accepted_claims['accepted_amount'].sum() if not accepted_claims.empty else 0
    
    # Calculate dynamic success rate
    success_rate = 0
    if total_recoverable > 0 and disputes_count > 0:
        if recovered_amount > 0:
            success_rate = min(int((recovered_amount / total_recoverable) * 100), 100)
        else:
            # Calculate based on statuses
            accepted_count = len(disputes_df[disputes_df['status'] == 'accepted']) if not disputes_df.empty else 0
            success_rate = min(int((accepted_count / disputes_count) * 100), 100) if disputes_count > 0 else 0
    
    recoverable_progress = min(int((total_recoverable / 10000) * 100), 100) if total_recoverable > 0 else 0
    disputes_progress = min(int((disputes_count / 50) * 100), 100) if disputes_count > 0 else 0
    
    # --- NAVIGATION SYSTEM ---
    from src.dashboard.ui_functions import render_navigation_header
    # The original render_navigation_header is replaced by option_menu as per instruction
    # from src.dashboard.ui_functions import render_navigation_header
    # active_page = render_navigation_header() # This line is replaced by the option_menu below
    
    # Sidebar Navigation
    with st.sidebar:
        # The logo and environment toggle are already at the top of the sidebar.
        # The instruction implies a new navigation menu here.
        # The original logo and Refundly.ai text at the bottom of the sidebar are removed
        # as the instruction's code snippet places a logo at the top of this new menu.
        st.image("static/logo_premium.png", use_container_width=True)
        st.markdown("---")
        
        selected = option_menu(
            "Menu Principal",
            ["Tableau de Bord", "💬 Assistant", "📎 Pièces Jointes", "Dépôt Preuves", "Mes Litiges", "Gestion Litiges", "📊 POD Analytics", "Rapports", "Réglages"],
            icons=["speedometer2", "chat-dots", "paperclip", "cloud-upload", "list-task", "clipboard-check", "bar-chart", "file-earmark-text", "gear"],
            menu_icon="cast",
            default_index=0,
        )
        
        st.markdown("---")
        # Store Manager logic... (This comment was in the provided snippet, keeping it)
        
        # Original controls from the bottom of the sidebar are moved here, after the new menu
        st.markdown("### ⚙️ Controls")
        if st.button("🔄 Refresh Data", width='stretch'):
            st.rerun()
        if st.button("🚪 Logout", width='stretch'):
            st.session_state.authenticated = False
            st.rerun()
        st.markdown("---")
        st.caption(f"👤 {st.session_state.client_email}")
    
    # --- PAGE RENDERING BASED ON NAVIGATION ---
    if selected == "Tableau de Bord":
        # Main Dashboard with Key Metrics
        # KPI Cards Container
        st.markdown('<div class="kpi-cards-container">', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            render_premium_metric(
                "Recoverable",
                f"{total_recoverable:,.0f}€",
                "Potential Recovery this month",
                icon="💰",
                progress=recoverable_progress
            )
        
        with col2:
            render_premium_metric(
                "Success Rate",
                f"{success_rate}%",
                "Based on closed cases",
                icon="🎯",
                progress=success_rate
            )
        
        with col3:
            render_premium_metric(
                "Active Disputes",
                f"{disputes_count:,}",
                "Processing currently",
                icon="📦",
                progress=disputes_progress
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Stagnation / Escalation Section (USP Feature)
        st.markdown('<div style="margin-top: 32px;"></div>', unsafe_allow_html=True)
        render_stagnation_escalation_section(disputes_df)
        
        # Disputes Table
        st.markdown('<div style="margin-top: 32px;"></div>', unsafe_allow_html=True)
        render_disputes_table_modern(disputes_df)
    
    elif selected == "Dépôt Preuves":
        # Upload page
        from upload_section import render_file_upload
        render_file_upload()
    
    elif selected == "Mes Litiges":
        # All Disputes page
        st.markdown('<div class="section-header">All Disputes</div>', unsafe_allow_html=True)
        render_disputes_table_modern(disputes_df)
        st.markdown("---")
        render_carrier_breakdown(disputes_df)
    
    elif selected == "Gestion Litiges":
        # Claims Management page with bulk actions
        from src.dashboard.claims_management_page import render_claims_management
        render_claims_management()
    
    elif selected == "📊 POD Analytics":
        # POD Analytics Dashboard
        from src.dashboard.pod_analytics_page import render_pod_analytics_page
        render_pod_analytics_page()
    
    elif selected == "Rapports":
        # Reports & Analytics page
        render_reports_page(disputes_df)
    
    elif selected == "Réglages":
        # Settings page
        render_settings_page()
        
    elif selected == "💬 Assistant":
        # Assistant page
        render_assistant_page()
        return  # Stop execution to prevent Dashboard content from rendering
    
    elif selected == "📎 Pièces Jointes":
        # Attachments page
        render_attachments_page()
        return
    
    # Sidebar cleanup - redundant controls removed
    
    # Trigger auto-refresh
    refresh_interval = st.session_state.get('refresh_interval', 0)
    if st.session_state.get('auto_refresh_enabled', False) and refresh_interval > 0:
        AutoRefresh.auto_refresh_trigger(refresh_interval)



if __name__ == "__main__":
    main()
