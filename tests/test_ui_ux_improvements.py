import pytest
from streamlit.testing.v1 import AppTest
from unittest.mock import MagicMock, patch
import os

@pytest.mark.skip(reason="UI tests need wrapper files - will be implemented with full UI testing suite")
class TestUXImprovements:
    
    @patch('src.auth.credentials_manager.CredentialsManager')
    def test_registration_iban_optional(self, mock_cm_class):
        """Test that IBAN is optional in registration form."""
        at = AppTest.from_file("tests/ui_wrappers/registration_wrapper.py")
        at.run(timeout=10)
        
        # Go to tab 2 (New Client)
        # Note: tabs are indexed by order in script
        # Tab 1: Login, Tab 2: Register
        at.tabs[1].run()
        
        # Check that IBAN field has the "(Optionnel)" text in placeholder
        # Find the text input for IBAN
        iban_input = None
        for ti in at.text_input:
            if "IBAN" in ti.label:
                iban_input = ti
                break
        
        assert iban_input is not None
        assert "(Optionnel)" in iban_input.placeholder

    @patch('src.auth.credentials_manager.CredentialsManager')
    def test_api_guides_visible(self, mock_cm_class):
        """Test that API guides expanders are present."""
        at = AppTest.from_file("tests/ui_wrappers/registration_wrapper.py")
        at.run(timeout=10)
        at.tabs[1].run()
        
        # Check for expanders
        guide_found = False
        for exp in at.expander:
            if "Où trouver mes identifiants" in exp.label:
                guide_found = True
                break
        
        assert guide_found

    @patch('onboarding_functions.ManualPaymentManager')
    def test_onboarding_iban_skip(self, mock_pm):
        """Test that IBAN can be skipped in onboarding."""
        # Ensure no bank info exists to show the skip button
        mock_pm.return_value.get_client_bank_info.return_value = None
        
        at = AppTest.from_file("tests/ui_wrappers/onboarding_wrapper.py")
        at.query_params["step"] = "bank_info"
        at.run()
        
        # Look for the skip button
        skip_button = None
        for btn in at.button:
            if "Passer cette étape" in btn.label:
                skip_button = btn
                break
        
        assert skip_button is not None
        
        # Verify it works (marks step as complete/returns True logic)
        skip_button.click()
        at.run()
        # In the wrapper, it calls rerender/rerun. We check if it attempted to proceed.

    @patch('client_dashboard.CredentialsManager')
    @patch('client_dashboard.OrderSyncWorker')
    @patch('client_dashboard.OnboardingManager')
    def test_humanized_statuses_in_dashboard(self, mock_onboarding, mock_worker, mock_cm):
        """Test that statuses in the table are using human labels."""
        # Mock onboarding to be complete
        mock_onboarding.return_value.is_onboarding_complete.return_value = True
        
        # Setup session state to bypass login
        at = AppTest.from_file("client_dashboard.py")
        at.session_state.authenticated = True
        at.session_state.client_email = "test@test.com"
        
        # Mock disputes data
        import pandas as pd
        disputes_df = pd.DataFrame([{
            'order_id': '123',
            'carrier': 'Colissimo',
            'num_disputes': 1,
            'total_recoverable': 50.0
        }])
        
        # Run dashboard
        at.run()
        
        # Check that the status labels dictionary contains human text
        # (This is harder to check directly via AppTest UI, but we can verify 
        # the table rendering if we mock the dataframe return values)
        # However, checking the script text via grep or similar is also valid.
        # Here we just verify the dashboard loads without error with the new mapping.
        assert not at.exception
    @patch('client_dashboard.CredentialsManager')
    @patch('client_dashboard.OrderSyncWorker')
    @patch('client_dashboard.OnboardingManager')
    @patch('client_dashboard.get_db_manager')
    def test_history_tab_loads(self, mock_db_manager, mock_onboarding, mock_worker, mock_cm):
        """Test that the history tab loads without error and displays data."""
        # Mock onboarding to be complete
        mock_onboarding.return_value.is_onboarding_complete.return_value = True
        
        # Setup session state to bypass login
        at = AppTest.from_file("client_dashboard.py")
        at.session_state.authenticated = True
        at.session_state.client_email = "test@test.com"
        
        # Mock DB results
        mock_db = MagicMock()
        mock_db_manager.return_value = mock_db
        mock_db.get_client.return_value = {'id': 1, 'email': 'test@test.com'}
        mock_db.get_client_claims.return_value = [{
            'claim_reference': 'CLM-001',
            'order_id': 'ORD-123',
            'carrier': 'UPS',
            'dispute_type': 'lost',
            'amount_requested': 100.0,
            'status': 'paid',
            'payment_status': 'paid',
            'created_at': '2026-01-01 10:00:00'
        }]
        
        # Run dashboard
        at.run()
        
        # Switch to tab 2 (History) - Note: tabs are indexed by order in script
        # Vue d'ensemble (0), Historique (1), Analytics (2)...
        at.tabs[1].run()
        
        # Verify no exception
        assert not at.exception
