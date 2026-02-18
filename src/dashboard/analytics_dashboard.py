import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.database.database_manager import DatabaseManager
from src.utils.i18n import get_i18n_text

def render_analytics_dashboard():
    """Render the Business Analytics Dashboard."""
    st.title(f"📊 {get_i18n_text('analytics_dashboard', 'Analytiques Performance')}")
    st.markdown("---")
    
    # Check credentials
    client_id = st.session_state.get('client_id')
    if not client_id:
        st.error("Session invalide.")
        return

    db = DatabaseManager()
    data = db.get_business_analytics(client_id)
    
    # --- 1. KPI Cards ---
    g_stats = data.get('global', {})
    total_claims = g_stats.get('total_claims', 0) or 0
    total_rec = g_stats.get('total_volume_recovered', 0) or 0.0
    total_req = g_stats.get('total_volume_requested', 0) or 0.0
    accepted = g_stats.get('accepted_count', 0) or 0
    
    success_rate = (accepted / total_claims * 100) if total_claims > 0 else 0.0
    recovery_rate = (total_rec / total_req * 100) if total_req > 0 else 0.0
    
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("Win Rate", f"{success_rate:.1f}%", help="Pourcentage de dossiers acceptés")
    col2.metric("Taux Recouvrement", f"{recovery_rate:.1f}%", help="Volume récupéré / Volume demandé")
    col3.metric("Volume Récupéré", f"{total_rec:,.2f} €")
    col4.metric("Dossiers Traités", total_claims)
    
    st.markdown("### 📈 Évolution Mensuelle")
    
    # --- 2. Monthly Chart ---
    monthly_data = data.get('monthly', [])
    if monthly_data:
        df_monthly = pd.DataFrame(monthly_data)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_monthly['month'],
            y=df_monthly['recovered'],
            name='Montant Récupéré (€)',
            marker_color='#10b981'
        ))
        
        fig.add_trace(go.Scatter(
            x=df_monthly['month'],
            y=df_monthly['count'],
            name='Nombre Dossiers',
            yaxis='y2',
            line=dict(color='#3b82f6', width=3)
        ))
        
        fig.update_layout(
            yaxis=dict(title="Montant (€)", side="left"),
            yaxis2=dict(title="Volume Dossiers", side="right", overlaying="y", showgrid=False),
            legend=dict(x=0, y=1.2, orientation="h"),
            margin=dict(l=0, r=0, t=20, b=0),
            height=350
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Pas assez de données pour afficher l'évolution mensuelle.")

    # --- 3. Carrier Performance ---
    st.markdown("### 🚚 Performance par Transporteur")
    
    carrier_data = data.get('by_carrier', [])
    if carrier_data:
        df_carrier = pd.DataFrame(carrier_data)
        
        # Calculate success rate per carrier
        df_carrier['success_rate'] = (df_carrier['accepted'] / df_carrier['total']) * 100
        
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown("#### Taux de Succès")
            fig_bar = px.bar(
                df_carrier, 
                x='carrier', 
                y='success_rate',
                color='success_rate',
                color_continuous_scale='RdYlGn',
                labels={'success_rate': 'Taux de succès (%)', 'carrier': 'Transporteur'},
                range_y=[0, 100]
            )
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with c2:
            st.markdown("#### Volume de Dossiers")
            fig_pie = px.pie(
                df_carrier, 
                values='total', 
                names='carrier',
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Prism
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            
    # --- 4. Recent Activity Logs ---
    st.markdown("### 📋 Activité Récente")
    
    logs = db.get_recent_activity(client_id, limit=10)
    if logs:
        for log in logs:
            icon = "👤"
            action = log['action']
            if 'login' in action: icon = "🔑"
            elif 'claim' in action: icon = "📝"
            elif 'export' in action: icon = "⬇️"
            
            st.markdown(
                f"""
                <div style="
                    display: flex; 
                    justify-content: space-between;
                    padding: 8px 0;
                    border-bottom: 1px solid #f0f0f0;
                ">
                    <span>{icon} **{action}**</span>
                    <span style="color: #888; font-size: 0.9em;">{log['timestamp']}</span>
                </div>
                """, 
                unsafe_allow_html=True
            )
    else:
        st.info("Aucune activité récente enregistrée.")
