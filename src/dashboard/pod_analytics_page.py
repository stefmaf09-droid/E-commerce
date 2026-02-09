"""
POD Analytics Dashboard

Comprehensive analytics for POD (Proof of Delivery) retrieval performance.

Displays:
- Overall POD retrieval metrics (success rate, avg time)
- Success rates by carrier
- Retry performance analysis
- Time-based trends
- Error classification breakdown

Accessible from claims management page or main nav.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

from src.database.database_manager import get_db_manager
from src.utils.i18n import get_i18n_text, get_browser_language
import plotly.express as px
import plotly.graph_objects as go


def render_pod_analytics_page():
    """Main entry point for POD analytics dashboard."""
    
    lang = get_browser_language()
    
    # Header
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 24px;
        border-radius: 12px;
        margin: 0 0 24px 0;
        color: white;
    ">
        <h1 style="margin: 0; font-size: 28px; font-weight: 700;">
            📊 {get_i18n_text('pod_analytics_title', lang)}
        </h1>
        <p style="margin: 8px 0 0 0; font-size: 16px; opacity: 0.9;">
            {get_i18n_text('pod_analytics_subtitle', lang)}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # ========== ADVANCED FILTERS SIDEBAR ==========
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🔍 Advanced Filters")
        
        # Status filter
        status_options = st.multiselect(
            "📊 Status",
            options=['success', 'failed', 'pending'],
            default=['success', 'failed', 'pending'],
            format_func=lambda x: {
                'success': '✅ Success',
                'failed': '❌ Failed',
                'pending': '⏳ Pending'
            }.get(x, x)
        )
        
        # Carrier filter (get available carriers from DB)
        db = get_db_manager()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT carrier FROM claims WHERE carrier IS NOT NULL ORDER BY carrier")
        available_carriers = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        carrier_filter = st.multiselect(
            "🚚 Carriers",
            options=available_carriers,
            default=available_carriers if len(available_carriers) <= 5 else []
        )
        
        # Date range: preset or custom
        date_mode = st.radio(
            "📅 Date Range",
            options=['preset', 'custom'],
            format_func=lambda x: 'Preset' if x == 'preset' else 'Custom Range',
            horizontal=True
        )
        
        if date_mode == 'preset':
            time_range = st.selectbox(
                "Select Range",
                options=['7d', '30d', '90d', 'all'],
                format_func=lambda x: {
                    '7d': get_i18n_text('last_7_days', lang),
                    '30d': get_i18n_text('last_30_days', lang),
                    '90d': get_i18n_text('last_90_days', lang),
                    'all': get_i18n_text('all_time', lang)
                }[x],
                index=1,
                label_visibility='collapsed'
            )
            custom_start = custom_end = None
        else:
            from datetime import datetime, timedelta
            col_a, col_b = st.columns(2)
            with col_a:
                custom_start = st.date_input(
                    "From",
                    value=datetime.now() - timedelta(days=30),
                    max_value=datetime.now().date()
                )
            with col_b:
                custom_end = st.date_input(
                    "To",
                    value=datetime.now().date(),
                    max_value=datetime.now().date()
                )
            time_range = 'custom'
        
        # Error type filter (for failed only)
        if 'failed' in status_options:
            error_filter = st.text_input(
                "⚠️ Error Contains",
                placeholder="e.g., timeout, 404",
                help="Filter errors by keyword"
            )
        else:
            error_filter = ""
        
        # Claim reference search
        search_ref = st.text_input(
            "🔎 Search Claim Ref",
            placeholder="REF-",
            help="Search specific claim"
        )
        
        # ========== HELP SECTION ==========
        st.markdown("---")
        with st.expander("ℹ️ Help & Tips"):
            st.markdown("""
            **📊 Filters:**
            - **Status**: Filter by success/failed/pending
            - **Carriers**: Select specific carriers to analyze
            - **Date Range**: Use preset (7d, 30d...) or custom dates
            - **Error Search**: Find claims with specific errors
            
            **📥 CSV Export:**
            - Click export button → Download appears
            - Files include timestamp for tracking
            - Open in Excel or import to BI tools
            
            **📈 Charts:**
            - Hover over points to see details
            - Click and drag to zoom
            - Double-click to reset zoom
            
            **⚠️ Email Alerts:**
            - Automatic alerts sent when:
              - 10+ consecutive failures (Critical)
              - 50+ failures in 24 hours (Warning)
            - Check your admin email inbox
            """)
    
    # ========== BUILD FILTERS DICT ==========
    filters = {
        'time_range': time_range,
        'custom_start': custom_start if date_mode == 'custom' else None,
        'custom_end': custom_end if date_mode == 'custom' else None,
        'statuses': status_options,
        'carriers': carrier_filter,
        'error_keyword': error_filter,
        'search_ref': search_ref
    }
    
    # Load analytics data with filters
    analytics_data = _load_pod_analytics_data(filters)
    
    if not analytics_data:
        st.warning(get_i18n_text('no_pod_data', lang))
        return
    
    # ========== CSV EXPORT BUTTONS ==========
    st.markdown("### 📥 Export Data")
    col1, col2, col3, col4 = st.columns(4)
    
    from datetime import datetime
    import csv
    import io
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    with col1:
        # Export overview metrics
        if st.button("📊 Overview", help="Export overview metrics"):
            csv_buffer = io.StringIO()
            writer = csv.writer(csv_buffer)
            writer.writerow(['Metric', 'Value'])
            writer.writerow(['Total Claims', analytics_data['total']])
            writer.writerow(['Success', analytics_data['success']])
            writer.writerow(['Failed', analytics_data['failed']])
            writer.writerow(['Pending', analytics_data['pending']])
            writer.writerow(['Success Rate (%)', analytics_data['success_rate']])
            writer.writerow(['Avg Fetch Time (hours)', analytics_data['avg_fetch_time']])
            
            st.download_button(
                label="⬇️ Download",
                data=csv_buffer.getvalue(),
                file_name=f"pod_overview_{timestamp}.csv",
                mime="text/csv"
            )
    
    with col2:
        # Export carrier breakdown
        if st.button("🚚 Carriers", help="Export carrier performance"):
            csv_buffer = io.StringIO()
            writer = csv.writer(csv_buffer)
            writer.writerow(['Carrier', 'Total', 'Success', 'Failed', 'Success Rate (%)', 'Avg Time (hours)'])
            
            for carrier in analytics_data['carriers']:
                writer.writerow([
                    carrier['name'],
                    carrier['total'],
                    carrier['success'],
                    carrier['failed'],
                    carrier['success_rate'],
                    carrier['avg_fetch_time']
                ])
            
            st.download_button(
                label="⬇️ Download",
                data=csv_buffer.getvalue(),
                file_name=f"pod_carriers_{timestamp}.csv",
                mime="text/csv"
            )
    
    with col3:
        # Export retry analysis
        if st.button("🔄 Retries", help="Export retry analysis"):
            csv_buffer = io.StringIO()
            writer = csv.writer(csv_buffer)
            writer.writerow(['Retry Count', 'Total Attempts', 'Success', 'Success Rate (%)'])
            
            for retry in analytics_data.get('retries', []):
                success_rate = (retry['success'] / retry['count'] * 100) if retry['count'] > 0 else 0
                writer.writerow([
                    retry['retry_count'],
                    retry['count'],
                    retry['success'],
                    f"{success_rate:.1f}"
                ])
            
            st.download_button(
                label="⬇️ Download",
                data=csv_buffer.getvalue(),
                file_name=f"pod_retries_{timestamp}.csv",
                mime="text/csv"
            )
    
    with col4:
        # Export error log
        if st.button("⚠️ Errors", help="Export error breakdown"):
            csv_buffer = io.StringIO()
            writer = csv.writer(csv_buffer)
            writer.writerow(['Error Type', 'Occurrences'])
            
            for error in analytics_data.get('errors', []):
                writer.writerow([
                    error['error'],
                    error['count']
                ])
            
            st.download_button(
                label="⬇️ Download",
                data=csv_buffer.getvalue(),
                file_name=f"pod_errors_{timestamp}.csv",
                mime="text/csv"
            )
    
    st.markdown("---")
    
    # Overview metrics
    _render_overview_metrics(analytics_data, lang)
    
    st.markdown("---")
    
    # Carrier performance
    _render_carrier_performance(analytics_data, lang)
    
    st.markdown("---")
    
    # Retry analysis
    _render_retry_analysis(analytics_data, lang)
    
    st.markdown("---")
    
    # Error breakdown
    _render_error_breakdown(analytics_data, lang)
    
    st.markdown("---")
    
    # Time trends
    _render_time_trends(analytics_data, lang)


def _load_pod_analytics_data(filters: Dict) -> Dict:
    """
    Load POD analytics data from database with filters.
    
    Args:
        filters: Dictionary with filter parameters:
            - time_range: '7d', '30d', '90d', 'all', or 'custom'
            - custom_start: datetime for custom range start
            - custom_end: datetime for custom range end
            - statuses: List of status values to include
            - carriers: List of carriers to include
            - error_keyword: Keyword to search in errors
            - search_ref: Claim reference to search
    
    Returns:
        Dictionary with analytics data
    """
    db = get_db_manager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Build WHERE clauses from filters
    where_clauses = ["tracking_number IS NOT NULL AND tracking_number != ''"]
    
    # Date filter
    time_range = filters.get('time_range', '30d')
    if time_range == 'custom':
        custom_start = filters.get('custom_start')
        custom_end = filters.get('custom_end')
        if custom_start:
            where_clauses.append(f"created_at >= '{custom_start} 00:00:00'")
        if custom_end:
            where_clauses.append(f"created_at <= '{custom_end} 23:59:59'")
    elif time_range != 'all':
        days = int(time_range[:-1])
        cutoff_date = datetime.now() - timedelta(days=days)
        where_clauses.append(f"created_at >= '{cutoff_date.isoformat()}'")
    
    # Status filter
    statuses = filters.get('statuses', [])
    if statuses:
        status_list = ','.join([f"'{s}'" for s in statuses])
        where_clauses.append(f"pod_fetch_status IN ({status_list})")
    
    # Carrier filter
    carriers = filters.get('carriers', [])
    if carriers:
        carrier_list = ','.join([f"'{c}'" for c in carriers])
        where_clauses.append(f"carrier IN ({carrier_list})")
    
    # Error keyword filter
    error_keyword = filters.get('error_keyword', '')
    if error_keyword:
        where_clauses.append(f"pod_fetch_error LIKE '%{error_keyword}%'")
    
    # Claim reference search
    search_ref = filters.get('search_ref', '')
    if search_ref:
        where_clauses.append(f"claim_reference LIKE '%{search_ref}%'")
    
    where_clause = ' AND '.join(where_clauses)
    
    try:
        # Overall stats
        cursor.execute(f"""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN pod_fetch_status = 'success' THEN 1 ELSE 0 END) as success,
                SUM(CASE WHEN pod_fetch_status = 'failed' THEN 1 ELSE 0 END) as failed,
                SUM(CASE WHEN pod_fetch_status = 'pending' THEN 1 ELSE 0 END) as pending,
                AVG(CASE 
                    WHEN pod_fetched_at IS NOT NULL AND created_at IS NOT NULL 
                    THEN (julianday(pod_fetched_at) - julianday(created_at)) * 24 
                    ELSE NULL 
                END) as avg_fetch_hours
            FROM claims
            WHERE {where_clause}
        """)
        
        overall = cursor.fetchone()
        
        # Carrier breakdown
        cursor.execute(f"""
            SELECT 
                carrier,
                COUNT(*) as total,
                SUM(CASE WHEN pod_fetch_status = 'success' THEN 1 ELSE 0 END) as success,
                SUM(CASE WHEN pod_fetch_status = 'failed' THEN 1 ELSE 0 END) as failed,
                AVG(CASE 
                    WHEN pod_fetched_at IS NOT NULL AND created_at IS NOT NULL 
                    THEN (julianday(pod_fetched_at) - julianday(created_at)) * 24 
                    ELSE NULL 
                END) as avg_fetch_hours
            FROM claims
            WHERE {where_clause}
            GROUP BY carrier
            ORDER BY total DESC
        """)
        
        carriers_data = cursor.fetchall()
        
        # Retry analysis (if columns exist)
        try:
            cursor.execute(f"""
                SELECT 
                    pod_retry_count,
                    COUNT(*) as count,
                    SUM(CASE WHEN pod_fetch_status = 'success' THEN 1 ELSE 0 END) as success
                FROM claims
                WHERE {where_clause}
                AND pod_retry_count IS NOT NULL 
                AND pod_retry_count > 0
                GROUP BY pod_retry_count
                ORDER BY pod_retry_count
            """)
            retry_data = cursor.fetchall()
        except:
            retry_data = []
        
        # Error breakdown
        cursor.execute(f"""
            SELECT 
                pod_fetch_error,
                COUNT(*) as count
            FROM claims
            WHERE {where_clause}
            AND pod_fetch_status = 'failed'
            AND pod_fetch_error IS NOT NULL
            GROUP BY pod_fetch_error
            ORDER BY count DESC
            LIMIT 10
        """)
        
        errors_data = cursor.fetchall()
        
        # Daily trend (last 30 days)
        cursor.execute(f"""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as total,
                SUM(CASE WHEN pod_fetch_status = 'success' THEN 1 ELSE 0 END) as success
            FROM claims
            WHERE tracking_number IS NOT NULL
            AND created_at >= datetime('now', '-30 days')
            GROUP BY DATE(created_at)
            ORDER BY date
        """)
        
        trend_data = cursor.fetchall()
        
        conn.close()
        
        return {
            'total': overall[0] or 0,
            'success': overall[1] or 0,
            'failed': overall[2] or 0,
            'pending': overall[3] or 0,
            'avg_fetch_hours': overall[4] or 0,
            'carriers': carriers_data,
            'retries': retry_data,
            'errors': errors_data,
            'trend': trend_data
        }
        
    except Exception as e:
        st.error(f"Error loading analytics: {e}")
        conn.close()
        return None


def _render_overview_metrics(data: Dict, lang: str):
    """Render overview metrics cards."""
    
    st.markdown(f"### 🎯 {get_i18n_text('overview_metrics', lang)}")
    
    total = data['total']
    success = data['success']
    failed = data['failed']
    pending = data['pending']
    avg_hours = data['avg_fetch_hours']
    
    success_rate = (success / total * 100) if total > 0 else 0
    
    # Metrics cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div style="
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            text-align: center;
        ">
            <div style="font-size: 14px; color: #64748b; margin-bottom: 8px;">
                {get_i18n_text('total_pods', lang)}
            </div>
            <div style="font-size: 32px; font-weight: 700; color: #1e293b;">{total}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            text-align: center;
        ">
            <div style="font-size: 14px; color: #64748b; margin-bottom: 8px;">
                {get_i18n_text('success_rate', lang)}
            </div>
            <div style="font-size: 32px; font-weight: 700; color: #10b981;">{success_rate:.1f}%</div>
            <div style="font-size: 12px; color: #64748b; margin-top: 4px;">
                {success} / {total}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            text-align: center;
        ">
            <div style="font-size: 14px; color: #64748b; margin-bottom: 8px;">
                {get_i18n_text('avg_fetch_time', lang)}
            </div>
            <div style="font-size: 32px; font-weight: 700; color: #667eea;">{avg_hours:.1f}h</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div style="
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            text-align: center;
        ">
            <div style="font-size: 14px; color: #64748b; margin-bottom: 8px;">
                {get_i18n_text('failed_pods', lang)}
            </div>
            <div style="font-size: 32px; font-weight: 700; color: #ef4444;">{failed}</div>
            <div style="font-size: 12px; color: #64748b; margin-top: 4px;">
                {pending} {get_i18n_text('pending', lang)}
            </div>
        </div>
        """, unsafe_allow_html=True)


def _render_carrier_performance(data: Dict, lang: str):
    """Render carrier performance breakdown."""
    
    st.markdown(f"### 🚚 {get_i18n_text('carrier_performance', lang)}")
    
    if not data['carriers']:
        st.info(get_i18n_text('no_carrier_data', lang))
        return
    
    # Create DataFrame for display
    carriers_df = pd.DataFrame(data['carriers'], columns=[
        'Carrier', 'Total', 'Success', 'Failed', 'Avg Hours'
    ])
    
    # Add success rate
    carriers_df['Success Rate'] = (carriers_df['Success'] / carriers_df['Total'] * 100).round(1)
    carriers_df['Avg Hours'] = carriers_df['Avg Hours'].fillna(0).round(1)
    
    # Display each carrier as a card
    for _, row in carriers_df.iterrows():
        carrier = row['Carrier']
        total = int(row['Total'])
        success = int(row['Success'])
        failed = int(row['Failed'])
        success_rate = row['Success Rate']
        avg_hours = row['Avg Hours']
        
        # Progress bar
        progress_html = f"""
        <div style="
            width: 100%;
            height: 8px;
            background: #e5e7eb;
            border-radius: 4px;
            overflow: hidden;
        ">
            <div style="
                width: {success_rate}%;
                height: 100%;
                background: linear-gradient(90deg, #10b981 0%, #059669 100%);
            "></div>
        </div>
        """
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"""
            <div style="
                background: white;
                padding: 16px;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.05);
                margin-bottom: 12px;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <div>
                        <span style="font-size: 18px; font-weight: 700; color: #1e293b;">{carrier}</span>
                        <span style="
                            margin-left: 12px;
                            padding: 4px 12px;
                            background: #667eea20;
                            color: #667eea;
                            border-radius: 6px;
                            font-size: 12px;
                            font-weight: 600;
                        ">{total} PODs</span>
                    </div>
                    <div style="font-size: 24px; font-weight: 700; color: #10b981;">
                        {success_rate:.1f}%
                    </div>
                </div>
                {progress_html}
                <div style="display: flex; gap: 24px; margin-top: 12px; font-size: 14px;">
                    <span style="color: #10b981;">✅ {success} {get_i18n_text('success', lang)}</span>
                    <span style="color: #ef4444;">❌ {failed} {get_i18n_text('failed', lang)}</span>
                    <span style="color: #667eea;">⏱️ {avg_hours:.1f}h {get_i18n_text('avg', lang)}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)


def _render_retry_analysis(data: Dict, lang: str):
    """Render retry performance analysis."""
    
    st.markdown(f"### 🔄 {get_i18n_text('retry_analysis', lang)}")
    
    if not data['retries']:
        st.info(get_i18n_text('no_retry_data', lang))
        return
    
    # Create DataFrame
    retry_df = pd.DataFrame(data['retries'], columns=['Retry Count', 'Total', 'Success'])
    retry_df['Success Rate'] = (retry_df['Success'] / retry_df['Total'] * 100).round(1)
    
    # Display as bar chart using st.bar_chart
    chart_data = pd.DataFrame({
        'Success Rate (%)': retry_df['Success Rate'].values
    }, index=[f"Attempt {int(r)}" for r in retry_df['Retry Count']])
    
    st.bar_chart(chart_data, color="#10b981")
    
    # Summary table
    st.markdown(f"""
    <div style="
        background: #f8fafc;
        padding: 16px;
        border-radius: 8px;
        margin-top: 12px;
    ">
        <div style="font-size: 14px; color: #64748b; margin-bottom: 8px;">
            {get_i18n_text('retry_summary', lang)}
        </div>
        <div style="font-size: 12px; color: #475569;">
            {"<br>".join([
                f"• Attempt {int(row['Retry Count'])}: {int(row['Success'])}/{int(row['Total'])} ({row['Success Rate']:.1f}%)"
                for _, row in retry_df.iterrows()
            ])}
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_error_breakdown(data: Dict, lang: str):
    """Render error classification breakdown."""
    
    st.markdown(f"### ⚠️ {get_i18n_text('error_breakdown', lang)}")
    
    if not data['errors']:
        st.success(get_i18n_text('no_errors', lang))
        return
    
    # Display errors as list
    for error_msg, count in data['errors']:
        # Truncate long error messages
        display_error = error_msg[:80] + "..." if len(error_msg) > 80 else error_msg
        
        st.markdown(f"""
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 16px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.05);
            margin-bottom: 8px;
        ">
            <div style="flex: 1; color: #475569; font-size: 14px;">
                {display_error}
            </div>
            <div style="
                padding: 4px 12px;
                background: #fee2e2;
                color: #ef4444;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
            ">
                {count} {get_i18n_text('occurrences', lang)}
            </div>
        </div>
        """, unsafe_allow_html=True)


def _render_time_trends(data: Dict, lang: str):
    """Render time-based trends."""
    
    st.markdown(f"### 📈 {get_i18n_text('time_trends', lang)} (30 {get_i18n_text('days', lang)})")
    
    if not data['trend']:
        st.info(get_i18n_text('no_trend_data', lang))
        return
    
    # Create DataFrame for chart
    trend_df = pd.DataFrame(data['trend'], columns=['Date', 'Total', 'Success'])
    trend_df['Success Rate'] = (trend_df['Success'] / trend_df['Total'] * 100).round(1)
    trend_df = trend_df.set_index('Date')
    
    # Interactive Plotly line chart
    fig = px.line(
        trend_df.reset_index(),
        x='Date',
        y='Success Rate',
        title=None,
        labels={'Success Rate': 'Success Rate (%)', 'Date': 'Date'},
        markers=True
    )
    
    # Customize appearance
    fig.update_traces(
        line_color='#10b981',
        line_width=3,
        marker=dict(size=8, color='#10b981', line=dict(width=2, color='white')),
        hovertemplate='<b>%{x}</b><br>Success Rate: %{y:.1f}%<extra></extra>'
    )
    
    fig.update_layout(
        height=400,
        margin=dict(l=0, r=0, t=20, b=0),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(200,200,200,0.2)',
            title=None
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(200,200,200,0.2)',
            title='Success Rate (%)',
            range=[0, 100]
        ),
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Stats
    avg_daily = trend_df['Total'].mean()
    st.caption(f"{get_i18n_text('avg_daily_pods', lang)}: {avg_daily:.1f}")


def check_and_send_critical_pod_alerts():
    """
    Check for critical POD failure conditions and send email alerts.
    
    Criteria for alert:
    - More than 10 consecutive failures
    - More than 50 failures in last 24 hours
    
    Sends email to admin using NotificationManager.
    Call this function from a background worker or scheduler.
    """
    import os
    from src.notifications.notification_manager import NotificationManager
    
    db = get_db_manager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    alerts_to_send = []
    
    try:
        # Check 1: Consecutive failures
        cursor.execute("""
            SELECT 
                tracking_number,
                carrier,
                pod_fetch_error,
                created_at
            FROM claims
            WHERE pod_fetch_status = 'failed'
            ORDER BY id DESC
            LIMIT 15
        """)
        
        recent_failures = cursor.fetchall()
        
        if len(recent_failures) >= 10:
            # All of last 10-15 are failures - critical
            alerts_to_send.append({
                'type': 'consecutive_failures',
                'count': len(recent_failures),
                'samples': recent_failures[:5]
            })
        
        # Check 2: High failure rate in last 24h
        cutoff = datetime.now() - timedelta(hours=24)
        cursor.execute(f"""
            SELECT COUNT(*) as count
            FROM claims
            WHERE pod_fetch_status = 'failed'
            AND created_at >= '{cutoff.isoformat()}'
        """)
        
        failures_24h = cursor.fetchone()[0]
        
        if failures_24h >= 50:
            cursor.execute(f"""
                SELECT 
                    pod_fetch_error,
                    COUNT(*) as count
                FROM claims
                WHERE pod_fetch_status = 'failed'
                AND created_at >= '{cutoff.isoformat()}'
                GROUP BY pod_fetch_error
                ORDER BY count DESC
                LIMIT 5
            """)
            
            error_breakdown = cursor.fetchall()
            
            alerts_to_send.append({
                'type': 'high_failure_rate',
                'count': failures_24h,
                'errors': error_breakdown
            })
        
    except Exception as e:
        print(f"Error checking POD alerts: {e}")
    finally:
        conn.close()
    
    # Send alerts if any
    if alerts_to_send:
        notif_mgr = NotificationManager()
        
        for alert in alerts_to_send:
            if alert['type'] == 'consecutive_failures':
                subject = f"🚨 POD ALERT: {alert['count']} Consecutive Failures"
                body = f"""
                <h2 style="color: #dc3545;">Critical POD Failure Alert</h2>
                
                <p><strong>{alert['count']} consecutive POD fetch failures</strong> detected.</p>
                
                <h3>Recent Failures:</h3>
                <table style="border-collapse: collapse; width: 100%;">
                    <thead>
                        <tr style="background: #f8f9fa;">
                            <th style="padding: 8px; border: 1px solid #dee2e6;">Tracking</th>
                            <th style="padding: 8px; border: 1px solid #dee2e6;">Carrier</th>
                            <th style="padding: 8px; border: 1px solid #dee2e6;">Error</th>
                            <th style="padding: 8px; border: 1px solid #dee2e6;">Date</th>
                        </tr>
                    </thead>
                    <tbody>
                """
                
                for sample in alert['samples']:
                    body += f"""
                        <tr>
                            <td style="padding: 8px; border: 1px solid #dee2e6;">{sample[0]}</td>
                            <td style="padding: 8px; border: 1px solid #dee2e6;">{sample[1]}</td>
                            <td style="padding: 8px; border: 1px solid #dee2e6;">{sample[2]}</td>
                            <td style="padding: 8px; border: 1px solid #dee2e6;">{sample[3]}</td>
                        </tr>
                    """
                
                body += """
                    </tbody>
                </table>
                
                <p><strong>Action Required:</strong></p>
                <ul>
                    <li>Check API credentials and rate limits</li>
                    <li>Verify network connectivity</li>
                    <li>Review carrier API status pages</li>
                    <li>Check POD Analytics dashboard for details</li>
                </ul>
                """
                
            else:  # high_failure_rate
                subject = f"⚠️ POD ALERT: {alert['count']} Failures in 24h"
                body = f"""
                <h2 style="color: #fd7e14;">High POD Failure Rate Alert</h2>
                
                <p><strong>{alert['count']} POD fetch failures</strong> in the last 24 hours.</p>
                
                <h3>Error Breakdown:</h3>
                <table style="border-collapse: collapse; width: 100%;">
                    <thead>
                        <tr style="background: #f8f9fa;">
                            <th style="padding: 8px; border: 1px solid #dee2e6;">Error</th>
                            <th style="padding: 8px; border: 1px solid #dee2e6;">Count</th>
                        </tr>
                    </thead>
                    <tbody>
                """
                
                for error in alert['errors']:
                    body += f"""
                        <tr>
                            <td style="padding: 8px; border: 1px solid #dee2e6;">{error[0]}</td>
                            <td style="padding: 8px; border: 1px solid #dee2e6;">{error[1]}</td>
                        </tr>
                    """
                
                body += """
                    </tbody>
                </table>
                
                <p><strong>Recommended Actions:</strong></p>
                <ul>
                    <li>Review error patterns in POD Analytics</li>
                    <li>Check if specific carriers are affected</li>
                    <li>Verify API quotas and billing status</li>
                    <li>Consider implementing retry delays</li>
                </ul>
                """
            
            # Send email to admin
            try:
                notif_mgr.send_html_email(
                    to_email=os.getenv('ADMIN_EMAIL', 'admin@example.com'),
                    subject=subject,
                    html_body=body
                )
                print(f"✅ Sent POD alert: {subject}")
            except Exception as e:
                print(f"❌ Failed to send POD alert: {e}")
