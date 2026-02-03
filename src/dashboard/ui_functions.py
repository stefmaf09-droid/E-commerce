"""
UI functions for Streamlit dashboards.

This module contains all UI-related functions for rendering various components
of the client dashboard including navigation, tables, analytics, etc.
"""

import streamlit as st
import os
import sys
import pandas as pd
from datetime import datetime, timedelta

# Path configuration
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(root_dir, 'src'))
sys.path.insert(0, root_dir)

from auth.credentials_manager import CredentialsManager
from workers.order_sync_worker import OrderSyncWorker
from ui.theme import render_premium_metric
from utils.i18n import format_currency, get_i18n_text


def render_navigation_header():
    """
    Render professional horizontal navigation header with styled tab buttons.
    
    Returns:
        str: The active page name.
    """
    client_email = st.session_state.get('client_email', 'user@example.com')
    
    # Initialize active page in session state
    if 'active_page' not in st.session_state:
        st.session_state.active_page = 'Dashboard'
    
    # Professional header with logo and user info
    st.markdown(f"""
    <style>
    .pro-nav-tab {{
        background: transparent;
        border: none;
        border-bottom: 3px solid transparent;
        padding: 12px 24px !important;
        font-size: 15px !important;
        font-weight: 600 !important;
        color: #64748b !important;
        cursor: pointer;
        transition: all 0.2s;
        margin: 0 !important;
    }}
    .pro-nav-tab:hover {{
        color: #4338ca !important;
        background: #f8f7ff !important;
    }}
    .pro-nav-tab-active {{
        color: #4338ca !important;
        border-bottom-color: #4338ca !important;
    }}
    </style>
    
    <div style="
        background: white;
        padding: 16px 32px;
        margin: -6rem -1rem 0rem -1rem;
        border-bottom: 1px solid #e0e7ff;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    ">
        <div style="display: flex; align-items: center; gap: 12px;">
            <div style="
                width: 40px;
                height: 40px;
                background: linear-gradient(135deg, #4338ca 0%, #8b5cf6 100%);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: 800;
                font-size: 20px;
                box-shadow: 0 2px 8px rgba(67, 56, 202, 0.3);
            ">R</div>
            <div style="
                font-size: 24px;
                font-weight: 800;
                color: #1e1b4b;
                letter-spacing: -0.5px;
            ">Refundly<span style="color: #8b5cf6;">.ai</span></div>
        </div>
        <div style="
            display: flex;
            align-items: center;
            gap: 12px;
            color: #64748b;
            font-size: 14px;
        ">
            <span>👤 {client_email}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Small action on the right for quick login/register visibility
    with st.container():
        if not st.session_state.get('authenticated', False):
            if st.button("Se connecter / S'inscrire", key="header_auth_btn", width='content'):
                st.session_state.show_portal = True
                st.rerun()
        else:
            if st.button("Mon compte", key="header_account_btn", width='content'):
                st.session_state.active_page = 'Settings'
                st.rerun()
    
    # Professional navigation tab buttons
    st.markdown('<div style="margin: -1rem -1rem 0rem -1rem; background: white; border-bottom: 1px solid #e9ecef;"></div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5, col_spacer = st.columns([1.2, 1.2, 1.2, 1.2, 1.2, 4.8])
    
    pages = [
        ("Dashboard", "📊 Dashboard"),
        ("Upload", "📤 Upload"),
        ("Disputes", "📋 Disputes"),
        ("Reports", "📈 Reports"),
        ("Settings", "⚙️ Settings")
    ]
    
    for col, (page_id, page_label) in zip([col1, col2, col3, col4, col5], pages):
        with col:
            is_active = st.session_state.active_page == page_id
            if st.button(
                page_label,
                key=f"nav_{page_id}",
                width='stretch',
                type="primary" if is_active else "secondary"
            ):
                st.session_state.active_page = page_id
                st.rerun()
    
    st.markdown('<div style="margin: 0rem -1rem 2rem -1rem;"></div>', unsafe_allow_html=True)
    
    return st.session_state.active_page


def render_disputes_table_modern(disputes_df):
    """
    Render disputes table matching mockup design exactly with functional buttons.
    
    Args:
        disputes_df (pd.DataFrame): DataFrame containing disputes data.
    """
    st.markdown('<div class="section-header">Recent Delivery Disputes</div>', unsafe_allow_html=True)
    
    if disputes_df.empty:
        st.info("✨ Aucun litige détecté actuellement. C'est une bonne nouvelle !")
        return
    
    # Prepare data
    carriers_info = {
        'UPS': {'logo': '🟫', 'name': 'UPS'},
        'DHL': {'logo': '🟨', 'name': 'DHL'},
        'FedEx': {'logo': '🟪', 'name': 'FedEx'},
        'USPS': {'logo': '🟦', 'name': 'USPS'},
        'DPD': {'logo': '🟥', 'name': 'DPD'},
        'Chronopost': {'logo': '🔵', 'name': 'Chronopost'},
        'Colissimo': {'logo': '⚪', 'name': 'Colissimo'}
    }
    
    status_configs = {
        'Processing': {'class': 'status-processing', 'label': 'Processing'},
        'Under Review': {'class': 'status-review', 'label': 'Under Review'},
        'Awaiting Carrier': {'class': 'status-awaiting', 'label': 'Awaiting Carrier'},
        'Pending': {'class': 'status-pending', 'label': 'Pending'}
    }
    
    # Start table
    st.markdown("""
    <div class="disputes-table">
        <div class="table-header">
            <div>Carrier</div>
            <div>AI Confidence</div>
            <div>Estimated Refund Date</div>
            <div>Status</div>
            <div>Actions</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Render each row with functional buttons
    for idx, row in disputes_df.head(5).iterrows():
        carrier = row.get('carrier', 'UPS')
        carrier_info = carriers_info.get(carrier, {'logo': '📦', 'name': carrier})
        
        # Calculate AI confidence (simulation based on data)
        confidence = min(98, 60 + (idx * 7) % 35)
        confidence_color = '#4338ca' if confidence >= 90 else ('#10b981' if confidence >= 75 else '#f59e0b')
        confidence_icon = '✓' if confidence >= 90 else ('⚠️' if confidence < 75 else '')
        
        # Generate realistic date
        refund_date = (datetime.now() + timedelta(days=15 + idx * 3)).strftime('%b %d, %Y')
        
        # Status
        statuses = list(status_configs.keys())
        status = statuses[idx % len(statuses)]
        status_config = status_configs[status]
        
        # Create row container
        st.markdown('<div class="table-row" style="display: grid; grid-template-columns: 1fr 2fr 1.2fr 1fr 1.5fr; align-items: center; padding: 16px; border-bottom: 1px solid #f1f5f9;">', unsafe_allow_html=True)
        
        # Use columns for interactive layout
        col1, col2, col3, col4, col5 = st.columns([1, 2, 1.2, 1, 1.5])
        
        with col1:
            # Rendre le nom du transporteur cliquable
            carrier_name = carrier_info['name']
            if st.button(
                f"{carrier_info['logo']} {carrier_name}",
                key=f"carrier_link_{idx}_{carrier}",
                type="secondary",
                width='content'
            ):
                # Navigate to carrier overview page
                st.session_state.selected_carrier = carrier
                st.session_state.active_page = 'Carrier Overview'
                st.rerun()
        
        with col2:
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-weight: 700; color: #4338ca; min-width: 40px;">{confidence}%</span>
                <div style="flex: 1; height: 8px; background: #f1f5f9; border-radius: 99px; overflow: hidden;">
                    <div style="width: {confidence}%; height: 100%; background: {confidence_color}; transition: width 0.3s;"></div>
                </div>
                <span style="font-size: 18px;">{confidence_icon}</span>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f'<div style="color: #64748b; font-weight: 500; text-align: center;">{refund_date}</div>', unsafe_allow_html=True)
        
        with col4:
            badge_colors = {
                'status-processing': 'background: #dbeafe; color: #1e40af;',
                'status-review': 'background: #fed7aa; color: #c2410c;',
                'status-awaiting': 'background: #e9d5ff; color: #6b21a8;',
                'status-pending': 'background: #f1f5f9; color: #475569;'
            }
            badge_style = badge_colors.get(status_config['class'], '')
            st.markdown(f'<div style="text-align: center;"><span style="padding: 6px 14px; border-radius: 12px; font-size: 12px; font-weight: 600; {badge_style}">{status_config["label"]}</span></div>', unsafe_allow_html=True)
        
        with col5:
            # Functional Streamlit buttons with real data
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button(f"👁️ {get_i18n_text('btn_view')}", key=f"view_btn_{idx}", width='stretch'):
                    # Navigate to dispute details page with real data
                    st.session_state.selected_dispute = {
                        'dispute_id': row.get('dispute_id', f'DSP-{idx:03d}'),
                        'order_id': row.get('order_id', f'ORD-{1000+idx}'),
                        'tracking_number': row.get('tracking_number', f'TRK{idx:08d}'),
                        'carrier': carrier,
                        'dispute_type': row.get('dispute_type', 'unknown'),
                        'amount': row.get('total_recoverable', 0),
                        'status': row.get('status', 'pending'),
                        'probability_success': confidence,
                        'customer_email': st.session_state.get('client_email', ''),
                        'customer_name': row.get('customer_name', 'N/A'),
                        'delivery_address': row.get('delivery_address', 'N/A'),
                        'order_date': row.get('created_at', 'N/A'),
                    }
                    st.session_state.active_page = 'Dispute Details'
                    st.rerun()
            with btn_col2:
                action_type = 'escalate' if idx % 2 == 0 else 'archive'
                if action_type == 'escalate':
                    action_label = f'⚡ {get_i18n_text("btn_escalate")}'
                else:
                    action_label = f'📁 {get_i18n_text("btn_archive")}'
                
                if st.button(action_label, key=f"action_btn_{idx}", width='stretch'):
                    if action_type == 'escalate':
                        st.toast(f"⚡ {get_i18n_text('btn_escalate')}...")
                    else:
                        st.toast(f"📁 {get_i18n_text('btn_archive')}...")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Close table
    st.markdown('</div>', unsafe_allow_html=True)


def render_analytics_tab(disputes_df):
    """
    Render advanced analytics tab.
    
    Args:
        disputes_df (pd.DataFrame): DataFrame containing disputes data.
    """
    st.markdown("### 📊 Analytics")
    st.info("Advanced analytics and insights about your disputes")
    
    if disputes_df.empty:
        st.warning("No data available for analytics")
        return
    
    # Placeholder for analytics - extend as needed
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Disputes", len(disputes_df))
    
    with col2:
        st.metric("Total Recoverable", f"{disputes_df['total_recoverable'].sum():,.2f} EUR")


def render_history_tab():
    """Render the full history of processed claims for the client."""
    st.markdown("### 📜 History")
    st.info("View your complete claim history")
    
    # Placeholder - extend as needed
    st.caption("No historical data available yet")


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
