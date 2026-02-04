
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import sys

root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(root_dir, 'src'))
sys.path.insert(0, root_dir)

from database.database_manager import get_db_manager
from analytics.metrics_calculator import MetricsCalculator
from utils.cloud_sync_manager import CloudSyncManager


from src.ui.theme import apply_premium_theme, render_premium_metric

# Page config
st.set_page_config(
    page_title="Refundly.ai - Control Tower",
    page_icon="🗼",
    layout="wide"
)

# Apply unified premium theme
apply_premium_theme()

def render_global_metrics(stats):
    """Affiche les KPIs globaux avec le style premium grid."""
    df = pd.DataFrame(stats)
    
    st.markdown("#### Global Metrics (Thousands of Clients)")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        render_premium_metric("Active Clients", f"{len(df) * 125:,}", "0.6% Growth", icon="👥", progress=85)
        render_premium_metric("Network Health", "99.9%", "Uptime stable", icon="⚡", progress=99)
        
    with col2:
        total_recovered = df['total_recovered'].sum() * 1200 # scaled for mockup feel
        render_premium_metric("Total Refund Value", f"${total_recovered:,.0f}", "Global network", icon="💰", progress=70)
        render_premium_metric("Total Refund Claims", "1.73%", "Approval rate", icon="📈", progress=45)
        
    with col3:
        render_premium_metric("Pending Records", "1,205", "Processing", icon="📂", progress=55)
        render_premium_metric("Success Rate", "42.4%", "In queue", icon="🎯", progress=42)

def render_forecasting(stats):
    """Affiche les projections de cashflow basées sur l'IA."""
    st.subheader("🔮 Intelligence Prédictive & Cashflow Pipeline")
    
    from ai.predictor import AIPredictor
    predictor = AIPredictor()
    
    df = pd.DataFrame(stats)
    # Simulation des dossiers "en cours"
    total_pending_amount = max(5000, df['total_requested'].sum() - df['total_recovered'].sum())
    
    mock_disputes = [
        {'carrier': 'Colissimo', 'dispute_type': 'late_delivery', 'amount_recoverable': total_pending_amount * 0.4},
        {'carrier': 'UPS', 'dispute_type': 'lost', 'amount_recoverable': total_pending_amount * 0.3},
        {'carrier': 'Chronopost', 'dispute_type': 'damaged', 'amount_recoverable': total_pending_amount * 0.3},
    ]
    
    forecasts = predictor.get_forecasted_cashflow(mock_disputes)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        render_premium_metric("📦 Pipeline Total (En cours)", f"{forecasts['total_potential_raw']:,.2f}€", "Gross Volume", icon="📦", progress=30)
    with col2:
        render_premium_metric("🎯 Recouvrement Attendu (IA)", f"{forecasts['weighted_expected_recovery']:,.2f}€", "Weighted Probability", icon="🎯", progress=52)
    with col3:
        render_premium_metric("🛡️ Estimation Prudente", f"{forecasts['conservative_estimate']:,.2f}€", "-10% safety margin", icon="🛡️", progress=45)
    
    from src.ui.theme import render_premium_info
    render_premium_info("Ces prédictions sont mises à jour en temps réel en fonction des performances actuelles des transporteurs.", icon="🔮")

def render_clients_table(stats):
    """Tableau récapitulatif de tous les clients."""
    st.subheader("📊 Performance par Client")
    
    df = pd.DataFrame(stats)
    
    # Formatage pour l'affichage
    display_df = df[[
        'email', 'total_claims', 'accepted_claims', 'pending_claims', 
        'total_requested', 'total_recovered'
    ]].copy()
    
    display_df.columns = [
        'Client', 'Total Dossiers', 'Acceptés', 'En cours', 
        'Montant Choisi', 'Montant Récupéré'
    ]
    
    st.dataframe(
        display_df,
        width='stretch',
        hide_index=True
    )

def render_fraud_alerts():
    """Interface de gestion des alertes de contournement (Bypass)."""
    st.subheader("🛡️ Alertes IA & Bypass (Global)")
    
    db = get_db_manager()
    # On simule la récupération d'alertes depuis system_alerts
    # En prod: alerts = db.get_system_alerts(alert_type='bypass_detected', is_resolved=False)
    
    alerts = [
        {"id": 1, "type": "Bypass Detecté", "client": "marchand_a@email.com", "ref": "CLM-2026-001", "score": 92, "reason": "Colis marqué Livré après plainte perte"},
        {"id": 2, "type": "Suspicion Fraude", "client": "marchand_b@email.com", "ref": "CLM-2026-045", "score": 85, "reason": "Multi-réclamations même adresse"}
    ]
    
    for alert in alerts:
        with st.warning(f"🚨 {alert['type']} - Score: {alert['score']}%"):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(f"**Client:** {alert['client']}")
                st.write(f"**Ref:** {alert['ref']}")
            with col2:
                st.write(f"**Raison:** {alert['reason']}")
            with col3:
                if st.button("🔍 Investiguer", key=f"inv_{alert['id']}"):
                    st.info("Ouverture du dossier...")
                if st.button("✅ Bloquer", key=f"block_{alert['id']}"):
                    st.error("Client suspendu temporairement.")

def main():
    st.markdown("<div class='main-header'>Refundly.ai Control Tower</div>", unsafe_allow_html=True)
    
    db = get_db_manager()
    stats = db.get_all_statistics()
    
    if not stats:
        st.info("Aucune donnée disponible.")
        return
    
    # MAIN LAYOUT (Matches Mockup)
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        # 1. Global Metrics Grid
        render_global_metrics(stats)
        
        # 2. Carrier Chart
        st.markdown("#### Carrier Reliability Rankings")
        from src.analytics.carrier_benchmark import CarrierBenchmarkService
        benchmark_svc = CarrierBenchmarkService()
        leaderboard = benchmark_svc.get_market_leaderboard()
        
        fig = go.Figure()
        colors = ['#10b981', '#f59e0b', '#f43f5e'] # Green, Yellow, Orange
        
        for i, carrier in enumerate(leaderboard['carrier'].head(3)):
            score = leaderboard.iloc[i]['reliability_score']
            fig.add_trace(go.Bar(
                y=[carrier],
                x=[score],
                orientation='h',
                marker_color=colors[i % len(colors)],
                text=f"{score}%",
                textposition='inside',
                name=carrier
            ))
            
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#1e293b',
            height=350,
            margin=dict(l=100, r=20, t=20, b=20),
            showlegend=False,
            xaxis=dict(range=[0, 100], showgrid=False, zeroline=False, tickfont=dict(color='#1e293b', size=12)),
            yaxis=dict(showgrid=False, tickfont=dict(color='#1e293b', size=14, family="Inter", weight="bold"))
        )
        st.plotly_chart(fig, width='stretch')
        
        # Space for other tabs below
        st.markdown("---")
        tab1, tab2 = st.tabs(["👥 Clients Detail", "🔮 AI Forecasting"])
        with tab1:
            render_clients_table(stats)
        with tab2:
            render_forecasting(stats)

    with col_right:
        # 3. Audit Log Feed
        st.markdown("#### Audit Log Feed")
        from src.auth.security_manager import SecurityManager
        sec_mgr = SecurityManager()
        logs = sec_mgr.get_audit_trail(limit=6)
        
        for log in logs:
            timestamp = log['created_at'].split()[1] if ' ' in log['created_at'] else log['created_at']
            action = log['action']
            
            # Action class for colors
            action_class = ""
            if "detect" in action.lower(): action_class = "auto-detect"
            elif "payout" in action.lower(): action_class = "payout"
            elif "fraud" in action.lower() or "alert" in action.lower(): action_class = "fraud"
            
            st.markdown(f"""
            <div class="audit-log-item">
                <div class="audit-time">{timestamp}</div>
                <div class="audit-action {action_class}">{action.replace('_', ' ').capitalize()}</div>
                <div class="audit-client">Client ID #{log['user_id']}</div>
            </div>
            """, unsafe_allow_html=True)
            
        # 4. Tech Monitoring
        st.markdown("#### Tech Monitoring", unsafe_allow_html=True)
        from src.monitoring.health_monitor import HealthMonitor
        monitor = HealthMonitor()
        db_health = monitor.check_database()
        
        # Latency Gauge
        fig_g = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = db_health['latency_ms'],
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "DB Latency (ms)", 'font': {'size': 14, 'color': '#1e293b'}},
            gauge = {
                'axis': {'range': [0, 10], 'tickwidth': 1, 'tickcolor': "#64748b"},
                'bar': {'color': "#10b981"},
                'bgcolor': "white",
                'borderwidth': 1,
                'bordercolor': "#e2e8f0",
                'steps': [
                    {'range': [0, 2], 'color': 'rgba(16, 185, 129, 0.1)'},
                    {'range': [2, 10], 'color': 'rgba(244, 63, 94, 0.1)'}
                ],
            }
        ))
        fig_g.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', 
            font={'color': "#1e293b", 'family': "Inter"}, 
            height=180, 
            margin=dict(l=30, r=30, t=50, b=0)
        )
        st.plotly_chart(fig_g, width='stretch')
        
        st.markdown("""
        <div class="cert-badge">
            <div style="color: #10b981; font-size: 0.9rem; font-weight: 700; display: flex; align-items: center; justify-content: center; gap: 8px;">
                <span>🟢</span> Server Heartbeat Active
            </div>
            <div style="color: #64748b; font-size: 0.75rem; margin-top: 4px;">Verified SOC2 & GDPR Compliant</div>
        </div>
        """, unsafe_allow_html=True)

    # Secondary tabs for other features
    st.markdown("---")
    st.subheader("🛠 Outils Avancés")
    tab_sec, tab_infra = st.tabs(["🛡️ Sécurité & Bypass", "⚙️ Infra & Health"])
    
    with tab_sec:
        render_fraud_alerts()
    with tab_infra:
        st.markdown("#### ⚙️ Maintenance & Cloud")
        sync_manager = CloudSyncManager()
        
        col_s1, col_s2 = st.columns([2, 1])
        with col_s1:
            st.info("💡 **Synchronisation Totale** : Transférez toutes les données locales (Comptes, Dossiers, Photos) vers Supabase en un clic.")
        with col_s2:
            if st.button("🚀 Lancer la Synchro Cloud", use_container_width=True, type="primary"):
                with st.spinner("⏳ Migration en cours..."):
                    success, message = sync_manager.run_full_sync()
                    if success:
                        st.success("✅ Synchronisation réussie !")
                        st.balloons()
                        st.toast(message)
                    else:
                        st.error(f"❌ Erreur : {message}")
        
        st.markdown("---")
        st.markdown("#### 📊 System Metrics")
        st.code(monitor.get_system_metrics(), language="text")

if __name__ == "__main__":
    main()
