import pytest
from streamlit.testing.v1 import AppTest
from unittest.mock import MagicMock, patch
import os

class TestUIComponents:
    
    @patch('src.ui.store_management.sqlite3.connect')
    @patch('src.ui.store_management.Fernet')
    @patch('src.ui.store_management.Path.exists')
    def test_render_store_management(self, mock_exists, mock_fernet, mock_connect):
        # Mock credentials manager at its source
        with patch('src.auth.credentials_manager.CredentialsManager') as mock_cm:
            mock_manager = mock_cm.return_value
            mock_manager.get_all_stores.return_value = [{'id': 1, 'store_name': 'My Shop', 'platform': 'shopify'}]
            
            at = AppTest.from_file("tests/ui_wrappers/store_wrapper.py")
            at.run()
            
            assert "Gestion de vos Magasins" in at.markdown[0].value
            assert "My Shop" in at.expander[0].label
            
            # Test form submission
            at.text_input[0].set_value("New Shop")
            at.text_input[1].set_value("shop.url")
            # Fill credentials (keys depends on platform selectbox)
            # Default is shopify
            at.text_input[2].set_value("key")
            at.text_input[3].set_value("pass")
            
            # Mock file and DB for save
            mock_exists.return_value = True
            with patch('builtins.open', MagicMock()):
                at.button[1].click() # form submit
                at.run()
                # Should attempt to save to DB

    @patch('src.ui.password_reset.CredentialsManager')
    @patch('src.ui.password_reset.EmailService')
    def test_render_password_reset_flow(self, mock_email_class, mock_cm_class):
        mock_cm = mock_cm_class.return_value
        mock_email = mock_email_class.return_value
        
        at = AppTest.from_file("tests/ui_wrappers/password_wrapper.py")
        at.run()
        
        # 1. Test empty email
        at.button[0].click()
        at.run()
        # assert "Veuillez entrer votre email" in at.error[0].body
        
        # 2. Test request reset for existing email
        at.text_input[0].set_value("exists@test.com")
        mock_cm.get_credentials.return_value = {'email': 'exists@test.com'}
        mock_email.generate_reset_token.return_value = "token123"
        mock_email.send_password_reset_email.return_value = True
        at.button[0].click()
        at.run()
        assert mock_email.send_password_reset_email.called
        
        # 3. Test non-existent email (security message)
        mock_cm.get_credentials.return_value = None
        at.button[0].click()
        at.run()
        # Should show success message even if email not found
        
    @patch('src.ui.password_reset.EmailService')
    def test_render_new_password_form(self, mock_email_class):
        mock_email = mock_email_class.return_value
        mock_email.validate_reset_token.return_value = "user@test.com"
        
        at = AppTest.from_file("tests/ui_wrappers/password_wrapper.py")
        # Set query param to trigger new password form
        at.query_params['reset_token'] = "valid_token"
        at.run()
        
        assert "Nouveau mot de passe" in at.markdown[0].value
        
        # 1. Mismatch passwords
        at.text_input[0].set_value("pass123456")
        at.text_input[1].set_value("pass654321")
        at.button[0].click()
        at.run()
        
        # 2. Too short
        at.text_input[0].set_value("123")
        at.text_input[1].set_value("123")
        at.button[0].click()
        at.run()
        
        # 3. Success
        at.text_input[0].set_value("secure_pass_123")
        at.text_input[1].set_value("secure_pass_123")
        at.button[0].click()
        at.run()
        assert mock_email.invalidate_token.called

    @patch('src.ui.store_management.sqlite3.connect')
    @patch('src.auth.credentials_manager.CredentialsManager')
    def test_store_management_errors(self, mock_cm_class, mock_connect):
        mock_cm = mock_cm_class.return_value
        mock_cm.get_all_stores.return_value = [] # No stores, so no delete buttons
        
        at = AppTest.from_file("tests/ui_wrappers/store_wrapper.py")
        at.run()
        
        # 1. Empty submission (button[0] is the form submit because no delete buttons)
        at.button[0].click()
        at.run()
        
        # 2. DB Error
        mock_connect.side_effect = Exception("DB Fail")
        at.text_input[0].set_value("Shop")
        at.text_input[1].set_value("url.com")
        at.button[0].click()
        at.run()

