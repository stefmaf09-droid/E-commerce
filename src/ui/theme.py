"""
Premium Theme Module - Refundly.ai Design System
Palette: Teal / Vert Émeraude (#0d9488)
"""

import streamlit as st

# ── Tokens couleurs ────────────────────────────────────────────────────────────
PRIMARY       = "#0d9488"
PRIMARY_DARK  = "#0f766e"
PRIMARY_LIGHT = "#ccfbf1"
PRIMARY_GLOW  = "rgba(13, 148, 136, 0.18)"
BG_GRADIENT   = "linear-gradient(180deg, #f0fdf9 0%, #f0f9ff 60%, #eff6ff 100%)"
TEXT_DARK     = "#111827"
TEXT_MUTED    = "#6b7280"
BORDER        = "#e5e7eb"

def apply_premium_theme():
    """Applique le thème Refundly Teal sur toute l'application."""
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

    /* ===== GLOBAL ===== */
    html, body, .stApp {{
        font-family: 'Inter', 'Segoe UI', system-ui, sans-serif !important;
        background: {BG_GRADIENT} !important;
        color: {TEXT_DARK} !important;
    }}

    .main, .block-container {{
        padding-top: 0rem !important;
        padding-left: 2.5rem !important;
        padding-right: 2.5rem !important;
        max-width: 1400px !important;
    }}

    /* Hide Streamlit chrome */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}

    /* ===== SIDEBAR OFF ===== */
    [data-testid="stSidebar"] {{
        display: none !important;
    }}
    [data-testid="stSidebarCollapseButton"] {{
        display: none !important;
    }}
    /* Reclaim the full width when sidebar is hidden */
    .main .block-container {{
        padding-left: 2.5rem !important;
    }}

    /* ===== TOP NAVBAR ===== */
    .app-navbar {{
        position: sticky;
        top: 0;
        z-index: 1000;
        background: rgba(255,255,255,0.95);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-bottom: 1px solid {BORDER};
        box-shadow: 0 2px 16px rgba(0,0,0,0.06);
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 32px;
        height: 64px;
        margin: 0 -2.5rem 2rem -2.5rem;
    }}
    .app-navbar-logo {{
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 1.25rem;
        font-weight: 800;
        color: {TEXT_DARK};
        text-decoration: none;
        flex-shrink: 0;
    }}
    .app-navbar-logo-icon {{
        width: 34px;
        height: 34px;
        background: linear-gradient(135deg, {PRIMARY}, {PRIMARY_DARK});
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 900;
        font-size: 16px;
    }}
    .app-navbar-tabs {{
        display: flex;
        align-items: center;
        gap: 2px;
    }}
    .app-nav-tab {{
        padding: 8px 16px;
        border-radius: 8px;
        font-size: 0.88rem;
        font-weight: 600;
        color: {TEXT_MUTED};
        cursor: pointer;
        transition: all 0.2s;
        border: none;
        background: transparent;
        white-space: nowrap;
    }}
    .app-nav-tab:hover {{
        color: {PRIMARY};
        background: {PRIMARY_LIGHT};
    }}
    .app-nav-tab.active {{
        color: {PRIMARY_DARK};
        background: {PRIMARY_LIGHT};
        font-weight: 700;
    }}
    .app-navbar-right {{
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 0.85rem;
        color: {TEXT_MUTED};
        flex-shrink: 0;
    }}
    .app-navbar-avatar {{
        width: 34px;
        height: 34px;
        background: {PRIMARY_LIGHT};
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
        font-weight: 700;
        color: {PRIMARY_DARK};
    }}

    /* ===== KPI CARDS ===== */
    .kpi-cards-container {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 20px;
        margin-bottom: 32px;
    }}
    .kpi-card {{
        background: white;
        border: 1px solid {BORDER};
        border-radius: 16px;
        padding: 24px;
        text-align: left;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
        transition: all 0.25s ease;
        position: relative;
        overflow: hidden;
    }}
    .kpi-card:hover {{
        transform: translateY(-3px);
        box-shadow: 0 8px 24px {PRIMARY_GLOW};
        border-color: {PRIMARY_LIGHT};
    }}
    .kpi-card-icon {{
        font-size: 2.4rem;
        margin-bottom: 12px;
        display: block;
    }}
    .kpi-card-label {{
        font-size: 0.75rem;
        color: {TEXT_MUTED};
        font-weight: 600;
        margin-bottom: 4px;
        text-transform: uppercase;
        letter-spacing: 0.6px;
    }}
    .kpi-card-value {{
        font-size: 2.2rem;
        font-weight: 800;
        color: {TEXT_DARK};
        margin-bottom: 6px;
        line-height: 1;
    }}
    .kpi-card-subtitle {{
        font-size: 0.8rem;
        color: #9ca3af;
        margin-bottom: 14px;
    }}
    .kpi-progress-bar {{
        width: 100%;
        height: 5px;
        background: #f3f4f6;
        border-radius: 10px;
        overflow: hidden;
        margin-top: 10px;
    }}
    .kpi-progress-fill {{
        height: 100%;
        background: linear-gradient(90deg, {PRIMARY}, {PRIMARY_DARK});
        border-radius: 10px;
        transition: width 0.6s ease;
    }}

    /* ===== SECTION HEADERS ===== */
    .section-header {{
        font-size: 1.15rem;
        font-weight: 700;
        color: {TEXT_DARK};
        margin: 28px 0 14px 0;
        padding-bottom: 6px;
    }}

    /* ===== DISPUTES TABLE ===== */
    .disputes-table {{
        background: white;
        border-radius: 16px;
        padding: 0;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
        overflow: hidden;
        border: 1px solid {BORDER};
    }}
    .table-header {{
        background: #f9fafb;
        padding: 14px 24px;
        display: grid;
        grid-template-columns: 180px 200px 180px 150px 180px;
        gap: 16px;
        font-size: 0.75rem;
        font-weight: 700;
        color: {TEXT_MUTED};
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border-bottom: 1px solid {BORDER};
    }}
    .table-row {{
        padding: 18px 24px;
        display: grid;
        grid-template-columns: 180px 200px 180px 150px 180px;
        gap: 16px;
        align-items: center;
        border-bottom: 1px solid #f3f4f6;
        transition: background 0.15s ease;
    }}
    .table-row:nth-child(even) {{
        background: #fafafa;
    }}
    .table-row:hover {{
        background: #f0fdf9;
    }}
    .carrier-cell {{
        display: flex;
        align-items: center;
        gap: 10px;
    }}
    .carrier-name {{
        font-weight: 600;
        color: {TEXT_DARK};
        font-size: 0.9rem;
    }}
    .confidence-pct {{
        font-weight: 700;
        color: {PRIMARY};
        min-width: 40px;
        font-size: 0.85rem;
    }}
    .confidence-bar-container {{
        flex: 1;
        height: 6px;
        background: #f3f4f6;
        border-radius: 10px;
        overflow: hidden;
    }}
    .confidence-bar-fill {{
        height: 100%;
        border-radius: 10px;
    }}
    .date-cell {{
        color: {TEXT_MUTED};
        font-size: 0.85rem;
        font-weight: 500;
    }}
    .status-badge {{
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 700;
        text-align: center;
        display: inline-block;
    }}
    .status-processing {{ background: #dbeafe; color: #1e40af; }}
    .status-review     {{ background: #fed7aa; color: #c2410c; }}
    .status-awaiting   {{ background: #e9d5ff; color: #6b21a8; }}
    .status-pending    {{ background: #f3f4f6; color: #374151; }}
    .status-accepted   {{ background: #dcfce7; color: #166534; }}
    .status-rejected   {{ background: #fee2e2; color: #991b1b; }}
    .actions-cell {{ display: flex; gap: 8px; }}
    .action-btn {{
        padding: 5px 10px;
        border-radius: 8px;
        font-size: 0.75rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s;
        display: inline-flex;
        align-items: center;
        gap: 4px;
        border: 1px solid;
        background: white;
    }}
    .btn-view     {{ color: {PRIMARY}; border-color: {PRIMARY_LIGHT}; }}
    .btn-view:hover {{ background: {PRIMARY_LIGHT}; border-color: {PRIMARY}; }}
    .btn-escalate {{ color: #f59e0b; border-color: #fcd34d; }}
    .btn-escalate:hover {{ background: #fef3c7; border-color: #f59e0b; }}
    .btn-archive  {{ color: {TEXT_MUTED}; border-color: {BORDER}; }}
    .btn-archive:hover {{ background: #f8fafc; border-color: #9ca3af; }}

    /* ===== BUTTONS ===== */
    .stButton > button {{
        background: {PRIMARY} !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 10px 22px !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
        transition: all 0.25s ease !important;
        box-shadow: 0 2px 8px {PRIMARY_GLOW} !important;
    }}
    .stButton > button:hover {{
        background: {PRIMARY_DARK} !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 16px {PRIMARY_GLOW} !important;
    }}

    /* ===== INPUTS ===== */
    .stTextInput input, .stSelectbox select, .stTextArea textarea {{
        border: 1.5px solid {BORDER} !important;
        border-radius: 10px !important;
        font-size: 0.9rem !important;
        transition: all 0.2s !important;
    }}
    .stTextInput input:focus, .stSelectbox select:focus, .stTextArea textarea:focus {{
        border-color: {PRIMARY} !important;
        box-shadow: 0 0 0 3px rgba(13,148,136,0.1) !important;
    }}

    /* ===== TABS ===== */
    .stTabs {{ background: transparent !important; }}
    [data-testid="stTab"] {{
        background: white !important;
        border: 1.5px solid {BORDER} !important;
        color: {TEXT_MUTED} !important;
        font-weight: 600 !important;
        border-radius: 10px 10px 0 0 !important;
        padding: 10px 22px !important;
        margin-right: 4px !important;
    }}
    [data-testid="stTab"][aria-selected="true"] {{
        background: white !important;
        color: {PRIMARY} !important;
        border-bottom-color: white !important;
        border-top: 2px solid {PRIMARY} !important;
    }}

    /* ===== METRICS ===== */
    [data-testid="stMetricValue"] {{
        font-size: 2rem !important;
        font-weight: 800 !important;
        color: {PRIMARY} !important;
    }}
    [data-testid="stMetricLabel"] {{
        color: {TEXT_MUTED} !important;
        font-weight: 600 !important;
    }}

    /* ===== ALERTS ===== */
    .stAlert {{
        background: #f0fdf9 !important;
        border-left: 4px solid {PRIMARY} !important;
        border-radius: 10px !important;
    }}

    /* ===== DATAFRAME ===== */
    [data-testid="stDataFrame"] {{
        border-radius: 12px !important;
        overflow: hidden;
        border: 1px solid {BORDER} !important;
    }}

    /* ===== EXPANDER ===== */
    [data-testid="stExpander"] {{
        border: 1px solid {BORDER} !important;
        border-radius: 12px !important;
        background: white !important;
    }}

    </style>
    """, unsafe_allow_html=True)


def render_premium_metric(label, value, subtext="", icon="💰", progress=75, color="teal"):
    """Render a premium KPI card with teal design."""
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
    """Render a premium info box."""
    html = f"""
    <div style="background:#f0fdf9; border-left:4px solid #0d9488; padding:14px 18px; border-radius:10px; font-size:0.88rem; color:#111827; display:flex; align-items:center; gap:12px; margin-top:20px;">
        <span style="font-size:1.2rem;">{icon}</span>
        <span>{text}</span>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
