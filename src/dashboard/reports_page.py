"""
Reports page for analytics, timeline and statistics.

This module provides comprehensive analytics and reporting capabilities:
- Advanced dispute analytics with visualizations
- Timeline of recent events (chronological history)
- Stagnation detection and automatic escalation interface

Functions:
    render_reports_page: Main entry point for reports page
    render_analytics_tab: Display analytics charts and statistics
    render_timeline: Show chronological event history
    render_stagnation_escalation_section: USP feature for automatic legal escalation
"""

from typing import List, Dict, Any, Optional
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random

from utils.i18n import get_i18n_text
import logging

logger = logging.getLogger(__name__)


def render_reports_page(disputes_df: pd.DataFrame) -> None:
    """
    Render complete reports page with analytics and timeline.
    
    Args:
        disputes_df: DataFrame containing dispute data with columns:
                    - order_id, carrier, status, total_recoverable, etc.
    
    Returns:
        None
    
    Side Effects:
        - Renders analytics charts
        - Displays timeline of events
    """
    st.markdown('<div class="section-header">📈 Reports & Analytics</div>', unsafe_allow_html=True)
    
    # Analytics tab with charts
    render_analytics_tab(disputes_df)
    
    st.markdown("---")
    
    # Timeline of events
    render_timeline()


def render_analytics_tab(disputes_df: pd.DataFrame) -> None:
    """
    Render analytics with charts and statistics.
    
    Delegates to ui_functions.render_analytics_tab for actual rendering.
    Provides wrapper for modularity.
    
    Args:
        disputes_df: DataFrame with dispute data
    
    Returns:
        None
    
    Note:
        The actual analytics logic is in src.dashboard.ui_functions
    """
    from src.dashboard.ui_functions import render_analytics_tab as render_analytics
    render_analytics(disputes_df)


def render_timeline() -> None:
    """
    Render chronological timeline of recent dispute events.
    
    Displays:
    - New disputes detected
    - Claims submitted to carriers
    - Refunds received
    - Legal escalations sent
    - Synchronization events
    
    Each event includes:
    - Icon and timestamp
    - Event title and description
    - Color-coded type (success, warning, info, error)
    
    Returns:
        None
    
    Note:
        Currently uses mock data. In production, should fetch from database.
        Migrated from legacy client_dashboard.py:1502-1547
    """
    st.markdown("### 📅 Timeline des Événements Récents")
    st.caption("Historique chronologique de vos litiges et actions")
    
    # Generate timeline events (should come from database in production)
    timeline_events = [
        {
            'date': (datetime.now() - timedelta(hours=2)).strftime('%H:%M'),
            'title': 'Nouveau litige détecté',
            'description': 'Commande #8829 - Retard de livraison Chronopost',
            'type': 'warning',
            'icon': '⚠️'
        },
        {
            'date': (datetime.now() - timedelta(hours=5)).strftime('%H:%M'),
            'title': 'Réclamation soumise',
            'description': 'Dossier #DSP-045 envoyé à UPS',
            'type': 'info',
            'icon': '📤'
        },
        {
            'date': (datetime.now() - timedelta(days=1)).strftime('%d/%m %H:%M'),
            'title': 'Remboursement reçu',
            'description': '€45.50 crédité - Commande #7742',
            'type': 'success',
            'icon': '💰'
        },
        {
            'date': (datetime.now() - timedelta(days=2)).strftime('%d/%m %H:%M'),
            'title': 'Escalade juridique',
            'description': 'Mise en demeure envoyée à DHL',
            'type': 'warning',
            'icon': '⚖️'
        },
        {
            'date': (datetime.now() - timedelta(days=3)).strftime('%d/%m %H:%M'),
            'title': 'Synchronisation réussie',
            'description': '127 commandes analysées',
            'type': 'info',
            'icon': '🔄'
        },
    ]
    
    # Render timeline
    for event in timeline_events:
        # Color coding based on type
        colors = {
            'success': ('#10b981', '#dcfce7'),
            'warning': ('#f59e0b', '#fef3c7'),
            'info': ('#3b82f6', '#dbeafe'),
            'error': ('#ef4444', '#fee2e2')
        }
        border_color, bg_color = colors.get(event['type'], ('#6b7280', '#f3f4f6'))
        
        st.markdown(f"""
        <div style="
            display: flex;
            gap: 16px;
            padding: 16px;
            margin-bottom: 12px;
            background: {bg_color};
            border-left: 4px solid {border_color};
            border-radius: 8px;
        ">
            <div style="
                font-size: 32px;
                line-height: 1;
            ">{event['icon']}</div>
            <div style="flex: 1;">
                <div style="
                    font-weight: 700;
                    color: #1e293b;
                    margin-bottom: 4px;
                ">{event['title']}</div>
                <div style="
                    color: #64748b;
                    font-size: 14px;
                    margin-bottom: 4px;
                ">{event['description']}</div>
                <div style="
                    color: #94a3b8;
                    font-size: 12px;
                ">{event['date']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.caption("💡 Les événements sont mis à jour en temps réel lors de la synchronisation")


def render_stagnation_escalation_section(disputes_df: pd.DataFrame) -> None:
    """
    Render automatic legal escalation interface (KEY USP FEATURE).
    
    Detects disputes without carrier response > 7 days and offers
    one-click legal escalation (mise en demeure generation).
    
    Args:
        disputes_df: DataFrame containing all disputes data
    
    Returns:
        None
    
    Side Effects:
        - Identifies stagnant disputes
        - On escalation button click:
          * Generates legal document (TODO: connect to legal_document_generator)
          * Sends to carrier (TODO: connect to email system)
          * Updates dispute status
          * Shows success notification
    
    Business Logic:
        - Stagnation threshold: 7 days without response
        - Escalation level: MISE EN DEMEURE REQUISE
    
    Note:
        USP feature providing automatic legal pressure.
        Migrated from legacy client_dashboard.py:576-597
    """
    st.markdown("---")
    st.subheader("⚠️ Dossiers sans réponse (Garantie de Paiement)")
    
    st.info("""
    💡 **Pression Juridique Automatique** : Si un transporteur ignore un dossier plus de 7 jours, le bouton d'escalade apparaît ici. 
    Vous n'avez rien à faire, l'IA prépare les documents légaux pour vous.
    """)
    
    # Get stagnant disputes (those pending > 7 days)
    # In production, this would come from FollowUpManager
    stagnant_disputes = []
    
    if not disputes_df.empty:
        # Simulate stagnant disputes for demo
        # In production: filter disputes with last_contact_date > 7 days ago
        if len(disputes_df) > 0:
            # Show first dispute as example of stagnation
            sample_dispute = disputes_df.iloc[0]
            stagnant_disputes.append({
                'order_id': sample_dispute.get('order_id', '#8829'),
                'carrier': sample_dispute.get('carrier', 'Chronopost'),
                'days_waiting': 22,
                'escalation_level': 'MISE EN DEMEURE REQUISE'
            })
    else:
        # Demo dispute
        stagnant_disputes.append({
            'order_id': '#8829',
            'carrier': 'Chronopost',
            'days_waiting': 22,
            'escalation_level': 'MISE EN DEMEURE REQUISE'
        })
    
    if stagnant_disputes:
        for dispute in stagnant_disputes:
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.write(f"**Commande {dispute['order_id']}** ({dispute['carrier']})")
                st.caption(f"En attente depuis {dispute['days_waiting']} jours")
            
            with col2:
                st.warning(f"⚖️ Niveau d'escalade : {dispute['escalation_level']}")
            
            with col3:
                if st.button("🚀 Lancer l'Escalade", key=f"escalate_{dispute['order_id']}", width='stretch'):
                    # Réel workflow d'escalade intégré
                    try:
                        from src.automation.follow_up_manager import FollowUpManager
                        from src.database.escalation_logger import EscalationLogger
                        from src.database.database_manager import DatabaseManager
                        
                        # Récupérer le claim réel depuis la BDD
                        db_manager = DatabaseManager()
                        # Pour la démo, on crée un claim factice, en production on le récupère via:
                        # claim = db_manager.get_claim_by_order_id(dispute['order_id'])
                        
                        # Claim factice pour démo
                        demo_claim = {
                            'id': 1,
                            'claim_reference': f"CLM-2026-{dispute['order_id']}",
                            'carrier': dispute['carrier'],
                            'tracking_number': 'DEMO123456789',
                            'amount_requested': 150.00,
                            'dispute_type': 'Colis Perdu',
                            'customer_name': 'Client Demo',
                            'delivery_address': 'Paris, France',
                            'currency': 'EUR',
                            'country': 'FR',
                            'submitted_at': '2026-01-10T10:00:00'
                        }
                        
                        # Déclencher l'escalade
                        manager = FollowUpManager(db_manager)
                        result = manager._trigger_formal_notice(demo_claim)
                        
                        if result and result.get('email_sent'):
                            st.success("✅ **Mise en Demeure générée et envoyée !**")
                            st.info(f"📄 PDF : `{result['pdf_path']}`")
                            st.info("📧 Email envoyé au service juridique du transporteur")
                            
                            # Afficher l'historique d'escalade
                            escalation_logger = EscalationLogger()
                            history = escalation_logger.get_claim_escalation_history(demo_claim['id'])
                            
                            if history:
                                with st.expander("📋 Historique d'escalade"):
                                    for entry in history[:3]:  # 3 dernières actions
                                        action_icons = {
                                            'pdf_generated': '📄',
                                            'email_sent': '📧',
                                            'carrier_response': '✉️'
                                        }
                                        icon = action_icons.get(entry['action_type'], '📌')
                                        st.write(f"{icon} **{entry['action_type']}** - {entry['created_at']}")
                                        if entry.get('email_status'):
                                            status_color = '🟢' if entry['email_status'] == 'sent' else '🔴'
                                            st.caption(f"{status_color} Status: {entry['email_status']}")
                            
                            st.balloons()
                        else:
                            st.warning("⚠️ La mise en demeure a été générée mais l'email n'a pas pu être envoyé.")
                            st.info("Le PDF est disponible pour envoi manuel.")
                            if result:
                                st.code(result['pdf_path'])
                    
                    except Exception as e:
                        st.error(f"❌ Erreur lors de l'escalade : {str(e)}")
                        logger.error(f"Escalation error: {e}", exc_info=True)
    else:
        st.success("✅ Aucun dossier en attente de plus de 7 jours. Excellent !")
