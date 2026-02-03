
import streamlit as st

def apply_premium_theme():
    """Applique la version absolue 'Trait pour Trait' Elite UI."""
    st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* Background Pattern & Reset */
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', sans-serif;
        background-color: #f8fafc;
        color: #1e293b;
    }
    
    [data-testid="stHeader"], header {
        display: none !important;
    }
    
    [data-testid="block-container"] {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 1300px !important;
    }

    /* Main Container Card */
    .elite-container-card {
        background: #ffffff;
        border-radius: 24px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.03);
        padding: 40px;
        margin: 0 auto;
        border: 1px solid #edf2f7;
    }

    /* Absolute Mockup Header */
    .elite-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 30px;
        padding-bottom: 20px;
        border-bottom: 1px solid #f1f5f9;
    }

    .header-logo-group {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .header-logo-text {
        font-size: 1.8rem;
        font-weight: 800;
        color: #1e293b;
        letter-spacing: -0.04em;
    }

    /* --- ACTIVE NAVIGATION (st.tabs Styling) --- */
    .stTabs {
        background: transparent !important;
        margin-top: 0px !important; /* Reset to prevent overlap with title */
        z-index: 100;
        position: relative;
    }

    [data-testid="stActiveTabIndicator"] {
        background-color: #4338ca !important;
        height: 4px !important;
        border-radius: 10px !important;
        bottom: 2px !important;
    }

    [data-testid="stTab"] {
        background-color: transparent !important;
        border: none !important;
        color: #64748b !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        padding: 5px 25px !important;
        margin: 0 10px !important;
        transition: all 0.2s ease !important;
    }

    [data-testid="stTab"]:hover {
        color: #4338ca !important;
        background: transparent !important;
        transform: translateY(-2px);
    }

    [data-testid="stTab"][aria-selected="true"] {
        color: #4338ca !important;
        font-weight: 800 !important;
    }

    /* Centering the Tabs */
    [data-testid="stTabList"] {
        justify-content: center !important;
        gap: 20px !important;
        border: none !important;
        background: transparent !important;
        padding-top: 10px !important;
    }

    /* Header Minimal Branding (Logo placement) */
    .elite-header-minimal {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0;
        margin-bottom: 20px;
        position: relative;
        z-index: 50;
    }

    .header-profile {
        transition: transform 0.2s;
        cursor: pointer;
    }

    .header-profile:hover {
        transform: scale(1.1);
    }

    /* Active Table Buttons (st.button styling) */
    .stButton > button {
        background: #ffffff !important;
        color: #1e293b !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
        padding: 4px 12px !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        transition: all 0.2s !important;
        height: 32px !important;
        line-height: 1 !important;
    }

    .stButton > button:hover {
        border-color: #4338ca !important;
        color: #4338ca !important;
        background: #f8fafc !important;
        box-shadow: 0 4px 12px rgba(67, 56, 202, 0.1);
    }

    [data-testid="column"] {
        display: flex !important;
        align-items: center !important;
        justify-content: flex-end !important;
        gap: 8px !important;
    }

    /* KPI Cards - Mockup Precision */
    .elite-kpi-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 24px;
        margin-bottom: 40px;
    }

    .elite-kpi-card {
        border: 2px solid #eef2ff;
        border-radius: 20px;
        padding: 24px;
        position: relative;
        background: #fff;
        height: 190px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: transform 0.2s, border-color 0.2s;
    }
    
    .elite-kpi-card:first-child { border-color: #4338ca; }

    .kpi-bg-icon {
        position: absolute;
        right: 15px;
        top: 15px;
        font-size: 5rem;
        opacity: 0.04;
        filter: grayscale(1);
    }

    .kpi-content {
        position: relative;
        z-index: 1;
    }

    .kpi-label-row {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 12px;
    }

    .kpi-mini-icon {
        font-size: 1.1rem;
    }

    .kpi-label {
        font-size: 0.85rem;
        font-weight: 700;
        color: #1e293b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .kpi-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1e293b;
        letter-spacing: -0.02em;
    }
    
    .elite-kpi-card:first-child .kpi-value { color: #4338ca; }

    .kpi-sub {
        font-size: 0.9rem;
        color: #64748b;
        font-weight: 500;
    }

    .kpi-progress {
        height: 7px;
        background: #f1f5f9;
        border-radius: 10px;
        width: 100%;
        overflow: hidden;
    }

    .kpi-progress-fill {
        height: 100%;
        background: #4338ca;
        border-radius: 10px;
    }

    /* Table Mockup Style */
    .elite-table-header {
        background: #f8fafc;
        border-radius: 8px;
        padding: 14px 24px;
        display: flex;
        font-size: 0.75rem;
        font-weight: 800;
        color: #94a3b8;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 8px;
    }

    .elite-row {
        display: flex;
        align-items: center;
        padding: 16px 24px;
        border-bottom: 1px solid #f1f5f9;
        transition: background 0.2s;
        border-radius: 12px;
    }

    .elite-row:hover {
        background: #f8fafc;
    }

    .carrier-logo-box {
        width: 32px;
        height: 32px;
        border-radius: 6px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #fff;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    .confidence-bar-container {
        display: flex;
        align-items: center;
        gap: 15px;
        flex: 1;
    }

    .confidence-bar {
        height: 6px;
        background: #f1f5f9;
        border-radius: 10px;
        flex: 1;
        overflow: hidden;
        max-width: 300px;
    }

    .confidence-fill {
        height: 100%;
        background: #4338ca;
        border-radius: 10px;
    }

    .status-pill {
        padding: 6px 14px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 700;
        background: #f1f5f9;
        color: #475569;
    }

    /* Sidebar Clean */
    [data-testid="stSidebar"] {
        background-color: white !important;
        border-right: 1px solid #f1f5f9;
    }
</style>
""", unsafe_allow_html=True)

def render_premium_metric(label, value, subtext="", icon="💰", mini_icon=None, progress=75, color=None):
    """Rendu d'une carte métrique premium (Style Elite Mockup)."""
    if mini_icon is None:
        mini_icon = icon
    
    # Map color names to hex if provided, otherwise use default
    color_map = {
        'emerald': '#10b981',
        'indigo': '#6366f1',
        'sky': '#0ea5e9',
        'rose': '#f43f5e',
        'amber': '#f59e0b'
    }
    fill_color = color_map.get(color, '#4338ca')
    
    st.markdown(f"""
    <div class="elite-kpi-card">
        <div class="kpi-bg-icon">{icon}</div>
        <div class="kpi-content">
            <div class="kpi-label-row">
                <span class="kpi-mini-icon">{mini_icon}</span>
                <span class="kpi-label">{label.upper()}</span>
            </div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-sub">{subtext}</div>
        </div>
        <div class="kpi-progress">
            <div class="kpi-progress-fill" style="width: {progress}%; background-color: {fill_color};"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_premium_info(message, icon="💡"):
    """Rendu d'un bloc d'information premium."""
    st.markdown(f"""
    <div style="background: #f8fafc; border: 1px solid #edf2f7; border-radius: 16px; padding: 20px; display: flex; gap: 16px; align-items: center;">
        <div style="font-size: 1.5rem;">{icon}</div>
        <div style="color: #475569; font-size: 0.95rem;">{message}</div>
    </div>
    """, unsafe_allow_html=True)
