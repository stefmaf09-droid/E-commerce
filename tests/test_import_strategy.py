"""
Tests for import strategy and circular dependency detection.

This module tests that the new dashboard module structure eliminates
circular dependencies and can be imported correctly.
"""

import pytest
import sys
import os


def test_no_circular_dependencies():
    """Test that importing dashboard modules doesn't cause circular dependencies."""
    try:
        from src.dashboard import ui_functions, auth_functions
        assert ui_functions is not None
        assert auth_functions is not None
    except ImportError as e:
        pytest.fail(f"Circular dependency detected: {e}")


def test_ui_functions_importable():
    """Test that all UI functions can be imported."""
    from src.dashboard.ui_functions import (
        render_navigation_header,
        render_disputes_table_modern,
        render_analytics_tab,
        render_history_tab,
        render_platform_info,
        render_bank_info
    )
    
    assert callable(render_navigation_header)
    assert callable(render_disputes_table_modern)
    assert callable(render_analytics_tab)
    assert callable(render_history_tab)
    assert callable(render_platform_info)
    assert callable(render_bank_info)


def test_auth_functions_importable():
    """Test that all auth functions can be imported."""
    from src.dashboard.auth_functions import authenticate
    
    assert callable(authenticate)


def test_dashboard_package_imports():
    """Test that dashboard package exposes correct functions."""
    from src.dashboard import (
        authenticate,
        render_navigation_header,
        render_disputes_table_modern,
        render_analytics_tab,
        render_platform_info,
        render_bank_info
    )
    
    # Verify all functions are callable
    assert callable(authenticate)
    assert callable(render_navigation_header)
    assert callable(render_disputes_table_modern)
    assert callable(render_analytics_tab)
    assert callable(render_platform_info)
    assert callable(render_bank_info)


def test_no_import_from_client_dashboard():
    """Test that dashboard modules don't import from client_dashboard.py."""
    import src.dashboard.ui_functions as ui_funcs
    import src.dashboard.auth_functions as auth_funcs
    
    # Get module source files
    ui_source = ui_funcs.__file__
    auth_source = auth_funcs.__file__
    
    # Read source files
    with open(ui_source, 'r', encoding='utf-8') as f:
        ui_content = f.read()
    
    with open(auth_source, 'r', encoding='utf-8') as f:
        auth_content = f.read()
    
    # Check that neither imports from client_dashboard
    assert 'from client_dashboard import' not in ui_content
    assert 'import client_dashboard' not in ui_content
    assert 'from client_dashboard import' not in auth_content
    assert 'import client_dashboard' not in auth_content
