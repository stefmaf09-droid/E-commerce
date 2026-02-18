import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

from src.auth.password_manager import PasswordManager, set_user_role
from src.database.database_manager import get_db_manager

def render_admin_panel():
    """Render the Admin Panel for user management and global stats."""
    
    st.title("👑 Admin Panel")
    st.markdown("---")
    
    # --- TABS ---
    tab_users, tab_stats, tab_settings = st.tabs(["👥 Utilisateurs", "📊 Global Stats", "⚙️ Paramètres"])
    
    # ----------------------------------------------------
    # TAB 1: USERS MANAGEMENT
    # ----------------------------------------------------
    with tab_users:
        st.subheader("Gestion des Utilisateurs")
        
        pwd_manager = PasswordManager()
        users = pwd_manager.get_all_users()
        
        if not users:
            st.warning("Aucun utilisateur trouvé.")
        else:
            # Convert to DataFrame for easier handling
            df_users = pd.DataFrame(users)
            df_users['created_at'] = pd.to_datetime(df_users['created_at'])
            
            # Display summary metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Utilisateurs", len(df_users))
            col2.metric("Admins", len(df_users[df_users['role'] == 'admin']))
            col3.metric("Clients", len(df_users[df_users['role'] == 'client']))
            
            st.markdown("### Liste des inscrits")
            
            # Detailed list with actions
            for index, row in df_users.iterrows():
                with st.expander(f"{row['client_email']} ({row['role']})", expanded=False):
                    c1, c2, c3 = st.columns([2, 1, 1])
                    
                    with c1:
                        st.write(f"**Email:** {row['client_email']}")
                        st.write(f"**Inscrit le:** {row['created_at'].strftime('%d/%m/%Y %H:%M')}")
                    
                    with c2:
                        current_role = row['role']
                        # Role selector
                        new_role = st.selectbox(
                            "Rôle", 
                            ['client', 'admin'], 
                            index=0 if current_role == 'client' else 1,
                            key=f"role_{row['client_email']}"
                        )
                    
                    with c3:
                        st.write("") # Spacer
                        if new_role != current_role:
                            if st.button("💾 Enregistrer", key=f"save_{row['client_email']}"):
                                success = set_user_role(row['client_email'], new_role)
                                if success:
                                    st.success(f"Rôle mis à jour: {new_role}")
                                    st.rerun()
                                else:
                                    st.error("Erreur lors de la mise à jour")
                        
                        if st.button("🗑️ Supprimer", key=f"del_{row['client_email']}", type="primary"):
                            st.warning("Fonctionnalité de suppression à implémenter (RGPD)")

    # ----------------------------------------------------
    # TAB 2: GLOBAL STATS
    # ----------------------------------------------------
    with tab_stats:
        st.subheader("Statistiques Globales")
        
        db_manager = get_db_manager()
        conn = db_manager.get_connection()
        
        try:
            # Aggregate stats from all claims
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_claims,
                    SUM(amount_requested) as total_volume,
                    SUM(CASE WHEN status='accepted' THEN accepted_amount ELSE 0 END) as total_recovered,
                    COUNT(DISTINCT client_id) as active_clients
                FROM claims
            """)
            stats = cursor.fetchone()
            
            total_claims = stats[0] or 0
            total_volume = stats[1] or 0.0
            total_recovered = stats[2] or 0.0
            active_clients = stats[3] or 0
            
            # Global Metrics
            g_col1, g_col2, g_col3, g_col4 = st.columns(4)
            g_col1.metric("Vol. Réclamé Total", f"{total_volume:,.0f} €")
            g_col2.metric("Vol. Récupéré Total", f"{total_recovered:,.0f} €")
            g_col3.metric("Total Dossiers", total_claims)
            g_col4.metric("Clients Actifs", active_clients)
            
            conn.close()
            
            # Charts could go here
            if total_claims > 0:
                st.info("📊 Graphiques globaux à venir...")
                
        except Exception as e:
            st.error(f"Erreur lors du chargement des stats : {e}")
            if 'conn' in locals():
                conn.close()

    # ----------------------------------------------------
    # TAB 3: SETTINGS
    # ----------------------------------------------------
    with tab_settings:
        st.info("Paramètres globaux de l'instance (ex: mode maintenance, clés API globales, etc.)")
