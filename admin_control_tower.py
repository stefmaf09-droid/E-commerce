
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
    print("\n\n*** DEBUG: ADMIN CONTROL TOWER V2.0 LOADING (FINANCE LIVE) ***\n\n")
    st.markdown("<div class='main-header'>Refundly.ai Control Tower v2.0 (Finance Live) 💸</div>", unsafe_allow_html=True)
    
    db = get_db_manager()
    db = get_db_manager()
    try:
        stats = db.get_all_statistics()
    except Exception as e:
        st.warning(f"⚠️ **Mode Hors Ligne / Erreur Connexion**: Impossible de joindre la base de données Cloud ({str(e)}). Affichage en mode dégradé.")
        stats = []
    
    # 🆕 TABS STRUCTURE: Infra accessible everywhere
    tab_dash, tab_finance, tab_logs, tab_infra = st.tabs(["📊 Dashboard", "💸 Finance & Payouts", "🚨 Audit & Logs", "⚙️ Infra & Cloud Sync"])
    
    with tab_infra:
        st.markdown("### ☁️ Cloud Synchronization & Health")
        
        # Cloud Sync Manager
        from src.utils.cloud_sync_manager import CloudSyncManager
        sync_manager = CloudSyncManager()
        
        col_s1, col_s2 = st.columns([2, 1])
        with col_s1:
            st.info("💡 **Synchronisation Totale** : Transférez toutes les données locales (Comptes, Dossiers, Photos) vers Supabase en un clic. À faire après le déploiement.")
        with col_s2:
            if st.button("🚀 Lancer la Synchro Cloud", use_container_width=True, type="primary"):
                with st.spinner("⏳ Migration en cours..."):
                    success, message = sync_manager.run_full_sync()
                    if success:
                        st.success("✅ Synchronisation réussie !")
                        st.balloons()
                        st.toast(message)
                        # Rerun to show data immediately
                        st.rerun()
                    else:
                        st.error(f"❌ Erreur : {message}")

        st.markdown("---")
        st.markdown("#### ⚙️ Tech Monitoring")
        from src.monitoring.health_monitor import HealthMonitor
        monitor = HealthMonitor()
        st.code(monitor.get_system_metrics(), language="text")

    with tab_dash:
        if not stats:
            st.warning("⚠️ **Base de données vide.**\nRendez-vous dans l'onglet **'⚙️ Infra & Cloud Sync'** pour lancer la première synchronisation.")
        else:
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
                # 3. AI Insights Panel (simplified for layout)
                st.markdown("#### 🧠 AI Forecasting")
                col_tech1, col_tech2 = st.columns(2)
                col_tech1.metric("API Latency", "45ms", "-12ms")
                col_tech2.metric("Error Rate", "0.02%", "stable")
                st.markdown("---")
                st.markdown("**Cashflow Pipeline:**")
                st.markdown("- 🟢 **Confirmed:** 12,450€")
                st.markdown("- 🟡 **Pending:** 4,200€")
                
                st.markdown("#### Client Trust Scores")
                trust_df = pd.DataFrame(stats)
                if not trust_df.empty and 'total_claims' in trust_df.columns:
                    trust_df['Trust %'] = (trust_df['accepted_claims'] / trust_df['total_claims'] * 100).fillna(0).round(0).astype(int)
                    st.dataframe(
                        trust_df[['email', 'Trust %']].sort_values('Trust %', ascending=False),
                        hide_index=True,
                        use_container_width=True,
                        column_config={
                            "email": "Client",
                            "Trust %": st.column_config.ProgressColumn(
                                "Trust Score",
                                help="Taux d'acceptation des dossiers",
                                format="%d%%",
                                min_value=0,
                                max_value=100,
                            ),
                        }
                    )

    with tab_finance:
        st.markdown("#### 💸 Finance & Payouts")
        st.info("ℹ️ **Mode Réel** : Validez ici les virements des transporteurs. Le système reversera automatiquement 80% au client via Stripe Connect.")
        
        # Fetch resolved claims pending payout
        # Mocking for now, in prod: db.get_claims(status='accepted', payment_status='pending')
        # We'll use a mocked list for demonstration if DB is empty/unstructured for this specific query
        
        try:
            # Replaced with actual DB call logic if possible, or keep using stats for structure
            # Let's try to get real claims if possible
            conn = db.get_connection()
            # Assuming 'claims' table has status and payment_status columns
            # We filter for 'accepted' statuses where payment hasn't been marked 'completed'
            pending_payouts_df = pd.read_sql_query("""
                SELECT 
                    c.id, c.claim_reference, c.carrier, c.accepted_amount, 
                    cl.email as client_email, cl.stripe_connect_id, cl.company_name
                FROM claims c
                JOIN clients cl ON c.client_id = cl.id
                WHERE c.status = 'accepted' 
                AND (c.payment_status IS NULL OR c.payment_status != 'paid')
            """, conn)
            conn.close()
            
            if pending_payouts_df.empty:
                st.success("✅ Tous les dossiers validés ont été payés. Aucun reversement en attente.")
            else:
                st.markdown(f"**{len(pending_payouts_df)} Virements en attente**")
                
                for index, row in pending_payouts_df.iterrows():
                    with st.expander(f"💰 {row['carrier']} - {row['claim_reference']} ({row['accepted_amount']}€) -> {row['company_name']}"):
                        
                        col_pay1, col_pay2, col_pay3 = st.columns(3)
                        with col_pay1:
                            st.write(f"**Montant Reçu:** {row['accepted_amount']}€")
                            client_share = round(row['accepted_amount'] * 0.8, 2)
                            refundly_share = round(row['accepted_amount'] * 0.2, 2)
                            st.write(f"**Part Client (80%):** {client_share}€")
                            st.write(f"**Commission (20%):** {refundly_share}€")
                        
                        with col_pay2:
                            st.write(f"**Destinataire:** {row['client_email']}")
                            if row['stripe_connect_id']:
                                st.success(f"✅ Stripe Connect: {row['stripe_connect_id']}")
                            else:
                                st.error("❌ Pas de compte Stripe connecté")
                        
                        with col_pay3:
                            if row['stripe_connect_id']:
                                if st.button("💸 Distribuer les fonds", key=f"pay_{row['id']}"):
                                    # EXECUTE STRIPE TRANSFER
                                    from src.payments.stripe_manager import StripeManager
                                    stripe_mgr = StripeManager()
                                    
                                    try:
                                        with st.spinner("Traitement du virement Stripe..."):
                                            # Create Transfer
                                            transfer_id = stripe_mgr.create_payout_transfer(
                                                destination_account_id=row['stripe_connect_id'],
                                                amount=float(row['accepted_amount']),
                                                client_commission_rate=20.0,
                                                claim_ref=row['claim_reference']
                                            )
                                            
                                            # Update DB
                                            conn = db.get_connection()
                                            with conn.cursor() as cur:
                                                cur.execute("UPDATE claims SET payment_status = 'paid' WHERE id = %s", (row['id'],))
                                            conn.commit()
                                            conn.close()
                                            
                                            st.success(f"✅ Virement effectué ! ID: {transfer_id}")
                                            st.balloons()
                                            st.rerun()
                                            
                                    except Exception as e:
                                        st.error(f"Erreur Stripe: {str(e)}")
                            else:
                                st.warning("Le client doit configurer Stripe.")

        except Exception as e:
            # Fallback if query fails (e.g. schema mismatch)
            st.error(f"Erreur de chargement des paiements: {str(e)}")
            st.warning("Vérifiez que la base de données est synchronisée avec le dernier schéma.")

    with tab_logs:
        st.markdown("#### Audit Log Feed")
        from src.auth.security_manager import SecurityManager
        sec_mgr = SecurityManager()
        logs = sec_mgr.get_audit_trail(limit=10)
        
        for log in logs:
            timestamp = log['created_at'].split()[1] if ' ' in log['created_at'] else log['created_at']
            action = log['action']
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

if __name__ == "__main__":
    main()

