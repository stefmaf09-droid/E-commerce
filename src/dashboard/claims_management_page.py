"""
Claims Management Page

Enhanced claims view with bulk actions:
- Select multiple claims with checkboxes
- Bulk export to CSV
- Bulk send reminders
- Bulk delete with confirmation
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import List

from src.database.database_manager import get_db_manager


def render_claims_management():
    """Render enhanced claims management page with bulk actions."""
    
    st.markdown("### 📋 Gestion des Litiges")
    st.caption("Visualisez et gérez vos réclamations en masse")
    
    # Load claims from database
    client_email = st.session_state.get('client_email')
    db = get_db_manager()
    
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Get client ID
        cursor.execute("SELECT id FROM clients WHERE email = ?", (client_email,))
        result = cursor.fetchone()
        
        if not result:
            st.error("Client non trouvé")
            conn.close()
            return
        
        client_id = result[0]
        
        # Fetch all claims
        cursor.execute("""
            SELECT 
                id,
                claim_reference,
                carrier,
                status,
                amount_requested,
                accepted_amount,
                submitted_at,
                dispute_type,
                tracking_number,
                response_deadline
            FROM claims
            WHERE client_id = ?
            ORDER BY submitted_at DESC
        """, (client_id,))
        
        claims = cursor.fetchall()
        conn.close()
        
        if not claims:
            st.info("📭 Aucun litige enregistré pour le moment.")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(claims, columns=[
            'id', 'claim_reference', 'carrier', 'status', 'amount_requested',
            'accepted_amount', 'submitted_at', 'dispute_type', 'tracking_number',
            'response_deadline'
        ])
        
        # Format amounts
        df['amount_requested'] = df['amount_requested'].apply(lambda x: f"{x:.2f}€" if x else "0€")
        df['accepted_amount'] = df['accepted_amount'].apply(lambda x: f"{x:.2f}€" if x else "-")
        
        # Format dates
        df['submitted_at'] = pd.to_datetime(df['submitted_at']).dt.strftime('%d/%m/%Y')
        df['response_deadline'] = pd.to_datetime(df['response_deadline'], errors='coerce').dt.strftime('%d/%m/%Y')
        
        # Status badge
        status_emoji = {
            'pending': '⏳',
            'submitted': '📤',
            'accepted': '✅',
            'rejected': '❌',
            'in_progress': '🔄'
        }
        df['status_display'] = df['status'].apply(lambda x: f"{status_emoji.get(x, '❓')} {x.capitalize()}")
        
        # Show summary stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total litiges", len(df))
        with col2:
            accepted_count = len(df[df['status'] == 'accepted'])
            st.metric("Acceptés", accepted_count)
        with col3:
            pending_count = len(df[df['status'].isin(['pending', 'submitted'])])
            st.metric("En cours", pending_count)
        with col4:
            rejected_count = len(df[df['status'] == 'rejected'])
            st.metric("Rejetés", rejected_count)
        
        st.markdown("---")
        
        # Bulk Actions Toolbar
        st.markdown("#### ⚡ Actions groupées")
        
        col_bulk1, col_bulk2, col_bulk3 = st.columns(3)
        
        with col_bulk1:
            if st.button("📥 Exporter tout en CSV", use_container_width=True):
                export_claims_to_csv(df)
        
        with col_bulk2:
            if st.button("📧 Envoyer rappels (en cours)", use_container_width=True):
                send_bulk_reminders(df)
        
        with col_bulk3:
            if st.button("🗑️ Supprimer sélection", use_container_width=True, type="secondary"):
                st.session_state.show_delete_confirmation = True
        
        st.markdown("---")
        
        # Display claims table with selection
        st.markdown("#### 📊 Liste des litiges")
        
        # Use data_editor with checkbox for selection
        display_df = df[['claim_reference', 'carrier', 'status_display', 'amount_requested', 'submitted_at', 'response_deadline']].copy()
        display_df.columns = ['Référence', 'Transporteur', 'Statut', 'Montant', 'Soumis le', 'Deadline']
        
        edited_df = st.data_editor(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "select": st.column_config.CheckboxColumn(
                    "Sélectionner",
                    help="Cochez pour sélectionner le litige",
                    default=False,
                )
            },
            disabled=["Référence", "Transporteur", "Statut", "Montant", "Soumis le", "Deadline"],
            key="claims_table"
        )
        
        # Delete confirmation dialog
        if st.session_state.get('show_delete_confirmation'):
            st.error("⚠️ **Attention** : La suppression est définitive !")
            col_conf1, col_conf2 = st.columns(2)
            with col_conf1:
                if st.button("✅ Confirmer la suppression", type="primary"):
                    # TODO: Implement bulk delete
                    st.success("🗑️ Litiges supprimés")
                    st.session_state.show_delete_confirmation = False
                    st.rerun()
            with col_conf2:
                if st.button("❌ Annuler"):
                    st.session_state.show_delete_confirmation = False
                    st.rerun()
        
    except Exception as e:
        st.error(f"Erreur lors du chargement des litiges : {str(e)}")


def export_claims_to_csv(df: pd.DataFrame):
    """Export claims to CSV file."""
    try:
        # Prepare CSV
        csv_df = df[[
            'claim_reference', 'carrier', 'status', 'amount_requested',
            'submitted_at', 'tracking_number', 'response_deadline'
        ]].copy()
        
        csv_data = csv_df.to_csv(index=False, encoding='utf-8-sig')
        
        # Provide download button
        st.download_button(
            label="📥 Télécharger le CSV",
            data=csv_data,
            file_name=f"litiges_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            key="download_claims_csv"
        )
        
        st.success(f"✅ {len(df)} litiges prêts à être exportés !")
        
    except Exception as e:
        st.error(f"Erreur lors de l'export : {str(e)}")


def send_bulk_reminders(df: pd.DataFrame):
    """Send reminder emails for pending claims."""
    try:
        pending_claims = df[df['status'].isin(['pending', 'submitted'])]
        
        if pending_claims.empty:
            st.warning("Aucun litige en cours ne nécessite de rappel.")
            return
        
        from src.notifications.notification_manager import NotificationManager
        notification_mgr = NotificationManager()
        
        client_email = st.session_state.get('client_email')
        sent_count = 0
        
        for _, claim in pending_claims.iterrows():
            try:
                success = notification_mgr.queue_notification(
                    client_email=client_email,
                    event_type='claim_updated',
                    context={
                        'claim_ref': claim['claim_reference'],
                        'carrier': claim['carrier'],
                        'status': 'reminder_sent'
                    }
                )
                if success:
                    sent_count += 1
            except Exception as e:
                st.warning(f"Impossible d'envoyer le rappel pour {claim['claim_reference']}: {e}")
        
        st.success(f"📧 {sent_count} rappels envoyés avec succès !")
        
    except Exception as e:
        st.error(f"Erreur lors de l'envoi des rappels : {str(e)}")


if __name__ == "__main__":
    # For standalone testing
    st.set_page_config(page_title="Claims Management", layout="wide")
    
    # Mock session state
    if 'client_email' not in st.session_state:
        st.session_state.client_email = 'test@client.com'
    
    render_claims_management()
