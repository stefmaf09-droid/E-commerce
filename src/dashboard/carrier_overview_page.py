"""
Carrier overview page for displaying all disputes with a specific carrier.

This module renders a dedicated page showing statistics and a list of all disputes
for a selected carrier.
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

# Import i18n
from utils.i18n import get_i18n_text


def render_carrier_overview_page(carrier):
    """
    Render carrier overview page with statistics and all disputes.
    
    Args:
        carrier (str): Name of the carrier (e.g., 'Chronopost', 'DHL').
    """
    # Apply premium theme
    from ui.theme import apply_premium_theme
    apply_premium_theme()
    
    # Header avec bouton retour
    _render_carrier_header(carrier)
    
    # Get all disputes for this carrier
    disputes_data = _get_carrier_disputes(carrier)
    
    # Statistics
    _render_carrier_statistics(carrier, disputes_data)
    
    # List of all disputes
    _render_disputes_list(carrier, disputes_data)


def _render_carrier_header(carrier):
    """Render page header with back button and carrier name."""
    col_back, col_title = st.columns([1, 5])
    
    with col_back:
        if st.button(f"← {get_i18n_text('btn_back')}", key="back_to_dashboard_from_carrier", width='stretch'):
            st.session_state.active_page = 'Dashboard'
            st.rerun()
    
    # Get carrier info
    carriers_info = {
        'UPS': {'logo': '🟫', 'color': '#644117'},
        'DHL': {'logo': '🟨', 'color': '#FFCC00'},
        'FedEx': {'logo': '🟪', 'color': '#4D148C'},
        'USPS': {'logo': '🟦', 'color': '#004B87'},
        'DPD': {'logo': '🟥', 'color': '#DC0032'},
        'Chronopost': {'logo': '🔵', 'color': '#003DA5'},
        'Colissimo': {'logo': '⚪', 'color': '#FFCD00'}
    }
    
    carrier_info = carriers_info.get(carrier, {'logo': '📦', 'color': '#6366f1'})
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 24px;
        border-radius: 12px;
        margin: 0 0 24px 0;
        color: white;
    ">
        <h1 style="margin: 0; font-size: 28px; font-weight: 700;">
            {carrier_info['logo']} {carrier} - {get_i18n_text('carrier_overview')}
        </h1>
        <p style="margin: 8px 0 0 0; font-size: 16px; opacity: 0.9;">
            {get_i18n_text('all_disputes_with')} {carrier}
        </p>
    </div>
    """, unsafe_allow_html=True)


def _get_carrier_disputes(carrier):
    """
    Get all disputes for a specific carrier.
    
    Args:
        carrier (str): Carrier name.
        
    Returns:
        pd.DataFrame: DataFrame with all disputes for this carrier.
    """
    # Get client email
    client_email = st.session_state.get('client_email', '')
    
    # Get all claims from database using the correct method
    try:
        from database.database_manager import DatabaseManager
        db = DatabaseManager()
        
        # Get client first to get client_id
        client = db.get_client(email=client_email)
        if not client:
            return pd.DataFrame()
        
        client_id = client['id']
        
        # Get all claims for this client
        claims = db.get_client_claims(client_id)
        
        # Convert to DataFrame format matching dashboard structure
        claims_data = []
        for claim in claims:
            claims_data.append({
                'claim_reference': claim.get('claim_reference', 'N/A'),
                'dispute_id': claim.get('claim_reference', 'N/A'),
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
                'created_at': claim.get('submitted_at', 'N/A')
            })
        
        all_claims_df = pd.DataFrame(claims_data)
        
        # Filter by carrier (case-insensitive)
        if not all_claims_df.empty:
            carrier_claims = all_claims_df[all_claims_df['carrier'].str.lower() == carrier.lower()]
            return carrier_claims
        
        return pd.DataFrame()
        
    except Exception as e:
        print(f"Error fetching carrier disputes: {e}")
        import traceback
        traceback.print_exc()
        # Return empty DataFrame if error
        return pd.DataFrame()


def _render_carrier_statistics(carrier, disputes_df):
    """Render carrier statistics cards."""
    st.markdown(f"### 📊 {get_i18n_text('statistics')}")
    
    if disputes_df.empty:
        st.info(f"No disputes found with {carrier}")
        return
    
    # Calculate statistics
    total_disputes = len(disputes_df)
    total_recoverable = disputes_df['total_recoverable'].sum() if 'total_recoverable' in disputes_df.columns else 0
    
    # Win rate (placeholder - would need 'resolved' status)
    resolved_disputes = disputes_df[disputes_df['status'] == 'resolved'] if 'status' in disputes_df.columns else pd.DataFrame()
    win_rate = (len(resolved_disputes) / total_disputes * 100) if total_disputes > 0 else 0
    
    # Display statistics cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div style="
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            text-align: center;
        ">
            <div style="font-size: 14px; color: #64748b; margin-bottom: 8px;">{get_i18n_text('active_disputes')}</div>
            <div style="font-size: 32px; font-weight: 700; color: #1e293b;">{total_disputes}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            text-align: center;
        ">
            <div style="font-size: 14px; color: #64748b; margin-bottom: 8px;">{get_i18n_text('win_rate')}</div>
            <div style="font-size: 32px; font-weight: 700; color: #10b981;">{win_rate:.0f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            text-align: center;
        ">
            <div style="font-size: 14px; color: #64748b; margin-bottom: 8px;">{get_i18n_text('total_recoverable')}</div>
            <div style="font-size: 32px; font-weight: 700; color: #4338ca;">€{total_recoverable:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)


def _render_disputes_list(carrier, disputes_df):
    """Render list of all disputes for this carrier."""
    st.markdown("---")
    st.markdown(f"### 📋 All {carrier} Disputes")
    
    if disputes_df.empty:
        return
    
    # Render each dispute
    for idx, row in disputes_df.iterrows():
        _render_dispute_card(idx, row, carrier)


def _render_dispute_card(idx, dispute_row, carrier):
    """Render a single dispute card."""
    # Get dispute data
    dispute_id = dispute_row.get('dispute_id', f'DSP-{idx:03d}')
    order_id = dispute_row.get('order_id', f'ORD-{1000+idx}')
    tracking_number = dispute_row.get('tracking_number', 'N/A')
    dispute_type = dispute_row.get('dispute_type', 'unknown')
    total_recoverable = dispute_row.get('total_recoverable', 0)
    status = dispute_row.get('status', 'pending')
    
    # Format dispute type
    dispute_types = {
        'delayed_delivery': 'Delayed delivery',
        'lost_package': 'Lost package',
        'damaged_package': 'Damaged package',
        'invalid_pod': 'Invalid POD',
        'unknown': 'Unknown issue'
    }
    dispute_type_label = dispute_types.get(dispute_type, dispute_type)
    
    # AI confidence (mock)
    ai_confidence = min(98, 65 + (idx * 5) % 30)
    
    # Status badge
    status_badges = {
        'pending': ('⏳ Pending', '#f59e0b'),
        'processing': ('🔄 Processing', '#3b82f6'),
        'under_review': ('📋 Under Review', '#f59e0b'),
        'resolved': ('✅ Resolved', '#10b981'),
        'rejected': ('❌ Rejected', '#ef4444')
    }
    status_label, status_color = status_badges.get(status, ('Unknown', '#6b7280'))
    
    # Create card
    st.markdown(f"""
    <div style="
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        margin-bottom: 16px;
    ">
        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
            <div>
                <h4 style="margin: 0 0 4px 0; font-size: 18px; font-weight: 700; color: #1e293b;">
                    #{dispute_id}
                </h4>
                <p style="margin: 0; color: #64748b; font-size: 14px;">
                    Order #{order_id} • {tracking_number}
                </p>
            </div>
            <div style="
                padding: 6px 14px;
                background: {status_color}20;
                color: {status_color};
                border-radius: 8px;
                font-size: 12px;
                font-weight: 600;
            ">{status_label}</div>
        </div>
        <p style="margin: 0 0 12px 0; color: #475569;">
            {dispute_type_label} • €{total_recoverable:.2f} • {ai_confidence}% AI Confidence
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Action buttons
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col1:
        if st.button(f"👁️ {get_i18n_text('btn_view_details')}", key=f"view_carrier_dispute_{idx}", width='stretch'):
            # Navigate to dispute details page
            st.session_state.selected_dispute = {
                'dispute_id': dispute_row.get('dispute_id', f'DSP-{idx:03d}'),
                'order_id': dispute_row.get('order_id', f'ORD-{1000+idx}'),
                'tracking_number': dispute_row.get('tracking_number', f'TRK{idx:08d}'),
                'carrier': carrier,
                'dispute_type': dispute_row.get('dispute_type', 'unknown'),
                'amount': dispute_row.get('total_recoverable', 0),
                'status': dispute_row.get('status', 'pending'),
                'probability_success': dispute_row.get('probability_success', 85),
                'customer_email': st.session_state.get('client_email', ''),
                'customer_name': dispute_row.get('customer_name', 'N/A'),
                'delivery_address': dispute_row.get('delivery_address', 'N/A'),
                'order_date': dispute_row.get('created_at', 'N/A'),
            }
            st.session_state.active_page = 'Dispute Details'
            st.rerun()
    
    with col2:
        action_label = '⚡ Escalate' if idx % 2 == 0 else '📁 Archive'
        if st.button(action_label, key=f"action_{carrier}_{idx}", width='stretch'):
            st.toast(f"✅ Action performed on #{dispute_id}")
    
    with col3:
        if st.button("📄 PDF", key=f"pdf_{carrier}_{idx}", width='stretch'):
            st.toast(f"📄 Generating PDF for #{dispute_id}...")
