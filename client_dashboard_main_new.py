import streamlit as st
import os
import sys
import logging
import pandas as pd

logger = logging.getLogger(__name__)

root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, root_dir)

from src.auth.credentials_manager import CredentialsManager
from src.analytics.metrics_calculator import MetricsCalculator
from src.onboarding.onboarding_manager import OnboardingManager
from onboarding_functions import render_onboarding
from src.ui.theme import apply_premium_theme, render_premium_metric
from src.ui.logos import LOGOS, ICONS
from src.dashboard.auto_refresh import AutoRefresh, setup_auto_refresh
from src.workers.reminder_worker import ReminderWorker

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


# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Refundly.AI | Dashboard",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Navigation items ───────────────────────────────────────────────────────────
MENU_ITEMS = [
    ("🏠", "Dashboard"),
    ("📊", "Analytics"),
    ("📦", "Mes Litiges"),
    ("🗂️", "Gestion"),
    ("💬", "Assistant"),
    ("📄", "Rapports"),
    ("☁️", "Dépôt Preuves"),
    ("⚙️", "Réglages"),
]

# URL-safe page key → display label mapping
PAGE_MAP = {label: label for _, label in MENU_ITEMS}
PAGE_MAP["Admin"] = "Admin"


def _get_active_tab(role: str = "client") -> str:
    """Read active tab from URL query param, falling back to session state."""
    # Accept force-nav from other pages (e.g. assistant_page)
    if "force_menu_selection" in st.session_state:
        tab = st.session_state.pop("force_menu_selection")
        st.query_params["page"] = tab
        return tab

    # Read from URL
    page = st.query_params.get("page", "")
    if page in PAGE_MAP:
        st.session_state.active_tab = page
        return page

    # Fall back to session state
    return st.session_state.get("active_tab", "Dashboard")


def _render_top_navbar(active: str, email: str, role: str = "client"):
    """Render the sticky top navigation bar via st.components (avoids Streamlit iframe sandbox)."""

    items = list(MENU_ITEMS)
    if role == "admin":
        items.append(("👑", "Admin"))

    # Build tab pills HTML
    tabs_html = ""
    for icon, label in items:
        is_active = label == active
        active_style = (
            "color:#0f766e;background:#f0fdf4;font-weight:700;"
            if is_active else "color:#6b7280;background:transparent;"
        )
        safe_label = label.replace(" ", "%20")
        safe_email = email.replace("@", "%40").replace("+", "%2B")
        url = f"?page={safe_label}&token={safe_email}"
        tabs_html += (
            f'<a href="{url}" class="nav-tab" style="{active_style}">'
            f'{icon} {label}</a>'
        )

    initials = email[0].upper() if email else "U"
    safe_email_esc = email.replace("@", "%40").replace("+", "%2B")
    logout_url = f"?logout=1&token={safe_email_esc}"

    navbar_html = f"""<!DOCTYPE html>
<html>
<head>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; font-family:'Inter',sans-serif; }}
  body {{ background:transparent; overflow:hidden; }}
  .navbar {{
    display:flex; align-items:center; justify-content:space-between;
    background:rgba(255,255,255,0.97);
    backdrop-filter:blur(12px);
    border-bottom:1px solid #e5e7eb;
    box-shadow:0 2px 16px rgba(0,0,0,0.06);
    padding:0 28px; height:60px;
    position:fixed; top:0; left:0; right:0; z-index:9999;
  }}
  .logo {{
    display:flex; align-items:center; gap:10px;
    font-size:1.15rem; font-weight:800; color:#111827;
    text-decoration:none; flex-shrink:0;
  }}
  .logo-icon {{
    width:32px; height:32px;
    background:linear-gradient(135deg,#0d9488,#0f766e);
    border-radius:9px; display:flex; align-items:center;
    justify-content:center; color:white; font-weight:900; font-size:15px;
  }}
  .logo .ai {{ color:#0d9488; font-weight:900; }}
  .tabs {{ display:flex; align-items:center; gap:2px; }}
  .nav-tab {{
    padding:7px 13px; border-radius:8px; font-size:0.85rem;
    font-weight:600; text-decoration:none; transition:all 0.15s;
    white-space:nowrap; cursor:pointer;
  }}
  .nav-tab:hover {{ color:#0d9488!important; background:#f0fdf4!important; }}
  .right {{ display:flex; align-items:center; gap:10px; flex-shrink:0; }}
  .email {{ font-size:0.78rem; color:#6b7280; max-width:160px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
  .avatar {{
    width:32px; height:32px; background:#f0fdf4; border-radius:50%;
    display:flex; align-items:center; justify-content:center;
    font-weight:700; font-size:0.9rem; color:#0f766e;
  }}
  .logout {{
    font-size:0.78rem; color:#6b7280; text-decoration:none;
    padding:5px 10px; border:1px solid #e5e7eb; border-radius:7px;
    font-weight:600; transition:all 0.15s;
  }}
  .logout:hover {{ background:#fee2e2; color:#dc2626; border-color:#fca5a5; }}
</style>
</head>
<body>
<nav class="navbar">
  <div class="logo">
    <div class="logo-icon">R</div>
    <span>Refundly<span class="ai">.AI</span></span>
  </div>
  <div class="tabs">
    {tabs_html}
  </div>
  <div class="right">
    <span class="email">{email}</span>
    <div class="avatar">{initials}</div>
    <a href="{logout_url}" class="logout">🚪</a>
  </div>
</nav>
</body>
</html>"""

    # Render via components — has access to window.parent for same-tab navigation
    import streamlit.components.v1 as components
    components.html(navbar_html, height=68, scrolling=False)


def initialize_session():
    """Initialize session state."""
    apply_premium_theme()
    if "env_mode" not in st.session_state:
        st.session_state.env_mode = "TEST"
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = "Dashboard"


def main():
    """Main dashboard application."""
    initialize_session()

    # Handle logout via URL param
    if st.query_params.get("logout") == "1":
        st.session_state.authenticated = False
        st.session_state.active_tab = "Dashboard"
        st.query_params.clear()
        st.rerun()

    # Token auto-reconnect
    email_param = st.query_params.get("token", "")
    if email_param and not st.session_state.get("authenticated"):
        # Let authenticate() handle the auto-login via query_params
        pass
    elif st.session_state.get("authenticated") and "token" not in st.query_params:
        client_email = st.session_state.get("client_email", "")
        if client_email:
            page = st.session_state.get("active_tab", "Dashboard")
            st.query_params["token"] = client_email
            st.query_params["page"] = page

    # Auth gate
    if not authenticate():
        return

    # Start reminder worker once
    if not st.session_state.get("reminder_worker_started"):
        try:
            worker = ReminderWorker.get_instance()
            worker.start_background()
            st.session_state.reminder_worker_started = True
        except Exception as e:
            logger.warning(f"ReminderWorker non démarré: {e}")

    # Detail sub-pages (no navbar needed)
    sub_page = st.session_state.get("active_page", "")
    if sub_page == "Dispute Details":
        from src.dashboard.dispute_details_page import render_dispute_details_page
        render_dispute_details_page(st.session_state.get("selected_dispute", {}))
        return
    elif sub_page == "Carrier Overview":
        from src.dashboard.carrier_overview_page import render_carrier_overview_page
        render_carrier_overview_page(st.session_state.get("selected_carrier", "Unknown"))
        return

    # Onboarding
    onboarding_manager = OnboardingManager()
    client_email = st.session_state.get("client_email", "")
    if not onboarding_manager.is_onboarding_complete(client_email):
        render_onboarding(client_email, onboarding_manager)
        return

    # ── TOP NAVBAR ─────────────────────────────────────────────────────────────
    role = st.session_state.get("role", "client")
    active_tab = _get_active_tab(role)

    # Sync query param
    if st.query_params.get("page") != active_tab:
        st.query_params["page"] = active_tab

    _render_top_navbar(active_tab, client_email, role)

    # ── DATA LOADING ───────────────────────────────────────────────────────────
    from src.database.database_manager import DatabaseManager, set_db_manager

    db_path = os.path.join(
        root_dir,
        "data",
        "test_recours_ecommerce.db" if st.session_state.env_mode == "TEST"
        else "recours_ecommerce.db",
    )

    try:
        db_type_override = "sqlite" if st.session_state.env_mode == "TEST" else None
        db_manager = DatabaseManager(db_path=db_path, db_type=db_type_override)
        set_db_manager(db_manager)
        client = db_manager.get_client(email=client_email)
        client_id = client["id"] if client else None
        claims_data = []
        if client_id:
            for claim in db_manager.get_client_claims(client_id):
                claims_data.append({
                    "claim_reference": claim.get("claim_reference", "N/A"),
                    "order_id": claim.get("order_id", "N/A"),
                    "carrier": claim.get("carrier", "Unknown"),
                    "status": claim.get("status", "pending"),
                    "tracking_number": claim.get("tracking_number", "N/A"),
                    "total_recoverable": claim.get("amount_requested", 0),
                    "accepted_amount": claim.get("accepted_amount", 0),
                    "submitted_at": claim.get("submitted_at", ""),
                    "dispute_type": claim.get("dispute_type", "unknown"),
                    "payment_status": claim.get("payment_status", "unpaid"),
                    "customer_name": claim.get("customer_name", "N/A"),
                    "delivery_address": claim.get("delivery_address", "N/A"),
                    "ai_reason_key": claim.get("ai_reason_key"),
                    "ai_advice": claim.get("ai_advice"),
                })
    except Exception as e:
        st.error(f"❌ **Erreur base de données** : {e}")
        with st.expander("🔧 Actions correctives"):
            st.markdown("""
1. **Mode TEST** : vérifiez que `data/test_recours_ecommerce.db` existe.
2. **Mode RÉEL** : vérifiez `DATABASE_URL` dans `.env`.
""")
        st.stop()

    disputes_df = pd.DataFrame(claims_data)
    total_recoverable = disputes_df["total_recoverable"].sum() if not disputes_df.empty else 0
    disputes_count = len(disputes_df) if not disputes_df.empty else 0
    recovered_amount = 0
    if not disputes_df.empty:
        accepted = disputes_df[disputes_df["status"] == "accepted"]
        recovered_amount = accepted["accepted_amount"].sum() if not accepted.empty else 0
    success_rate = 0
    if total_recoverable > 0 and disputes_count > 0:
        if recovered_amount > 0:
            success_rate = min(int((recovered_amount / total_recoverable) * 100), 100)
        else:
            acc_count = len(disputes_df[disputes_df["status"] == "accepted"])
            success_rate = min(int((acc_count / disputes_count) * 100), 100)
    recoverable_progress = min(int((total_recoverable / 10000) * 100), 100)
    disputes_progress = min(int((disputes_count / 50) * 100), 100)

    # ── PAGE ROUTING ───────────────────────────────────────────────────────────
    if active_tab == "Dashboard":
        if st.session_state.env_mode == "TEST":
            st.markdown(
                '<div style="display:inline-flex;align-items:center;gap:6px;background:#fef3c7;color:#92400e;'
                'padding:4px 14px;border-radius:20px;font-size:0.8rem;font-weight:600;margin-bottom:16px;">'
                '🛠️ Mode Test — données fictives</div>',
                unsafe_allow_html=True,
            )
        st.markdown('<div class="kpi-cards-container">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            render_premium_metric("Récupérable", f"{total_recoverable:,.0f}€",
                                  "Récupération potentielle", icon="💰", progress=recoverable_progress)
        with col2:
            render_premium_metric("Taux de Succès", f"{success_rate}%",
                                  "Basé sur les dossiers clos", icon="🎯", progress=success_rate)
        with col3:
            render_premium_metric("Litiges Actifs", f"{disputes_count:,}",
                                  "En cours de traitement", icon="📦", progress=disputes_progress)
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown('<div style="margin-top:28px;"></div>', unsafe_allow_html=True)
        render_stagnation_escalation_section(disputes_df)
        st.markdown('<div style="margin-top:28px;"></div>', unsafe_allow_html=True)
        render_disputes_table_modern(disputes_df)

    elif active_tab == "Analytics":
        from src.dashboard.analytics_dashboard import render_analytics_dashboard
        render_analytics_dashboard()

    elif active_tab == "Dépôt Preuves":
        from upload_section import render_file_upload
        render_file_upload()

    elif active_tab == "Mes Litiges":
        st.markdown('<div class="section-header">Tous les Litiges</div>', unsafe_allow_html=True)
        render_disputes_table_modern(disputes_df)
        st.markdown("---")
        render_carrier_breakdown(disputes_df)

    elif active_tab == "Gestion":
        from src.dashboard.claims_management_page import render_claims_management
        render_claims_management()

    elif active_tab == "Rapports":
        render_reports_page(disputes_df)

    elif active_tab == "Assistant":
        render_assistant_page()

    elif active_tab == "Pièces Jointes":
        render_attachments_page()

    elif active_tab == "Réglages":
        render_settings_page()

    elif active_tab == "Admin":
        if role != "admin":
            st.error("⛔ Accès refusé.")
            return
        from src.dashboard.admin_panel import render_admin_panel
        render_admin_panel()

    # Auto-refresh
    refresh_interval = st.session_state.get("refresh_interval", 0)
    if st.session_state.get("auto_refresh_enabled", False) and refresh_interval > 0:
        AutoRefresh.auto_refresh_trigger(refresh_interval)


if __name__ == "__main__":
    main()
