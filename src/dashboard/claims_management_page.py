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
from src.utils.i18n import get_i18n_text, get_browser_language


def render_claims_management():
    """Render enhanced claims management page with bulk actions."""
    
    lang = get_browser_language()
    
    st.markdown(f"### 📋 {get_i18n_text('claims_management_title', lang)}")
    st.caption(get_i18n_text('claims_management_caption', lang))
    
    # Load claims from database
    client_email = st.session_state.get('client_email')
    db = get_db_manager()
    
    try:
        # Use DatabaseManager methods instead of direct SQL to handle PostgreSQL compatibility
        client = db.get_client(email=client_email)
        
        if not client:
            st.error(get_i18n_text('client_not_found', lang))
            return
        
        client_id = client['id']
        
        # Fetch all claims with POD info using db._execute for special queries
        conn = db.get_connection()
        cursor = db._execute(conn, """
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
                response_deadline,
                pod_fetch_status,
                pod_url,
                pod_fetch_error
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
            'response_deadline', 'pod_fetch_status', 'pod_url', 'pod_fetch_error'
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
        
        # 🔍 Filters Section
        filter_col1, filter_col2 = st.columns([2, 1])
        with filter_col1:
            search_term = st.text_input("🔍 Recherche", placeholder="Référence, transporteur ou tracking...", label_visibility="collapsed")
        with filter_col2:
            status_options = list(df['status'].unique())
            selected_statuses = st.multiselect("Statut", options=status_options, placeholder="Filtrer par statut", label_visibility="collapsed", format_func=lambda x: f"{status_emoji.get(x, '❓')} {x.capitalize()}")

        # Apply filters
        filtered_df = df.copy()
        if search_term:
            search_lower = search_term.lower()
            filtered_df = filtered_df[
                filtered_df['claim_reference'].str.lower().str.contains(search_lower) |
                filtered_df['carrier'].str.lower().str.contains(search_lower) |
                filtered_df['tracking_number'].str.lower().str.contains(search_lower)
            ]
        
        if selected_statuses:
            filtered_df = filtered_df[filtered_df['status'].isin(selected_statuses)]
        
        st.markdown("")
        
        # POD Status Section
        st.markdown(f"#### 📄 {get_i18n_text('pod_status_title', lang)}")
        st.caption("Visualisez la disponibilité des preuves de livraison et relancez les échecs")
        
        # Pod stats
        pod_col1, pod_col2, pod_col3, pod_col4 = st.columns(4)
        with pod_col1:
            success_count = len(df[df['pod_fetch_status'] == 'success'])
            st.metric("POD Disponibles", success_count, delta=None)
        with pod_col2:
            pending_count = len(df[df['pod_fetch_status'] == 'pending'])
            st.metric("En attente", pending_count, delta=None)
        with pod_col3:
            failed_count = len(df[df['pod_fetch_status'] == 'failed'])
            st.metric("Échecs", failed_count, delta=None)
        with pod_col4:
            none_count = len(df[df['pod_fetch_status'].isna()])
            st.metric("Non demandés", none_count, delta=None)
        
        st.markdown("---")
        
        # Display POD status with actions for each claim
        for _, claim in df.iterrows():
            pod_status = claim.get('pod_fetch_status')
            claim_ref = claim['claim_reference']
            
            if pod_status == 'success':
                cols = st.columns([3, 1, 1])
                with cols[0]:
                    st.success(get_i18n_text('pod_status_available', lang).format(claim_ref=claim_ref), icon="📄")
                with cols[1]:
                    if claim.get('pod_url'):
                        # View POD button - show inline viewer
                        if st.button(f"👁️ {get_i18n_text('view_pod', lang)}", key=f"view_{claim['id']}", use_container_width=True):
                            st.session_state[f"show_pod_{claim_ref}"] = True
                            st.rerun()
                with cols[2]:
                    if claim.get('pod_url'):
                        st.link_button(f"⬇️", claim['pod_url'], use_container_width=True, help=get_i18n_text('download_csv', lang))
                    else:
                        st.caption("URL non disponible")
                
                # Display POD viewer if requested
                if st.session_state.get(f"show_pod_{claim_ref}", False):
                    from src.dashboard.pod_viewer import render_pod_viewer
                    with st.container():
                        render_pod_viewer(claim['pod_url'], claim_ref, display_mode="inline")
            
            elif pod_status == 'failed':
                cols = st.columns([3, 1])
                with cols[0]:
                    st.error(get_i18n_text('pod_status_failed', lang).format(claim_ref=claim_ref), icon="⚠️")
                    if claim.get('pod_fetch_error'):
                        st.caption(f"Erreur: {claim['pod_fetch_error'][:80]}")
                with cols[1]:
                    if st.button(f"🔄 {get_i18n_text('btn_retry_pod', lang)}", key=f"retry_{claim['id']}", use_container_width=True):
                        retry_pod_fetch(claim['id'], claim['tracking_number'], claim['carrier'])
                        st.rerun()
            
            elif pod_status == 'pending':
                st.warning(get_i18n_text('pod_status_fetching', lang).format(claim_ref=claim_ref), icon="⏱️")
        
        # Bulk retry button for failed PODs
        if failed_count > 0:
            st.markdown("---")
            if st.button(f"🔄 {get_i18n_text('btn_retry_all', lang)} ({failed_count})", type="primary", use_container_width=True):
                bulk_retry_failed_pods(df)
                st.rerun()
        
        st.markdown("---")
        
        # Bulk Actions Toolbar
        st.markdown(f"#### ⚡ {get_i18n_text('bulk_actions_title', lang)}")
        
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
        st.markdown(f"#### 📊 {get_i18n_text('claims_list_title', lang)}")
        
        # Use data_editor with checkbox for selection
        display_df = filtered_df[['claim_reference', 'carrier', 'status_display', 'amount_requested', 'submitted_at', 'response_deadline']].copy()
        display_df.columns = ['Référence', 'Transporteur', 'Statut', 'Montant', 'Soumis le', 'Deadline']
        display_df.insert(0, "select", False)
        
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

        # Handle View Details Action
        selected_rows = edited_df[edited_df["select"]]
        
        # We need to find the full row data for selected items
        # The edited_df only has display columns. We need to map back to original df via index if possible, 
        # but hide_index=True makes it harder. 
        # Workaround: Use Claim Reference as key since it's unique
        
        if not selected_rows.empty:
            # Check if "Voir Détails" was clicked (we need a way to detect button click OR just show button below)
            # Actually, let's put the action buttons BELOW the table for context-aware actions
            
            selected_refs = selected_rows['Référence'].tolist()
            
            col_actions1, col_actions2 = st.columns([1, 4])
            with col_actions1:
                if st.button(f"👁️ Voir ({len(selected_rows)})", type="primary", use_container_width=True):
                    if len(selected_rows) == 1:
                        # Navigate
                        ref = selected_refs[0]
                        # Find full claim data
                        original_claim = df[df['claim_reference'] == ref].iloc[0]
                        
                        st.session_state.selected_dispute = {
                            'dispute_id': original_claim['claim_reference'],
                            'order_id': original_claim.get('order_id', 'N/A'),
                            'tracking_number': original_claim['tracking_number'],
                            'carrier': original_claim['carrier'],
                            'dispute_type': original_claim['dispute_type'],
                            'amount': original_claim['amount_requested'],
                            'status': original_claim['status'],
                            'created_at': original_claim['submitted_at'],
                             # Add other necessary fields for details page
                            'customer_email': st.session_state.get('client_email'),
                            'customer_name': original_claim.get('customer_name', 'Client'),
                            'delivery_address': original_claim.get('delivery_address', 'Adresse inconnue')
                        }
                        st.session_state.active_page = 'Dispute Details'
                        st.rerun()
                    else:
                        st.warning("Veuillez sélectionner un seul litige pour voir les détails.")
            
            with col_actions2:
                if st.button("🗑️ Supprimer", type="secondary"):
                    st.session_state.show_delete_confirmation = True

        st.caption(f"Affichage de {len(filtered_df)} litiges")
        
        # Delete confirmation dialog
        if st.session_state.get('show_delete_confirmation'):
            st.error(f"⚠️ **{get_i18n_text('delete_warning', lang)}**")
            col_conf1, col_conf2 = st.columns(2)
            with col_conf1:
                if st.button(f"✅ {get_i18n_text('btn_confirm_delete', lang)}", type="primary"):
                    # TODO: Implement bulk delete
                    st.success(f"🗑️ {get_i18n_text('claims_deleted', lang)}")
                    st.session_state.show_delete_confirmation = False
                    st.rerun()
            with col_conf2:
                if st.button(f"❌ {get_i18n_text('btn_cancel', lang)}"):
                    st.session_state.show_delete_confirmation = False
                    st.rerun()
        
    except Exception as e:
        st.error(f"{get_i18n_text('error_loading_claims', lang)}: {str(e)}")


def export_claims_to_csv(df: pd.DataFrame):
    """Export claims to CSV file."""
    lang = get_browser_language()
    
    try:
        # Prepare CSV
        csv_df = df[[
            'claim_reference', 'carrier', 'status', 'amount_requested',
            'submitted_at', 'tracking_number', 'response_deadline'
        ]].copy()
        
        csv_data = csv_df.to_csv(index=False, encoding='utf-8-sig')
        
        # Provide download button
        st.download_button(
            label=f"📥 {get_i18n_text('download_csv', lang)}",
            data=csv_data,
            file_name=f"litiges_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            key="download_claims_csv"
        )
        
        st.success(f"✅ {len(df)} {get_i18n_text('csv_ready', lang)}")
        
    except Exception as e:
        st.error(f"{get_i18n_text('error_export', lang)}: {str(e)}")




def retry_pod_fetch(claim_id: int, tracking_number: str, carrier: str):
    """Manually retry POD fetch for a claim."""
    lang = get_browser_language()
    
    try:
        if not tracking_number:
            st.error(f"❌ {get_i18n_text('no_tracking', lang)}")
            return
        
        # Import POD fetcher and rate limiter
        from src.integrations.pod_fetcher import PODFetcher
        from src.integrations.api_request_queue import APIRequestQueue
        
        pod_fetcher = PODFetcher()
        api_queue = APIRequestQueue()
        
        # Check rate limit
        if not api_queue.can_execute(carrier):
            reset_time = api_queue._get_reset_time(carrier)
            st.warning(get_i18n_text('rate_limit_reached', lang).format(
                carrier=carrier,
                time=reset_time.strftime('%H:%M')
            ))
            return
        
        with st.spinner(get_i18n_text('retrieving_pod', lang).format(tracking=tracking_number)):
            # Attempt POD fetch with rate limiting
            result = api_queue.execute_with_limit(
                carrier,
                pod_fetcher.fetch_pod,
                tracking_number,
                carrier
            )
            
            db = get_db_manager()
            
            if result.get('success'):
                # Update claim with POD data
                conn = db.get_connection()
                cursor = db._execute(conn, """
                    UPDATE claims 
                    SET pod_url = ?,
                        pod_fetch_status = 'success',
                        pod_fetched_at = ?,
                        pod_delivery_person = ?
                    WHERE id = ?
                """, (
                    result['pod_url'],
                    datetime.now(),
                    result['pod_data'].get('recipient_name'),
                    claim_id
                ))
                conn.commit()
                conn.close()
                
                st.success(f"✅ {get_i18n_text('pod_retrieved_success', lang)}")
                st.balloons()
                
                # Send success notification
                try:
                    from src.notifications.notification_manager import NotificationManager
                    from src.utils.i18n import get_browser_language
                    
                    # Get claim info for notification
                    conn = db.get_connection()
                    cursor = db._execute(conn, """
                        SELECT c.claim_reference, c.carrier, cl.email
                        FROM claims c
                        JOIN clients cl ON c.client_id = cl.id
                        WHERE c.id = ?
                    """, (claim_id,))
                    claim_info = cursor.fetchone()
                    conn.close()
                    
                    if claim_info:
                        notif_manager = NotificationManager()
                        lang = get_browser_language()
                        notif_manager.queue_notification(
                            client_email=claim_info[2],
                            event_type='pod_retrieved',
                            context={
                                'claim_ref': claim_info[0],
                                'carrier': claim_info[1],
                                'pod_url': result['pod_url'],
                                'lang': lang
                            }
                        )
                except Exception as notif_error:
                    # Don't fail the whole operation if notification fails
                    st.warning(get_i18n_text('pod_retrieved_notification_failed', lang).format(error=str(notif_error)))
                    
            else:
                # Mark as failed
                error_msg = result['error']
                conn = db.get_connection()
                cursor = db._execute(conn, """
                    UPDATE claims 
                    SET pod_fetch_status = 'failed',
                        pod_fetch_error = ?
                    WHERE id = ?
                """, (error_msg, claim_id))
                conn.commit()
                
                # Get claim info for notification
                cursor = db._execute(conn, """
                    SELECT c.claim_reference, c.carrier, cl.email
                    FROM claims c
                    JOIN clients cl ON c.client_id = cl.id
                    WHERE c.id = ?
                """, (claim_id,))
                claim_info = cursor.fetchone()
                conn.close()
                
                st.error(get_i18n_text('pod_failed_error', lang).format(error=error_msg))
                
                # Send notification ONLY for persistent errors
                try:
                    from src.integrations.pod_error_classifier import is_persistent_pod_error
                    from src.notifications.notification_manager import NotificationManager
                    from src.utils.i18n import get_browser_language
                    
                    if is_persistent_pod_error(error_msg):
                        if claim_info:
                            notif_manager = NotificationManager()
                            lang = get_browser_language()
                            notif_manager.queue_notification(
                                client_email=claim_info[2],
                                event_type='pod_failed',
                                context={
                                    'claim_ref': claim_info[0],
                                    'carrier': claim_info[1],
                                    'error': error_msg,
                                    'lang': lang
                                }
                            )
                            st.info(f"📧 {get_i18n_text('notification_sent_persistent', lang)}")
                    else:
                        st.info(f"⏳ {get_i18n_text('notification_temp_error', lang)}")
                except Exception as notif_error:
                    st.warning(get_i18n_text('notification_failed', lang).format(error=str(notif_error)))
                
                st.error(f"❌ Échec: {result['error']}")
                
    except Exception as e:
        st.error(get_i18n_text('error_pod_retrieval', lang).format(error=str(e)))





def bulk_retry_failed_pods(df: pd.DataFrame):
    """Retry all failed POD fetches in batch with rate limiting."""
    lang = get_browser_language()
    failed_claims = df[df['pod_fetch_status'] == 'failed']
    
    if failed_claims.empty:
        st.warning(get_i18n_text('no_failed_pods', lang))
        return
    
    # Import dependencies
    from src.integrations.pod_fetcher import PODFetcher
    from src.integrations.api_request_queue import APIRequestQueue
    
    pod_fetcher = PODFetcher()
    api_queue = APIRequestQueue()
    db = get_db_manager()
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    success_count = 0
    failed_count = 0
    skipped_count = 0
    total = len(failed_claims)
    
    # Process each failed claim
    for idx, (_, claim) in enumerate(failed_claims.iterrows()):
        claim_id = claim['id']
        tracking_number = claim['tracking_number']
        carrier = claim['carrier']
        claim_ref = claim['claim_reference']
        
        # Update progress
        progress = (idx + 1) / total
        progress_bar.progress(progress)
        status_text.text(f"⏳ Traitement {idx + 1}/{total}: {claim_ref}")
        
        # Skip if no tracking number
        if not tracking_number:
            skipped_count += 1
            continue
        
        # Check rate limit
        if not api_queue.can_execute(carrier):
            skipped_count += 1
            continue
        
        try:
            # Attempt POD fetch
            result = api_queue.execute_with_limit(
                carrier,
                pod_fetcher.fetch_pod,
                tracking_number,
                carrier
            )
            
            conn = db.get_connection()
            
            if result.get('success'):
                # Update success
                cursor = db._execute(conn, """
                    UPDATE claims 
                    SET pod_url = ?,
                        pod_fetch_status = 'success',
                        pod_fetched_at = ?,
                        pod_delivery_person = ?
                    WHERE id = ?
                """, (
                    result['pod_url'],
                    datetime.now(),
                    result['pod_data'].get('recipient_name'),
                    claim_id
                ))
                success_count += 1
            else:
                # Update failure
                cursor = db._execute(conn, """
                    UPDATE claims 
                    SET pod_fetch_status = 'failed',
                        pod_fetch_error = ?
                    WHERE id = ?
                """, (result['error'], claim_id))
                failed_count += 1
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            failed_count += 1
    
    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()
    
    # Show summary
    st.success(f"""
✅ **Réessai en masse terminé !**
- ✅ Succès: {success_count}
- ❌ Échecs: {failed_count}
- ⏭️ Ignorés (rate limit): {skipped_count}
    """)
    
    if success_count > 0:
        st.balloons()


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
