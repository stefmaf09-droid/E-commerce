"""
Tests specifically targeting the last 9 lines for 100% coverage on escalation_logger.py
Uses sophisticated call-counting mocks to allow __init__ to pass but fail on method calls.
"""

import pytest
import sqlite3
from unittest.mock import patch, MagicMock, call
from src.database.escalation_logger import EscalationLogger


class TestLogger100PercentCoverage:
    """Tests to achieve 100% coverage on escalation_logger.py"""
    
    def test_get_history_exception_lines_224_226(self, tmp_path):
        """Test exception handling in get_claim_escalation_history (lines 224-226)."""
        db_path = tmp_path / "test.db"
        
        # Create logger normally (without patch)
        logger = EscalationLogger(str(db_path))
        
        # NOW patch sqlite3.connect to fail
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.side_effect = RuntimeError("Database failure")
            
            # This call should catch the exception and return [] (lines 224-226)
            history = logger.get_claim_escalation_history(1)
            assert history == []
    
    def test_get_statistics_exception_lines_277_279(self, tmp_path):
        """Test exception handling in get_escalation_statistics (lines 277-279)."""
        db_path = tmp_path / "test.db"
        
        # Create logger normally
        logger = EscalationLogger(str(db_path))
        
        # Patch sqlite3.connect to fail
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.side_effect = IOError("Database connection lost")
            
            # This should catch exception and return default stats (lines 277-279)
            stats = logger.get_escalation_statistics()
            assert stats == {
                'total_escalations': 0,
                'by_level': {},
                'by_email_status': {},
                'success_rate': 0
            }
    
    def test_get_recent_escalations_exception_lines_325_327(self, tmp_path):
        """Test exception handling in get_recent_escalations (lines 325-327)."""
        db_path = tmp_path / "test.db"
        
        # Create logger normally
        logger = EscalationLogger(str(db_path))
        
        # Patch sqlite3.connect to fail
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.side_effect = PermissionError("Database access denied")
            
            # This should catch exception and return [] (lines 325-327)
            recent = logger.get_recent_escalations()
            assert recent == []
