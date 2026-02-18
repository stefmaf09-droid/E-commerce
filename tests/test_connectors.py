import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from src.integrations.woocommerce_connector import WooCommerceConnector
from src.integrations.prestashop_connector import PrestaShopConnector

class TestConnectors:
    
    # === WOOCOMMERCE TESTS ===
    
    def test_woocommerce_init(self):
        # Missing keys
        with pytest.raises(ValueError):
            WooCommerceConnector({'store_url': 'http://test.com'})
            
        # Success
        connector = WooCommerceConnector({
            'store_url': 'http://test.com',
            'consumer_key': 'ck_123',
            'consumer_secret': 'cs_456'
        })
        assert connector.base_url == 'http://test.com/wp-json/wc/v3'

    @patch('src.integrations.woocommerce_connector.requests.get')
    def test_woocommerce_fetch_orders(self, mock_get):
        connector = WooCommerceConnector({
            'store_url': 'http://test.com',
            'consumer_key': 'ck_123',
            'consumer_secret': 'cs_456'
        })
        
        # Mock API Response
        mock_response = MagicMock()
        mock_response.json.return_value = [{
            'id': 1001,
            'date_created': '2023-10-25T10:00:00',
            'total': '50.00',
            'status': 'completed',
            'shipping_lines': [{'method_title': 'Colissimo', 'total': '5.00'}],
            'meta_data': [{'key': '_tracking_number', 'value': '8R1234567890'}],
            'billing': {'email': 'client@test.com'},
            'shipping': {'address_1': '1 Rue de la Paix', 'city': 'Paris', 'country': 'FR'}
        }]
        mock_response.headers = {'X-WP-TotalPages': '1'}
        mock_get.return_value = mock_response
        
        orders = connector.fetch_orders()
        
        assert len(orders) == 1
        order = orders[0]
        assert order['order_id'] == '1001'
        assert order['total_amount'] == 50.0
        assert order['shipping_carrier'] == 'Colissimo'
        assert order['tracking_number'] == '8R1234567890'
        assert order['delivery_status'] == 'delivered'

    # === PRESTASHOP TESTS ===

    def test_prestashop_init(self):
        # Missing keys
        with pytest.raises(ValueError):
            PrestaShopConnector({'store_url': 'http://prestashop.com'})
            
        # Success
        connector = PrestaShopConnector({
            'store_url': 'http://prestashop.com',
            'api_key': 'key_123'
        })
        assert connector.base_url == 'http://prestashop.com/api'

    @patch('src.integrations.prestashop_connector.requests.Session.get')
    def test_prestashop_fetch_orders(self, mock_get):
        connector = PrestaShopConnector({
            'store_url': 'http://prestashop.com',
            'api_key': 'key_123'
        })
        
        # 1. Mock List Response
        mock_list_resp = MagicMock()
        mock_list_resp.json.return_value = {'orders': [{'id': 500}]}
        
        # 2. Mock Detail Response
        mock_detail_resp = MagicMock()
        mock_detail_resp.json.return_value = {'order': {
            'id': 500,
            'date_add': '2023-10-26 14:00:00',
            'total_paid': '120.50',
            'current_state': '5', # Delivered
            'id_carrier': '12',
            'total_shipping': '10.00',
            'shipping_number': 'PRESTA123456'
        }}
        
        mock_get.side_effect = [mock_list_resp, mock_detail_resp]
        
        orders = connector.fetch_orders()
        
        assert len(orders) == 1
        order = orders[0]
        assert order['order_id'] == '500'
        assert order['total_amount'] == 120.5
        assert order['delivery_status'] == 'delivered'
        assert order['tracking_number'] == 'PRESTA123456'
