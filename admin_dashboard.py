"""
Admin Dashboard - Interface pour la plateforme (Gestion des alertes & clients).
"""

import streamlit as st
import pandas as pd
from src.database.database_manager import DatabaseManager
from src.analytics.bypass_scorer import BypassScorer

# Initialize tools
db = DatabaseManager()
scorer = BypassScorer(db)

# Page config
st.set_page_config(page_title="ADMIN - Recours E-commerce", page_icon="🛡️", layout="wide")

st.markdown("# 🛡️ Administration - Recours E-commerce")
st.caption("Gestion des alertes Anti-Bypass et surveillance plateforme (Scoring IA Activé 🧠)")

# --- ALERTES SYSTEME ---
st.subheader("⚠️ Alertes Prioritaires (Anti-Bypass)")

conn = db.get_connection()
alerts_df = pd.read_sql_query("SELECT * FROM system_alerts WHERE is_resolved = 0 ORDER BY created_at DESC", conn)
conn.close()

if not alerts_df.empty:
    for _, alert in alerts_df.iterrows():
        with st.container():
            severity_color = {"high": "#ef4444", "medium": "#f59e0b", "low": "#3b82f6"}.get(alert['severity'], "#cbd5e1")
            
            st.markdown(f"""
            <div style="padding: 15px; border-left: 5px solid {severity_color}; background: #f8fafc; border-radius: 5px; margin-bottom: 10px;">
                <div style="font-weight: bold; color: {severity_color};">{alert['alert_type'].upper()} - {alert['severity'].upper()}</div>
                <div style="font-size: 1.1rem; margin: 5px 0;">{alert['message']}</div>
                <div style="font-size: 0.8rem; color: #64748b;">Détecté le : {alert['created_at']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button(f"✅ Résoudre", key=f"res_{alert['id']}"):
                    conn = db.get_connection()
                    conn.execute("UPDATE system_alerts SET is_resolved = 1, resolved_at = DATETIME('now') WHERE id = ?", (alert['id'],))
                    conn.commit()
                    conn.close()
                    st.rerun()
            st.markdown("---")
else:
    st.success("✨ Aucune alerte de contournement détectée. Les clients respectent le mandat de gestion.")

# --- STATISTIQUES GLOBALES ---
st.subheader("📊 Performance Plateforme")
col1, col2, col3 = st.columns(3)

conn = db.get_connection()
total_clients = conn.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
total_claims = conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
total_recovered = conn.execute("SELECT SUM(accepted_amount) FROM claims WHERE status = 'recovered'").fetchone()[0] or 0
conn.close()

col1.metric("Clients Actifs", total_clients)
col2.metric("Dossiers Gérés", total_claims)
col3.metric("Total Récupéré (€)", f"{total_recovered:,.2f}")

# --- DERNIERS CLIENTS & TRUST SCORING ---
st.subheader("👥 Surveillance Clients & Indice de Confiance")
conn = db.get_connection()
clients_df = pd.read_sql_query("SELECT id, email, company_name, created_at FROM clients ORDER BY created_at DESC LIMIT 10", conn)

if not clients_df.empty:
    # Calculer les scores en temps réel pour l'admin
    scores = []
    labels = []
    for _, row in clients_df.iterrows():
        score = scorer.calculate_client_risk_score(row['id'])
        label_info = scorer.get_client_trust_label(score)
        scores.append(score)
        labels.append(label_info['label'])
    
    clients_df['Score Risque'] = scores
    clients_df['Confiance'] = labels
    
    # Affichage stylisé (Streamlit table does not support background colors easily, use dataframe styling or columns)
    st.dataframe(clients_df, width='stretch')
    
    st.info("💡 **Indice de Confiance** : Basé sur l'analyse IA des écarts de tracking et l'historique des alertes bypass.")

conn.close()
