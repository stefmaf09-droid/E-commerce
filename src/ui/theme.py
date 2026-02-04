"""
Premium Theme Module - Refundly.ai Design System (Mockup Match)
Palette: Lavande + Indigo
"""

import streamlit as st

def apply_premium_theme():
    """Apply the Refundly.ai premium theme with lavender/indigo color scheme."""
    st.markdown("""
    <style>
    /* ===== GLOBAL RESET & BACKGROUND ===== */
    .main, .block-container {
        padding-top: 0rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 1400px !important;
    }
    
    body, .stApp {
        background: linear-gradient(135deg, #faf9fc 0%, #f5f3ff 100%) !important;
        font-family: 'Inter', 'Segoe UI', system-ui, sans-serif !important;
    }
    
    /* Geometric background pattern */
    .stApp::before {
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        z-index: -1;
        opacity: 0.3;
        background-image: 
            linear-gradient(30deg, #e0e7ff 12%, transparent 12.5%, transparent 87%, #e0e7ff 87.5%, #e0e7ff),
            linear-gradient(150deg, #e0e7ff 12%, transparent 12.5%, transparent 87%, #e0e7ff 87.5%, #e0e7ff),
            linear-gradient(30deg, #e0e7ff 12%, transparent 12.5%, transparent 87%, #e0e7ff 87.5%, #e0e7ff),
            linear-gradient(150deg, #e0e7ff 12%, transparent 12.5%, transparent 87%, #e0e7ff 87.5%, #e0e7ff);
        background-size: 80px 140px;
        background-position: 0 0, 0 0, 40px 70px, 40px 70px;
    }

    /* ===== NAVIGATION HEADER ===== */
    .nav-header {
        background: white;
        padding: 16px 32px;
        margin: -2rem -2rem 2rem -2rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 2px 8px rgba(67, 56, 202, 0.08);
        border-bottom: 1px solid #e0e7ff;
    }
    
    .nav-logo {
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 24px;
        font-weight: 800;
        color: #1e1b4b;
    }
    
    .logo-icon {
        width: 40px;
        height: 40px;
        background: linear-gradient(135deg, #4338ca 0%, #6366f1 100%);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 20px;
    }
    
    .nav-menu {
        display: flex;
        gap: 40px;
    }
    
    .nav-item {
        color: #64748b;
        text-decoration: none;
        font-weight: 600;
        font-size: 15px;
        padding: 8px 0px;
        border-bottom: 3px solid transparent;
        transition: all 0.2s ease;
    }
    
    .nav-item:hover {
        color: #4338ca;
        border-bottom-color: #c7d2fe;
    }
    
    .nav-item.active {
        color: #4338ca;
        border-bottom-color: #4338ca;
    }
    
    .nav-user {
        width: 40px;
        height: 40px;
        background: #f1f5f9;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .nav-user:hover {
        background: #e0e7ff;
        transform: scale(1.05);
    }

    /* ===== KPI CARDS (MOCKUP MATCH) ===== */
    .kpi-cards-container {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 24px;
        margin-bottom: 32px;
    }
    
    .kpi-card {
        background: white;
        border: 2px solid #e0e7ff;
        border-radius: 16px;
        padding: 28px 24px;
        text-align: left;
        box-shadow: 0 2px 12px rgba(67, 56, 202, 0.06);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .kpi-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(67, 56, 202, 0.12);
        border-color: #c7d2fe;
    }
    
    .kpi-card-icon {
        font-size: 42px;
        margin-bottom: 16px;
        display: block;
    }
    
    .kpi-card-label {
        font-size: 13px;
        color: #64748b;
        font-weight: 600;
        margin-bottom: 4px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .kpi-card-value {
        font-size: 36px;
        font-weight: 800;
        color: #1e1b4b;
        margin-bottom: 8px;
        line-height: 1;
    }
    
    .kpi-card-subtitle {
        font-size: 13px;
        color: #94a3b8;
        margin-bottom: 16px;
    }
    
    .kpi-progress-bar {
        width: 100%;
        height: 6px;
        background: #f1f5f9;
        border-radius: 10px;
        overflow: hidden;
        margin-top: 12px;
    }
    
    .kpi-progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #4338ca 0%, #6366f1 100%);
        border-radius: 10px;
        transition: width 0.6s ease;
    }

    /* ===== SECTION HEADERS ===== */
    .section-header {
        font-size: 20px;
        font-weight: 700;
        color: #1e1b4b;
        margin: 32px 0 16px 0;
        padding-bottom: 8px;
    }

    /* ===== DISPUTES TABLE (MOCKUP MATCH) ===== */
    .disputes-table {
        background: white;
        border-radius: 16px;
        padding: 0px;
        box-shadow: 0 2px 12px rgba(67, 56, 202, 0.06);
        overflow: hidden;
    }
    
    .table-header {
        background: #faf9fc;
        padding: 16px 24px;
        display: grid;
        grid-template-columns: 180px 200px 180px 150px 180px;
        gap: 16px;
        font-size: 13px;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border-bottom: 2px solid #f1f5f9;
    }
    
    .table-row {
        padding: 20px 24px;
        display: grid;
        grid-template-columns: 180px 200px 180px 150px 180px;
        gap: 16px;
        align-items: center;
        border-bottom: 1px solid #f1f5f9;
        transition: all 0.2s ease;
    }
    
    .table-row:nth-child(even) {
        background: #faf8ff;
    }
    
    .table-row:hover {
        background: #f5f3ff;
        transform: scale(1.01);
    }
    
    .carrier-cell {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .carrier-logo {
        width: 40px;
        height: 40px;
        object-fit: contain;
    }
    
    .carrier-name {
        font-weight: 600;
        color: #1e1b4b;
        font-size: 15px;
    }
    
    .confidence-cell {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .confidence-pct {
        font-weight: 700;
        color: #4338ca;
        min-width: 40px;
        font-size: 14px;
    }
    
    .confidence-bar-container {
        flex: 1;
        height: 8px;
        background: #f1f5f9;
        border-radius: 10px;
        overflow: hidden;
    }
    
    .confidence-bar-fill {
        height: 100%;
        border-radius: 10px;
        transition: width 0.4s ease;
    }
    
    .confidence-icon {
        font-size: 18px;
    }
    
    .date-cell {
        color: #64748b;
        font-size: 14px;
        font-weight: 500;
    }
    
    .status-badge {
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
        text-align: center;
        display: inline-block;
    }
    
    .status-processing {
        background: #dbeafe;
        color: #1e40af;
    }
    
    .status-review {
        background: #fed7aa;
        color: #c2410c;
    }
    
    .status-awaiting {
        background: #e9d5ff;
        color: #6b21a8;
    }
    
    .status-pending {
        background: #f1f5f9;
        color: #475569;
    }
    
    .actions-cell {
        display: flex;
        gap: 8px;
    }
    
    .action-btn {
        padding: 6px 12px;
        border-radius: 8px;
        font-size: 12px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
        display: inline-flex;
        align-items: center;
        gap: 4px;
        border: 1px solid;
        background: white;
    }
    
    .btn-view {
        color: #4338ca;
        border-color: #c7d2fe;
    }
    
    .btn-view:hover {
        background: #f5f3ff;
        border-color: #4338ca;
    }
    
    .btn-escalate {
        color: #f59e0b;
        border-color: #fcd34d;
    }
    
    .btn-escalate:hover {
        background: #fef3c7;
        border-color: #f59e0b;
    }
    
    .btn-archive {
        color: #64748b;
        border-color: #e2e8f0;
    }
    
    .btn-archive:hover {
        background: #f8fafc;
        border-color: #94a3b8;
    }

    /* ===== STREAMLIT COMPONENT OVERRIDES ===== */
    .stButton button {
        background: linear-gradient(135deg, #4338ca 0%, #6366f1 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 12px 24px !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 12px rgba(67, 56, 202, 0.2) !important;
    }
    
    .stButton button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(67, 56, 202, 0.3) !important;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Tabs styling (if used) */
    .stTabs {
        background: transparent !important;
        margin-top: 0px !important;
    }
    
    [data-testid="stTab"] {
        background: white !important;
        border: 2px solid #e0e7ff !important;
        color: #64748b !important;
        font-weight: 700 !important;
        border-radius: 10px 10px 0 0 !important;
        padding: 12px 24px !important;
        margin-right: 4px !important;
    }
    
    [data-testid="stTab"][aria-selected="true"] {
        background: white !important;
        color: #4338ca !important;
        border-bottom-color: white !important;
    }
    
    /* Input fields */
    .stTextInput input, .stSelectbox select {
        border: 2px solid #e0e7ff !important;
        border-radius: 10px !important;
        padding: 12px !important;
        font-size: 14px !important;
        transition: all 0.2s ease !important;
    }
    
    .stTextInput input:focus, .stSelectbox select:focus {
        border-color: #4338ca !important;
        box-shadow: 0 0 0 3px rgba(67, 56, 202, 0.1) !important;
    }
    
    /* Metrics (Streamlit native) */
    [data-testid="stMetricValue"] {
        font-size: 32px !important;
        font-weight: 800 !important;
        color: #4338ca !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #64748b !important;
        font-weight: 600 !important;
    }
    
    /* Sidebar (optional, si utilisé) */
    section[data-testid="stSidebar"] {
        background: white !important;
        border-right: 2px solid #f1f5f9 !important;
    }
    
    /* Alerts/Info boxes */
    .stAlert {
        background: #f5f3ff !important;
        border-left: 4px solid #4338ca !important;
        border-radius: 10px !important;
        padding: 16px !important;
    }
    
    </style>
    """, unsafe_allow_html=True)


def render_premium_metric(label, value, subtext="", icon="💰", progress=75, color="indigo"):
    """
    Render a premium KPI card matching the mockup design.
    
    Args:
        label: Metric label (e.g., "Recoverable")
        value: Main value to display
        subtext: Subtitle/description
        icon: Emoji icon
        progress: Progress bar percentage (0-100)
        color: Color theme (not used in new design, keeping for compatibility)
    """
    html = f"""
    <div class="kpi-card">
        <span class="kpi-card-icon">{icon}</span>
        <div class="kpi-card-label">{label}</div>
        <div class="kpi-card-value">{value}</div>
        <div class="kpi-card-subtitle">{subtext}</div>
        <div class="kpi-progress-bar">
            <div class="kpi-progress-fill" style="width: {progress}%;"></div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_premium_info(text, icon="ℹ️"):
    """
    Render a premium info box.
    """
    html = f"""
    <div style="background: #e0e7ff; border-left: 4px solid #4338ca; padding: 16px; border-radius: 8px; font-size: 14px; color: #1e1b4b; display: flex; align-items: center; gap: 12px; margin-top: 24px;">
        <span style="font-size: 20px;">{icon}</span>
        <span>{text}</span>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
