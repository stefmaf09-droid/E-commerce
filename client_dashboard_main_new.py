import streamlit as st
import os
import sys
import pandas as pd
from datetime import datetime, timedelta

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


# Page config
st.set_page_config(
    page_title="Refundly.ai - Customer Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Apply unified premium theme
apply_premium_theme()


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
    from database.database_manager import DatabaseManager
    db_manager = DatabaseManager()
    
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
                'delivery_address': claim.get('delivery_address', 'N/A')
            })
    
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
    active_page = render_navigation_header()
    
    
    # --- PAGE RENDERING BASED ON NAVIGATION ---
    if active_page == 'Dashboard':
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
    
    elif active_page == 'Upload':
        # Upload page
        from upload_section import render_file_upload
        render_file_upload()
    
    elif active_page == 'Disputes':
        # All Disputes page
        st.markdown('<div class="section-header">All Disputes</div>', unsafe_allow_html=True)
        render_disputes_table_modern(disputes_df)
        st.markdown("---")
        render_carrier_breakdown(disputes_df)
    
    elif active_page == 'Reports':
        # Reports & Analytics page
        render_reports_page(disputes_df)
    
    elif active_page == 'Settings':
        # Settings page
        render_settings_page()
    
    elif active_page == 'Email Templates':
        # Email Templates customization page
        from src.dashboard.email_templates_page import render_email_templates_page
        render_email_templates_page()
    
    # Sidebar for controls
    with st.sidebar:
        st.image("static/logo_premium.png", width='stretch')
        st.markdown("""
            <div style="text-align: center; margin-top: -10px; margin-bottom: 20px;">
                <div style="font-size: 1.2rem; font-weight: 800; color: #1e1b4b;">Refundly.ai</div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("### ⚙️ Controls")
        if st.button("🔄 Refresh Data", width='stretch'):
            st.rerun()
        if st.button("🚪 Logout", width='stretch'):
            st.session_state.authenticated = False
            st.rerun()
        st.markdown("---")
        st.caption(f"👤 {st.session_state.client_email}")


if __name__ == "__main__":
    main()
