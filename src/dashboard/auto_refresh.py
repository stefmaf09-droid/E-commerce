"""
Auto-Refresh Component for Streamlit Dashboards

Provides configurable auto-refresh with:
- Toggle ON/OFF
- Interval selection (5s, 10s, 30s, 60s)
- Last update timestamp
- Manual refresh button
- Visual indicators

Usage:
    from src.dashboard.auto_refresh import AutoRefresh
    
    # In your dashboard main()
    refresh_interval = AutoRefresh.render_controls()
    AutoRefresh.manual_refresh_button()
    
    # At end of main()
    if refresh_interval > 0:
        AutoRefresh.auto_refresh_trigger(refresh_interval)
"""

import streamlit as st
import time
from datetime import datetime
from typing import Optional


class AutoRefresh:
    """Smart auto-refresh component for Streamlit dashboards."""
    
    # Default settings
    DEFAULT_ENABLED = True
    DEFAULT_INTERVAL = 30  # seconds
    AVAILABLE_INTERVALS = [5, 10, 30, 60]
    
    @staticmethod
    def initialize_session_state():
        """Initialize session state variables."""
        if 'auto_refresh_enabled' not in st.session_state:
            st.session_state.auto_refresh_enabled = AutoRefresh.DEFAULT_ENABLED
        
        if 'refresh_interval' not in st.session_state:
            st.session_state.refresh_interval = AutoRefresh.DEFAULT_INTERVAL
        
        if 'last_update' not in st.session_state:
            st.session_state.last_update = datetime.now()
        
        if 'refresh_count' not in st.session_state:
            st.session_state.refresh_count = 0
    
    @staticmethod
    def render_controls() -> int:
        """
        Render refresh controls in sidebar.
        
        Returns:
            Current refresh interval in seconds (0 = disabled)
        """
        AutoRefresh.initialize_session_state()
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("### ⏱️ Auto-Actualisation")
        
        # Toggle
        enabled = st.sidebar.toggle(
            "Activer",
            value=st.session_state.auto_refresh_enabled,
            help="Actualise automatiquement les données sans recharger la page",
            key='auto_refresh_toggle_main'
        )
        
        st.session_state.auto_refresh_enabled = enabled
        
        if enabled:
            # Interval selector
            interval = st.sidebar.select_slider(
                "Intervalle de rafraîchissement",
                options=AutoRefresh.AVAILABLE_INTERVALS,
                value=st.session_state.refresh_interval,
                format_func=lambda x: f"{x} secondes" if x > 1 else f"{x} seconde",
                help="Fréquence des mises à jour automatiques",
                key='refresh_interval_slider_main'
            )
            
            st.session_state.refresh_interval = interval
            
            # Status info
            last_update = st.session_state.last_update
            time_ago = (datetime.now() - last_update).total_seconds()
            
            if time_ago < 60:
                time_text = f"il y a {int(time_ago)}s"
            else:
                time_text = f"il y a {int(time_ago / 60)}min"
            
            st.sidebar.caption(f"🕒 Dernière mise à jour: {time_text}")
            st.sidebar.caption(f"🔄 Actualisations: {st.session_state.refresh_count}")
            
            # Next refresh countdown
            next_refresh_in = interval - time_ago
            if next_refresh_in > 0:
                st.sidebar.caption(f"⏳ Prochaine: dans {int(next_refresh_in)}s")
            
            return interval
        else:
            st.sidebar.info("Auto-actualisation désactivée")
            return 0
    
    @staticmethod
    def manual_refresh_button() -> bool:
        """
        Add manual refresh button.
        
        Returns:
            True if button was clicked
        """
        if st.sidebar.button(
            "🔄 Actualiser maintenant",
            use_container_width=True,
            help="Forcer une actualisation immédiate"
        ):
            st.session_state.last_update = datetime.now()
            st.session_state.refresh_count += 1
            st.rerun()
            return True
        return False
    
    @staticmethod
    def auto_refresh_trigger(interval: int):
        """
        Trigger auto-refresh after interval.
        
        Args:
            interval: Seconds to wait before refresh (0 = disabled)
        """
        if interval > 0:
            # Calculate time since last update
            last_update = st.session_state.get('last_update', datetime.now())
            elapsed = (datetime.now() - last_update).total_seconds()
            
            # Only refresh if interval has passed
            if elapsed >= interval:
                st.session_state.last_update = datetime.now()
                st.session_state.refresh_count = st.session_state.get('refresh_count', 0) + 1
                time.sleep(0.1)  # Small delay to ensure state is saved
                st.rerun()
            else:
                # Wait for remaining time
                remaining = interval - elapsed
                time.sleep(min(remaining, 1))  # Check at least every second
                st.rerun()
    
    @staticmethod
    def show_refresh_indicator(enabled: bool = True):
        """
        Show visual indicator when auto-refresh is active.
        
        Args:
            enabled: Whether auto-refresh is currently enabled
        """
        if not enabled:
            return
        
        st.markdown("""
            <style>
            @keyframes pulse-green {
                0% { opacity: 1; transform: scale(1); }
                50% { opacity: 0.7; transform: scale(1.05); }
                100% { opacity: 1; transform: scale(1); }
            }
            .refresh-indicator {
                position: fixed;
                bottom: 24px;
                right: 24px;
                background: white;
                padding: 12px 20px;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                font-size: 13px;
                font-weight: 500;
                color: #1e293b;
                z-index: 1000;
                border: 1px solid #e5e7eb;
            }
            .pulse-dot {
                display: inline-block;
                width: 8px;
                height: 8px;
                background: #10b981;
                border-radius: 50%;
                margin-right: 10px;
                animation: pulse-green 2s infinite;
            }
            </style>
            <div class="refresh-indicator">
                <span class="pulse-dot"></span>
                Auto-actualisation active
            </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def get_status() -> dict:
        """
        Get current refresh status.
        
        Returns:
            Dict with enabled, interval, last_update, and count
        """
        AutoRefresh.initialize_session_state()
        
        return {
            'enabled': st.session_state.auto_refresh_enabled,
            'interval': st.session_state.refresh_interval,
            'last_update': st.session_state.last_update,
            'count': st.session_state.refresh_count
        }


# Convenience function for quick setup
def setup_auto_refresh(
    show_indicator: bool = True,
    allow_manual: bool = True
) -> int:
    """
    Quick setup function for auto-refresh.
    
    Args:
        show_indicator: Show visual refresh indicator
        allow_manual: Show manual refresh button
        
    Returns:
        Current refresh interval (0 = disabled)
    """
    interval = AutoRefresh.render_controls()
    
    if allow_manual:
        AutoRefresh.manual_refresh_button()
    
    if show_indicator and interval > 0:
        AutoRefresh.show_refresh_indicator(enabled=True)
    
    return interval


if __name__ == "__main__":
    # Demo
    st.set_page_config(page_title="Auto-Refresh Demo", layout="wide")
    
    st.title("🔄 Auto-Refresh Demo")
    
    # Setup auto-refresh
    interval = setup_auto_refresh()
    
    # Show current time to demonstrate refresh
    st.metric(
        "Heure actuelle",
        datetime.now().strftime("%H:%M:%S"),
        delta="Mise à jour automatique"
    )
    
    # Show refresh stats
    status = AutoRefresh.get_status()
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Status", "Activé" if status['enabled'] else "Désactivé")
    
    with col2:
        st.metric("Intervalle", f"{status['interval']}s" if status['enabled'] else "N/A")
    
    with col3:
        st.metric("Actualisations", status['count'])
    
    # Sample data that changes
    import random
    st.subheader("Données dynamiques")
    st.write(f"Nombre aléatoire: {random.randint(1, 100)}")
    
    # Trigger refresh
    if interval > 0:
        AutoRefresh.auto_refresh_trigger(interval)
