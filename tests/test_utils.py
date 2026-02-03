import pytest
import os
import json
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from src.utils.custom_carriers import CustomCarrierManager
from src.utils.email_service import EmailService

class TestCustomCarrierManager:
    @pytest.fixture
    def manager(self, tmp_path):
        data_file = tmp_path / "custom_carriers.json"
        return CustomCarrierManager(data_file=str(data_file))

    def test_add_get_carriers(self, manager):
        email = "test@example.com"
        assert manager.add_carrier(email, "LocalExpress", {"phone": "123"}) is True
        assert manager.add_carrier(email, "LocalExpress") is False  # Duplicate
        
        carriers = manager.get_carriers(email)
        assert len(carriers) == 1
        assert carriers[0]['name'] == 'LocalExpress'
        
        all_carriers = manager.get_all_carriers(email)
        assert "LocalExpress" in all_carriers
        assert "Colissimo" in all_carriers

    def test_delete_carrier(self, manager):
        email = "test@example.com"
        manager.add_carrier(email, "ToDel")
        assert manager.delete_carrier(email, "ToDel") is True
        assert len(manager.get_carriers(email)) == 0
        assert manager.delete_carrier("none@test.com", "X") is False

    def test_add_carrier_exception(self, manager):
        # Trigger exception by mocking open to fail
        with patch("builtins.open", side_effect=IOError("Permission denied")):
            assert manager.add_carrier("a@b.com", "Name") is False

    def test_delete_carrier_exception(self, manager):
        with patch("builtins.open", side_effect=IOError("Permission denied")):
            assert manager.delete_carrier("a@b.com", "Name") is False

class TestEmailService:
    @pytest.fixture
    def service(self, tmp_path):
        tokens_file = tmp_path / "tokens.json"
        # Set env vars to avoid int('') error
        with patch.dict(os.environ, {
            'SMTP_PORT': '587',
            'SMTP_USER': 'test@gmail.com',
            'SMTP_PASSWORD': 'password'
        }):
            # Set tokens_file before init via mock or just let it use default then change it
            with patch('src.utils.email_service.Path.mkdir'): # avoid creating 'data/' dir
                service = EmailService()
                service.tokens_file = str(tokens_file)
                # Now manually trigger the init logic for the specific file
                if not os.path.exists(service.tokens_file):
                    with open(service.tokens_file, 'w') as f:
                        json.dump({}, f)
            return service

    def test_token_lifecycle(self, service):
        email = "user@test.com"
        token = service.generate_reset_token(email)
        assert token is not None
        
        # Validate
        assert service.validate_reset_token(token) == email
        
        # Invalidate
        service.invalidate_token(token)
        assert service.validate_reset_token(token) is None

    def test_token_expiration(self, service):
        email = "user@test.com"
        token = service.generate_reset_token(email)
        
        # Manually expire token in JSON
        with open(service.tokens_file, 'r') as f:
            tokens = json.load(f)
        
        tokens[token]['expires_at'] = (datetime.now() - timedelta(hours=1)).isoformat()
        
        with open(service.tokens_file, 'w') as f:
            json.dump(tokens, f)
            
        assert service.validate_reset_token(token) is None
        
        # Check that expired token was removed from file
        with open(service.tokens_file, 'r') as f:
            tokens = json.load(f)
        assert token not in tokens

    def test_validate_token_not_found(self, service):
        assert service.validate_reset_token("unknown") is None

    def test_validate_token_exception(self, service):
        with patch("builtins.open", side_effect=IOError):
            assert service.validate_reset_token("any") is None

    def test_invalidate_token_not_found(self, service):
        service.invalidate_token("unknown") # Should not crash

    def test_invalidate_token_exception(self, service):
        with patch("builtins.open", side_effect=IOError):
            service.invalidate_token("any") # Should not crash

    @patch('smtplib.SMTP')
    def test_send_email_no_creds(self, mock_smtp, service):
        service.smtp_user = ""
        assert service.send_password_reset_email("to@test.com", "http://reset") is True
        assert not mock_smtp.called

    @patch('smtplib.SMTP')
    def test_send_email_with_creds(self, mock_smtp, service):
        service.smtp_user = "user"
        service.smtp_password = "password"
        assert service.send_password_reset_email("to@test.com", "http://reset") is True
        assert mock_smtp.called

    @patch('smtplib.SMTP')
    def test_send_email_exception(self, mock_smtp, service):
        service.smtp_user = "user"
        service.smtp_password = "password"
        mock_smtp.side_effect = Exception("SMTP Error")
        assert service.send_password_reset_email("to@test.com", "http://reset") is False
