"""
Carrier breakdown and statistics component.

This module provides detailed breakdown of disputes by shipping carrier.
"""

from typing import Dict, Any
import pandas as pd
import streamlit as st


def render_carrier_breakdown(disputes_df: pd.DataFrame) -> None:
    """
    Render comprehensive breakdown of disputes by carrier.
    
    Displays aggregated statistics for each shipping carrier including:
    - Total number of disputes
    - Total recoverable amount
    - Success rate (recovered / total)
    - Average dispute value
    - Status distribution
    
    Args:
        disputes_df: DataFrame containing disputes data with columns:
                    - carrier: Shipping carrier name (str)
                    - total_recoverable: Amount in EUR  (float)
                    - status: Dispute status (str)
    
    Returns:
        None
    
    Side Effects:
        - Renders Streamlit UI components
        - Displays interactive charts
    
    Example:
        >>> df = pd.DataFrame({'carrier': ['UPS', 'DHL'], 'total_recoverable': [100, 200]})
        >>> render_carrier_breakdown(df)
    """
    st.markdown("### 📦 Breakdown par Transporteur")
    st.caption("Analyse détaillée de la performance par transporteur")
    
    if disputes_df.empty:
        st.info("Aucune donnée de litige disponible")
        return
    
    # Group by carrier
    carrier_stats = disputes_df.groupby('carrier').agg({
        'order_id': 'count',
        'total_recoverable': ['sum', 'mean']
    }).reset_index()
    
    carrier_stats.columns = ['carrier', 'total_disputes', 'total_recoverable', 'avg_recoverable']
    
    # Calculate success rate per carrier
    success_rates = []
    for carrier in carrier_stats['carrier']:
        carrier_df = disputes_df[disputes_df['carrier'] == carrier]
        recovered = carrier_df[carrier_df['status'] == 'recovered']['total_recoverable'].sum()
        total = carrier_df['total_recoverable'].sum()
        success_rate = (recovered / total * 100) if total > 0 else 0
        success_rates.append(success_rate)
    
    carrier_stats['success_rate'] = success_rates
    
    # Sort by total recoverable descending
    carrier_stats = carrier_stats.sort_values('total_recoverable', ascending=False)
    
    # Display as cards
    for idx, row in carrier_stats.iterrows():
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
            
            # Carrier icon mapping
            carrier_icons = {
                'chronopost': '📮',
                'ups': '📦',
                'dhl': '✈️',
                'fedex': '🚚',
                'colissimo': '📬',
                'dpd': '🚛',
                'gls': '🚐',
                'tnt': '🛣️'
            }
            
            carrier_name = row['carrier']
            icon = carrier_icons.get(carrier_name.lower(), '📦')
            
            with col1:
                st.metric(
                    label=f"{icon} {carrier_name}",
                    value=f"{int(row['total_disputes'])} litiges"
                )
            
            with col2:
                st.metric(
                    label="Montant Total",
                    value=f"{row['total_recoverable']:.2f}€"
                )
            
            with col3:
                st.metric(
                    label="Montant Moyen",
                    value=f"{row['avg_recoverable']:.2f}€"
                )
            
            with col4:
                success_color = "🟢" if row['success_rate'] > 70 else ("🟡" if row['success_rate'] > 40 else "🔴")
                st.metric(
                    label="Taux de Succès",
                    value=f"{success_color} {row['success_rate']:.1f}%"
                )
            
            st.markdown("---")
    
    # Summary stats
    st.markdown("### 📊 Statistiques Globales")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_carriers = len(carrier_stats)
        st.info(f"**{total_carriers}** transporteurs actifs")
    
    with col2:
        best_carrier = carrier_stats.iloc[0]['carrier'] if not carrier_stats.empty else "N/A"
        st.success(f"**Meilleur taux**: {best_carrier}")
    
    with col3:
        worst_carrier = carrier_stats.iloc[-1]['carrier'] if not carrier_stats.empty else "N/A"
        st.warning(f"**À améliorer**: {worst_carrier}")
