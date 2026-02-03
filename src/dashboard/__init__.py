"""
Dashboard module - UI and authentication functions for Streamlit dashboards.

This module provides reusable UI components and authentication functions
for client dashboards.
"""

from .ui_functions import (
    render_navigation_header,
    render_disputes_table_modern,
    render_analytics_tab,
)
from .carrier_breakdown import render_carrier_breakdown

from .auth_functions import authenticate

from .dispute_details_page import render_dispute_details_page

from .carrier_overview_page import render_carrier_overview_page

from .settings_page import render_settings_page, render_platform_info, render_bank_info
from .reports_page import render_reports_page, render_stagnation_escalation_section

__all__ = [
    'render_navigation_header',
    'render_disputes_table_modern',
    'render_analytics_tab',
    'render_carrier_breakdown',
    'authenticate',
    'render_dispute_details_page',
    'render_carrier_overview_page',
    'render_settings_page',
    'render_platform_info',
    'render_bank_info',
    'render_reports_page',
    'render_stagnation_escalation_section',
]
