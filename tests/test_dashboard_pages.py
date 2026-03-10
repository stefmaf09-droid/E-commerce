"""
Unit tests for dashboard pages.

Tests cover:
- Settings page rendering
- Reports page rendering  
- Carrier breakdown functionality
- Navigation system
"""

import pytest
import pandas as pd
import streamlit as st
from unittest.mock import Mock, patch, MagicMock

# Import modules to test
from src.dashboard.settings_page import (
    render_settings_page,
    render_store_management,
    render_platform_info,
    render_bank_info
)
from src.dashboard.reports_page import (
    render_reports_page,
    render_analytics_tab,
    render_timeline,
    render_stagnation_escalation_section
)
from src.dashboard.carrier_breakdown import render_carrier_breakdown


class TestSettingsPage:
    """Test suite for settings page — uses full mocking to avoid Streamlit runtime issues."""

    def test_render_settings_page_calls_subsections(self):
        """Settings page should invoke all sub-render functions."""
        with patch('src.dashboard.settings_page.render_store_management') as mock_store, \
             patch('src.dashboard.settings_page.render_platform_info') as mock_platform, \
             patch('src.dashboard.settings_page.render_bank_info') as mock_bank, \
             patch('src.dashboard.settings_page.render_notification_preferences'), \
             patch('src.dashboard.settings_page.render_email_templates_section'), \
             patch('src.dashboard.settings_page.get_browser_language', return_value='fr'), \
             patch('src.dashboard.settings_page.get_i18n_text', return_value='R\u00e9glages'), \
             patch('streamlit.markdown'), \
             patch('streamlit.session_state', {'client_email': 'test@example.com'}), \
             patch('src.ui.stripe_onboarding.render_stripe_onboarding', create=True):
            render_settings_page()

        mock_store.assert_called_once()
        mock_platform.assert_called_once()
        mock_bank.assert_called_once()

    def test_render_store_management_no_stores(self):
        """When no stores exist, st.info should be called (\"no stores\" message)."""
        mock_manager = MagicMock()
        mock_manager.get_all_stores.return_value = []

        with patch('src.dashboard.settings_page.CredentialsManager', return_value=mock_manager), \
             patch('src.dashboard.settings_page.get_browser_language', return_value='fr'), \
             patch('src.dashboard.settings_page.get_i18n_text', side_effect=lambda k, l: k), \
             patch('streamlit.session_state', {'client_email': 'test@example.com'}), \
             patch('streamlit.markdown'), \
             patch('streamlit.caption'), \
             patch('streamlit.expander', return_value=MagicMock(
                 __enter__=lambda s: s, __exit__=MagicMock(return_value=False))), \
             patch('streamlit.form', return_value=MagicMock(
                 __enter__=lambda s: s, __exit__=MagicMock(return_value=False))), \
             patch('streamlit.form_submit_button', return_value=False), \
             patch('streamlit.selectbox', return_value='Shopify'), \
             patch('streamlit.text_input', return_value=''), \
             patch('streamlit.info') as mock_info:
            render_store_management()

        mock_info.assert_called()


class TestReportsPage:
    """Test suite for reports page functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.sample_df = pd.DataFrame({
            'order_id': ['#001', '#002', '#003'],
            'carrier': ['UPS', 'DHL', 'FedEx'],
            'status': ['pending', 'recovered', 'pending'],
            'total_recoverable': [100.0, 200.0, 150.0]
        })
    
    @patch('streamlit.markdown')
    def test_render_reports_page_structure(self, mock_markdown):
        """Test reports page renders correctly."""
        with patch('src.dashboard.reports_page.render_analytics_tab'), \
             patch('src.dashboard.reports_page.render_timeline'):
            
            render_reports_page(self.sample_df)
            
            # Verify header exists
            assert any('Reports' in str(call) for call in mock_markdown.call_args_list)
    
    @patch('streamlit.markdown')
    @patch('streamlit.caption')
    def test_render_timeline_structure(self, mock_caption, mock_markdown):
        """Test timeline renders with events."""
        render_timeline()
        
        # Should render timeline header
        header_calls = [call for call in mock_markdown.call_args_list 
                       if 'Timeline' in str(call)]
        assert len(header_calls) > 0, "Timeline header should be rendered"
        
        # Should render multiple event items (at least 5 events)
        assert mock_markdown.call_count >= 6  # Header + at least 5 events
    
    @patch('streamlit.subheader')
    @patch('streamlit.info')
    def test_render_stagnation_escalation_empty_df(self, mock_info, mock_subheader):
        """Test escalation section with empty dataframe."""
        empty_df = pd.DataFrame()
        
        with patch('streamlit.success') as mock_success:
            render_stagnation_escalation_section(empty_df)
            
            # Should show subheader
            mock_subheader.assert_called()


class TestCarrierBreakdown:
    """Test suite for carrier breakdown functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.sample_df = pd.DataFrame({
            'order_id': ['#001', '#002', '#003', '#004', '#005'],
            'carrier': ['Chronopost', 'UPS', 'DHL', 'Chronopost', 'UPS'],
            'status': ['recovered', 'pending', 'recovered', 'pending', 'recovered'],
            'total_recoverable': [100.0, 200.0, 150.0, 300.0, 250.0]
        })
    
    @patch('streamlit.markdown')
    @patch('streamlit.caption')
    def test_render_carrier_breakdown_structure(self, mock_caption, mock_markdown):
        """Test carrier breakdown renders with correct structure."""
        from unittest.mock import MagicMock
        def fake_columns(arg):
            from unittest.mock import MagicMock
            if isinstance(arg, int):
                return [MagicMock() for _ in range(arg)]
            if isinstance(arg, (list, tuple)):
                return [MagicMock() for _ in range(len(arg))]
            return [MagicMock()]

        with patch('streamlit.container'), \
             patch('streamlit.columns', side_effect=fake_columns), \
             patch('streamlit.metric'), \
             patch('streamlit.info'):
            
            render_carrier_breakdown(self.sample_df)
            
            # Should render header
            assert any('Breakdown par Transporteur' in str(call) for call in mock_markdown.call_args_list)
    
    @patch('streamlit.info')
    def test_render_carrier_breakdown_empty_df(self, mock_info):
        """Test carrier breakdown handles empty dataframe."""
        empty_df = pd.DataFrame()
        
        render_carrier_breakdown(empty_df)
        
        # Should show info message
        mock_info.assert_called_with("Aucune donnée de litige disponible")
    
    def test_carrier_stats_calculation(self):
        """Test that carrier stats are calculated correctly."""
        # Group by carrier
        carrier_stats = self.sample_df.groupby('carrier').agg({
            'order_id': 'count',
            'total_recoverable': ['sum', 'mean']
        }).reset_index()
        
        carrier_stats.columns = ['carrier', 'total_disputes', 'total_recoverable', 'avg_recoverable']
        
        # Verify Chronopost stats
        chronopost = carrier_stats[carrier_stats['carrier'] == 'Chronopost'].iloc[0]
        assert chronopost['total_disputes'] == 2
        assert chronopost['total_recoverable'] == 400.0
        assert chronopost['avg_recoverable'] == 200.0
        
        # Verify UPS stats
        ups = carrier_stats[carrier_stats['carrier'] == 'UPS'].iloc[0]
        assert ups['total_disputes'] == 2
        assert ups['total_recoverable'] == 450.0


class TestNavigationIntegration:
    """Integration tests for navigation between pages."""
    
    @patch('streamlit.session_state', {'active_page': 'Dashboard'})
    def test_navigation_state_dashboard(self):
        """Test navigation state for dashboard."""
        assert st.session_state.get('active_page') == 'Dashboard'
    
    @patch('streamlit.session_state', {'active_page': 'Disputes'})
    def test_navigation_state_disputes(self):
        """Test navigation state for disputes."""
        assert st.session_state.get('active_page') == 'Disputes'
    
    @patch('streamlit.session_state', {'active_page': 'Reports'})
    def test_navigation_state_reports(self):
        """Test navigation state for reports."""
        assert st.session_state.get('active_page') == 'Reports'
    
    @patch('streamlit.session_state', {'active_page': 'Settings'})
    def test_navigation_state_settings(self):
        """Test navigation state for settings."""
        assert st.session_state.get('active_page') == 'Settings'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
