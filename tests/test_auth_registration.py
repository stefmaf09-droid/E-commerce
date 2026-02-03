import tempfile
import os
from src.dashboard.auth_functions import register_client
from src.auth.credentials_manager import CredentialsManager
from src.auth.password_manager import PasswordManager


def test_register_and_login(tmp_path):
    # Setup temp database files
    cred_db = tmp_path / "credentials_test.db"
    pwd_db = tmp_path / "passwords_test.db"

    # Instantiate managers pointing to temp files
    creds_mgr = CredentialsManager(db_path=str(cred_db))
    pwd_mgr = PasswordManager(db_path=str(pwd_db))

    email = "ui_test_user@example.com"
    password = "TestPass123"

    # Ensure clean state
    assert creds_mgr.get_credentials(email) is None

    result = register_client(
        reg_email=email,
        reg_password=password,
        reg_password_confirm=password,
        store_name="Test Store",
        store_url="https://teststore.example",
        platform="Shopify",
        api_key="test-shop.myshopify.com",
        api_secret="token123",
        reg_iban="",
        reg_account_holder="",
        reg_bic="",
        accept_terms=True,
        credentials_manager=creds_mgr,
        password_setter=lambda e, p: pwd_mgr.set_client_password(e, p),
        onboarding_manager=None,
        email_sender=None
    )

    assert result['success'] is True

    # Credentials stored
    stored = creds_mgr.get_credentials(email)
    assert stored is not None
    assert 'access_token' in stored or 'consumer_key' in stored

    # Password set and verifiable
    assert pwd_mgr.verify_client_password(email, password) is True

    # Duplicate registration should fail
    dup = register_client(
        reg_email=email,
        reg_password=password,
        reg_password_confirm=password,
        store_name="Test Store",
        store_url="https://teststore.example",
        platform="Shopify",
        api_key="test-shop.myshopify.com",
        api_secret="token123",
        reg_iban="",
        reg_account_holder="",
        reg_bic="",
        accept_terms=True,
        credentials_manager=creds_mgr,
        password_setter=lambda e, p: pwd_mgr.set_client_password(e, p),
    )

    assert dup['success'] is False
    assert any("déjà utilisé" in err for err in dup['errors'])
