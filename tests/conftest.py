"""
Pytest Configuration and Fixtures.

Provides common fixtures for all tests including:
- Mock database
- Mock SMTP server
- Test clients
- Sample data
"""

import pytest
import sqlite3
import os
import tempfile
from datetime import datetime, timedelta
from typing import Dict, List
import json


@pytest.fixture
def temp_db():
    """Create a temporary SQLite database for testing."""
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    
    # Initialize database with schema
    schema_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'schema.sql')
    if os.path.exists(schema_path):
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = f.read()
        
        conn = sqlite3.connect(db_path)
        conn.executescript(schema)
        conn.commit()
        conn.close()
    
    yield db_path
    
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def db_manager(temp_db):
    """Provide a DatabaseManager instance with temporary database."""
    from src.database import DatabaseManager
    return DatabaseManager(db_path=temp_db)


@pytest.fixture
def sample_client(db_manager):
    """Create a sample client in database."""
    client_id = db_manager.create_client(
        email='test@example.com',
        full_name='Test User',
        company_name='Test Company',
        phone='+33612345678'
    )
    return db_manager.get_client(client_id=client_id)


@pytest.fixture
def sample_claim(db_manager, sample_client):
    """Create a sample claim in database."""
    claim_id = db_manager.create_claim(
        claim_reference='CLM-TEST-001',
        client_id=sample_client['id'],
        order_id='ORD-123',
        carrier='colissimo',
        dispute_type='late_delivery',
        amount_requested=150.00,
        tracking_number='FR123456789',
        order_date='2026-01-15',
        customer_name='Jean Dupont'
    )
    return db_manager.get_claim(claim_id=claim_id)


@pytest.fixture
def sample_disputes(db_manager, sample_client):
    """Create sample disputes in database."""
    disputes = []
    
    carriers = ['colissimo', 'chronopost', 'dhl', 'ups']
    dispute_types = ['late_delivery', 'lost', 'damaged', 'invalid_pod']
    
    for i in range(5):
        dispute_id = db_manager.create_dispute(
            client_id=sample_client['id'],
            order_id=f'ORD-{1000+i}',
            carrier=carriers[i % len(carriers)],
            dispute_type=dispute_types[i % len(dispute_types)],
            amount_recoverable=100.0 + (i * 50),
            order_date=(datetime.now() - timedelta(days=30-i)).date().isoformat(),
            tracking_number=f'FR{123456789+i}'
        )
        disputes.append(db_manager.get_client_disputes(sample_client['id'])[0])
    
    return disputes


@pytest.fixture
def sample_orders():
    """Provide sample order data for testing."""
    return [
        {
            'order_id': 'ORD-1001',
            'order_date': '2026-01-10',
            'order_value': 150.00,
            'product_value': 150.00,
            'shipping_cost': 12.50,
            'carrier': 'Colissimo',
            'tracking_number': 'FR123456789',
            'status': 'Delivered_Late',  # Pour trigger dispute
            'delivery_date': '2026-01-20',
            'expected_delivery_date': '2026-01-15',
            'delay_days': 5,  # Retard de 5 jours
            'service': 'Standard',
            'recipient': {
                'name': 'Jean Dupont',
                'address': '123 Rue de Paris, 75001 Paris'
            },
            'has_pod': True,
            'pod_valid': True,
            'pod_gps_match': True
        },
        {
            'order_id': 'ORD-1002',
            'order_date': '2026-01-12',
            'order_value': 200.00,
            'product_value': 200.00,
            'shipping_cost': 15.00,
            'carrier': 'Chronopost',
            'tracking_number': 'CH987654321',
            'status': 'Lost',  # Colis perdu - dispute critique
            'delivery_date': None,
            'expected_delivery_date': '2026-01-14',
            'delay_days': 0,
            'service': 'Express',
            'recipient': {
                'name': 'Marie Martin',
                'address': '456 Avenue des Champs, 69000 Lyon'
            },
            'has_pod': False,
            'pod_valid': False,
            'pod_gps_match': False
        }
    ]


@pytest.fixture
def mock_smtp_server(monkeypatch):
    """Mock SMTP server for email testing."""
    sent_emails = []
    
    class MockSMTP:
        def __init__(self, host, port):
            self.host = host
            self.port = port
        
        def starttls(self):
            pass
        
        def login(self, user, password):
            pass
        
        def send_message(self, msg):
            sent_emails.append({
                'to': msg['To'],
                'subject': msg['Subject'],
                'from': msg['From'],
                'body': msg.get_payload()
            })
        
        def __enter__(self):
            return self
        
        def __exit__(self, *args):
            pass
    
    monkeypatch.setattr('smtplib.SMTP', MockSMTP)
    
    return sent_emails


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set mock environment variables for testing."""
    env_vars = {
        'GMAIL_SENDER': 'test@example.com',
        'GMAIL_APP_PASSWORD': 'test_password',
        'DATABASE_URL': 'sqlite:///test.db',
        'REDIS_URL': 'redis://localhost:6379/0',
        'OPENAI_API_KEY': 'sk-test-key',
        'STRIPE_SECRET_KEY': 'sk_test_123',
        'STRIPE_PUBLISHABLE_KEY': 'pk_test_123',
        'SENTRY_DSN': 'https://test@sentry.io/123'
    }
    
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    
    return env_vars


@pytest.fixture
def sample_dispute_data():
    """Sample dispute data for orchestrator testing."""
    return {
        'order_id': 'ORD-TEST-001',
        'tracking_number': 'FR123456789',
        'carrier': 'colissimo',
        'dispute_type': 'late_delivery',
        'order_date': '2026-01-10',
        'delivery_date': '2026-01-20',
        'expected_delivery_date': '2026-01-15',
        'order_value': 150.00,
        'shipping_cost': 12.50,
        'total_recoverable': 162.50,
        'client_email': 'test@example.com',
        'recipient': {
            'name': 'Jean Dupont',
            'address': '123 Rue de Paris, 75001 Paris'
        }
    }


@pytest.fixture
def sample_credentials():
    """Sample e-commerce platform credentials."""
    return {
        'shopify': {
            'platform': 'shopify',
            'shop_domain': 'test-shop.myshopify.com',
            'access_token': 'shpat_test_token',
            'api_key': 'test_api_key',
            'api_secret': 'test_api_secret'
        },
        'woocommerce': {
            'platform': 'woocommerce',
            'store_url': 'https://test-store.com',
            'consumer_key': 'ck_test_key',
            'consumer_secret': 'cs_test_secret'
        }
    }


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances between tests."""
    # Reset database manager singleton
    import src.database.database_manager as db_module
    db_module._db_manager = None
    
    yield
    
    # Cleanup after test
    db_module._db_manager = None


# Test markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_api: mark test as requiring external API"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end test"
    )
