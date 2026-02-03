import pytest
import requests
from unittest.mock import MagicMock, patch
from src.integrations.shopify_connector import ShopifyConnector
from src.integrations.prestashop_connector import PrestaShopConnector
from datetime import datetime

class TestEcommerceConnectors:
    
    @pytest.fixture
    def shopify_creds(self):
        return {
            'shop_domain': 'test-shop.myshopify.com',
            'access_token': 'shpat_test_token'
        }
    
    @pytest.fixture
    def prestashop_creds(self):
        return {
            'store_url': 'https://prestashop.example.com',
            'api_key': 'PRESTASHOP_TEST_KEY'
        }

    @patch('requests.Session.get')
    def test_shopify_fetch_orders(self, mock_get, shopify_creds):
        # ... (rest of Shopify test unchanged)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'orders': [
                {
                    'id': 123456,
                    'created_at': '2026-01-20T10:00:00Z',
                    'email': 'customer@test.com',
                    'total_price': '150.00',
                    'fulfillment_status': 'fulfilled',
                    'shipping_lines': [{'title': 'Colissimo', 'price': '8.50'}],
                    'shipping_address': {'city': 'Paris', 'country': 'France'},
                    'fulfillments': [
                        {
                            'tracking_number': '6A123456789',
                            'tracking_company': 'Colissimo',
                            'updated_at': '2026-01-21T15:00:00Z'
                        }
                    ]
                }
            ]
        }
        mock_get.return_value = mock_response
        
        connector = ShopifyConnector(shopify_creds)
        orders = connector.fetch_orders()
        
        assert len(orders) == 1
        assert orders[0]['order_id'] == '123456'
        assert orders[0]['customer_email'] == 'customer@test.com'
        assert orders[0]['shipping_carrier'] == 'Colissimo'
        assert orders[0]['tracking_number'] == '6A123456789'
        assert orders[0]['total_amount'] == 150.0
        assert orders[0]['delivery_status'] == 'delivered'

    @patch('requests.Session.get')
    def test_prestashop_fetch_orders(self, mock_get, prestashop_creds):
        # ... (rest of setup unchanged)
        mock_list_response = MagicMock()
        mock_list_response.status_code = 200
        mock_list_response.json.return_value = {
            'orders': [{'id': '789'}]
        }
        
        mock_detail_response = MagicMock()
        mock_detail_response.status_code = 200
        mock_detail_response.json.return_value = {
            'order': {
                'id': '789',
                'date_add': '2026-01-20 10:00:00',
                'total_paid': '99.90',
                'current_state': '5',  # Delivered
                'id_carrier': '12',
                'total_shipping': '7.50'
            }
        }
        
        mock_get.side_effect = [mock_list_response, mock_detail_response]
        
        connector = PrestaShopConnector(prestashop_creds)
        orders = connector.fetch_orders()
        
        assert len(orders) == 1
        assert orders[0]['order_id'] == '789'
        assert orders[0]['total_amount'] == 99.90
        assert orders[0]['delivery_status'] == 'delivered'
