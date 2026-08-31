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
    from utils.i18n import get_browser_language, get_i18n_text
    lang = get_browser_language()
    st.markdown(f'<div class="section-header">📈 {get_i18n_text("reports_header", lang)}</div>', unsafe_allow_html=True)
    
    # Analytics tab with charts
    render_analytics_tab(disputes_df)
    
    st.markdown("---")
    
    # Timeline of events
    render_timeline(disputes_df)


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


def _build_real_timeline_events(disputes_df: pd.DataFrame) -> list:
    """Construit des événements de timeline à partir de VRAIES données de
    dossiers (created_at, payment_date/payment_status, last_follow_up_at/
    follow_up_level). Retourne une liste vide si aucune donnée réelle
    exploitable — à ne PAS confondre avec "pas d'internet" : ça veut juste
    dire qu'aucun de ces événements n'a encore eu lieu pour ce compte.
    """
    events = []
    if disputes_df is None or disputes_df.empty:
        return events

    for _, row in disputes_df.iterrows():
        ref = row.get("claim_reference", "N/A")
        carrier = row.get("carrier", "N/A")

        created_raw = row.get("created_at")
        if created_raw:
            try:
                dt = pd.to_datetime(created_raw).to_pydatetime()
                events.append({
                    "dt": dt,
                    "title": "Nouveau dossier créé",
                    "description": f"{ref} — {carrier}",
                    "type": "info",
                    "icon": "📤",
                })
            except Exception:
                pass

        if str(row.get("payment_status", "")).lower() == "paid" and row.get("payment_date"):
            try:
                dt = pd.to_datetime(row["payment_date"]).to_pydatetime()
                amount = row.get("accepted_amount") or row.get("total_recoverable") or 0
                events.append({
                    "dt": dt,
                    "title": "Remboursement reçu",
                    "description": f"{amount:.2f}€ crédité — {ref}",
                    "type": "success",
                    "icon": "💰",
                })
            except Exception:
                pass

        level = int(row.get("follow_up_level") or 0)
        last_follow_up = row.get("last_follow_up_at")
        if level > 0 and last_follow_up:
            try:
                dt = pd.to_datetime(last_follow_up).to_pydatetime()
                level_titles = {
                    1: "Relance envoyée (demande de statut)",
                    2: "Avertissement envoyé au transporteur",
                    3: "Mise en demeure envoyée",
                }
                events.append({
                    "dt": dt,
                    "title": level_titles.get(level, "Relance envoyée"),
                    "description": f"{ref} — {carrier}",
                    "type": "warning" if level < 3 else "error",
                    "icon": "⚖️" if level == 3 else "🔔",
                })
            except Exception:
                pass

    events.sort(key=lambda e: e["dt"], reverse=True)
    return events[:8]


def render_timeline(disputes_df: pd.DataFrame = None) -> None:
    """
    Render chronological timeline of recent dispute events.

    31/08/2026 (audit complet) : cette fonction affichait auparavant TOUJOURS
    les 5 mêmes événements fictifs codés en dur ("Commande #8829", "Dossier
    #DSP-045"...), quel que soit le compte, réel ou vide, Test ou Prod — la
    docstring d'origine le disait elle-même ("Currently uses mock data").
    Elle utilise maintenant les VRAIS événements du compte (création de
    dossier, remboursement reçu, relance envoyée) quand ils existent. Les
    données de démo ne sont conservées QUE pour un compte en mode Test qui
    n'a encore aucune vraie donnée — jamais en Prod, où une absence de
    données réelles est maintenant affichée honnêtement comme telle.

    Returns:
        None
    """
    from utils.i18n import get_browser_language, get_i18n_text
    lang = get_browser_language()
    st.markdown(f"### 📅 {get_i18n_text('timeline_recent_events', lang)}")
    st.caption(get_i18n_text('timeline_caption', lang))

    real_events = _build_real_timeline_events(disputes_df)

    if real_events:
        timeline_events = [
            {
                "date": e["dt"].strftime("%d/%m %H:%M"),
                "title": e["title"],
                "description": e["description"],
                "type": e["type"],
                "icon": e["icon"],
            }
            for e in real_events
        ]
    else:
        is_test_mode = st.session_state.get("env_mode") == "TEST"
        if not is_test_mode:
            st.caption("Aucun événement pour le moment — les dossiers créés, relancés ou remboursés apparaîtront ici.")
            return
        # Mode Test sans aucune vraie donnée : on garde des événements de
        # démonstration (clairement demandé — un compte Test doit pouvoir
        # visualiser la fonctionnalité même sans dossier réel), inchangés
        # depuis la version d'origine.
        timeline_events = [
            {
                'date': (datetime.now() - timedelta(hours=2)).strftime('%H:%M'),
                'title': 'Nouveau litige détecté (démo)',
                'description': 'Commande #8829 - Retard de livraison Chronopost',
                'type': 'warning',
                'icon': '⚠️'
            },
            {
                'date': (datetime.now() - timedelta(hours=5)).strftime('%H:%M'),
                'title': 'Réclamation soumise (démo)',
                'description': 'Dossier #DSP-045 envoyé à UPS',
                'type': 'info',
                'icon': '📤'
            },
            {
                'date': (datetime.now() - timedelta(days=1)).strftime('%d/%m %H:%M'),
                'title': 'Remboursement reçu (démo)',
                'description': '€45.50 crédité - Commande #7742',
                'type': 'success',
                'icon': '💰'
            },
            {
                'date': (datetime.now() - timedelta(days=2)).strftime('%d/%m %H:%M'),
                'title': 'Escalade juridique (démo)',
                'description': 'Mise en demeure envoyée à DHL',
                'type': 'warning',
                'icon': '⚖️'
            },
            {
                'date': (datetime.now() - timedelta(days=3)).strftime('%d/%m %H:%M'),
                'title': 'Synchronisation réussie (démo)',
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

    # 31/08/2026 (audit complet) : cette section fabriquait auparavant un
    # faux dossier "Commande #8829 (Chronopost) — MISE EN DEMEURE REQUISE"
    # dès que le compte n'avait aucun litige réel, avec un bouton qui
    # déclenchait un vrai envoi d'email vers l'adresse réelle du service
    # réclamations du transporteur avec des données inventées (voir
    # l'historique de ce fichier). Neutralisé une première fois (affichage
    # "à venir"), puis la vraie détection + le vrai déclenchement ont été
    # construits : un worker d'arrière-plan (src/workers/reminder_worker.py,
    # démarré à la connexion) scanne maintenant réellement les dossiers en
    # base toutes les 4h et déclenche les relances J+7/J+14/J+21 — envoi
    # réel au transporteur pour un compte Prod, simulé (rien envoyé) pour un
    # compte Test. Cet écran est maintenant un affichage EN LECTURE SEULE
    # de ce que ce worker a constaté sur VOS dossiers ; il ne déclenche plus
    # rien lui-même (l'automatisation tourne déjà seule en arrière-plan).
    st.info("""
    💡 **Pression Juridique Automatique** : si un transporteur ignore un dossier plus de 7 jours,
    l'IA relance automatiquement en arrière-plan (statut, avertissement, puis mise en demeure à J+21).
    Vous n'avez rien à faire.
    """)

    if disputes_df.empty or "created_at" not in disputes_df.columns:
        st.caption("Aucun dossier à surveiller pour le moment.")
        return

    from utils.i18n import get_browser_language
    lang = get_browser_language()

    eligible_statuses = ("submitted", "pending", "waiting_response", "under_review")
    level_labels = {
        0: "🟡 En attente (relance à venir)",
        1: "🟡 Relance niveau 1 envoyée (demande de statut)",
        2: "🟠 Relance niveau 2 envoyée (avertissement)",
        3: "🔴 Mise en demeure envoyée (niveau 3)",
    }

    now = datetime.now()
    stagnant_rows = []
    for _, row in disputes_df.iterrows():
        status = row.get("status", "")
        created_raw = row.get("created_at", "")
        if status not in eligible_statuses or not created_raw:
            continue
        try:
            created_at = pd.to_datetime(created_raw)
        except Exception:
            continue
        days_waiting = (now - created_at.to_pydatetime().replace(tzinfo=None)).days
        if days_waiting < 7:
            continue
        stagnant_rows.append({
            "reference": row.get("claim_reference", "N/A"),
            "carrier": row.get("carrier", "N/A"),
            "days_waiting": days_waiting,
            "level": int(row.get("follow_up_level") or 0),
        })

    if not stagnant_rows:
        st.caption("✅ Aucun dossier en attente depuis plus de 7 jours actuellement.")
        return

    stagnant_rows.sort(key=lambda r: r["days_waiting"], reverse=True)
    for r in stagnant_rows:
        st.markdown(
            f"**{r['reference']}** — {r['carrier']} — en attente depuis **{r['days_waiting']} jours**  \n"
            f"{level_labels.get(r['level'], level_labels[0])}"
        )
    st.caption(
        "Ces dossiers sont surveillés automatiquement par le worker de relance "
        "(scan toutes les 4h) — aucune action manuelle n'est nécessaire."
    )
