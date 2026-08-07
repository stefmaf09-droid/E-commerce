"""
Test script for platform connectors.

This script demonstrates how to use the connectors and test their functionality.
"""

import sys
sys.path.append('src')

from integrations.shopify_connector import ShopifyConnector
from integrations.woocommerce_connector import WooCommerceConnector
from integrations.prestashop_connector import PrestaShopConnector
from auth.credentials_manager import CredentialsManager
from datetime import datetime, timedelta


def test_shopify():
    """Test Shopify connector (requires valid credentials)."""
    print("\n=== Testing Shopify Connector ===")
    
    # Example credentials (replace with real ones for testing)
    credentials = {
        'shop_domain': 'your-shop.myshopify.com',
        'access_token': 'YOUR_ACCESS_TOKEN_HERE'
    }
    
    try:
        connector = ShopifyConnector(credentials)
        
        # Test authentication
        if connector.authenticate():
            print("✅ Authentication successful")
            
            # Fetch recent orders
            since = datetime.now() - timedelta(days=90)
            orders = connector.fetch_orders(since=since)
            
            print(f"✅ Fetched {len(orders)} orders")
            
            if orders:
                # Display first order
                first_order = orders[0]
                print(f"\nFirst order details:")
                print(f"  - ID: {first_order['order_id']}")
print(f"  - Date: {first_order['order_date']}")
                print(f"  - Amount: {first_order['total_amount']}€")
                print(f"  - Carrier: {first_order['shipping_carrier']}")
        else:
            print("❌ Authentication failed")
    
    except Exception as e:
        print(f"❌ Error: {e}")


def test_woocommerce():
    """Test WooCommerce connector."""
    print("\n=== Testing WooCommerce Connector ===")
    
    credentials = {
        'store_url': 'https://your-store.com',
        'consumer_key': 'ck_YOUR_CONSUMER_KEY',
        'consumer_secret': 'cs_YOUR_CONSUMER_SECRET'
    }
    
    try:
        connector = WooCommerceConnector(credentials)
        
        if connector.authenticate():
            print("✅ Authentication successful")
            
            since = datetime.now() - timedelta(days=90)
            orders = connector.fetch_orders(since=since)
            
            print(f"✅ Fetched {len(orders)} orders")
        else:
            print("❌ Authentication failed")
    
    except Exception as e:
        print(f"❌ Error: {e}")


def test_prestashop():
    """Test PrestaShop connector."""
    print("\n=== Testing PrestaShop Connector ===")
    
    credentials = {
        'store_url': 'https://your-store.com',
        'api_key': 'YOUR_API_KEY_HERE'
    }
    
    try:
        connector = PrestaShopConnector(credentials)
        
        if connector.authenticate():
            print("✅ Authentication successful")
            
            since = datetime.now() - timedelta(days=90)
            orders = connector.fetch_orders(since=since)
            
            print(f"✅ Fetched {len(orders)} orders")
        else:
            print("❌ Authentication failed")
    
    except Exception as e:
        print(f"❌ Error: {e}")


def test_credentials_manager():
    """Test credentials manager."""
    print("\n=== Testing Credentials Manager ===")
    
    manager = CredentialsManager()
    
    # Store test credentials
    test_client_id = "test@example.com"
    test_credentials = {
        'shop_domain': 'test-shop.myshopify.com',
        'access_token': 'test_token_123456'
    }
    
    if manager.store_credentials(test_client_id, 'shopify', test_credentials):
        print("✅ Credentials stored successfully")
        
        # Retrieve credentials
        retrieved = manager.get_credentials(test_client_id)
        if retrieved and retrieved['shop_domain'] == test_credentials['shop_domain']:
            print("✅ Credentials retrieved successfully")
            print(f"  - Platform: {retrieved['platform']}")
            print(f"  - Shop Domain: {retrieved['shop_domain']}")
        else:
            print("❌ Failed to retrieve credentials")
        
        # Delete credentials
        if manager.delete_credentials(test_client_id):
            print("✅ Credentials deleted successfully")
        else:
            print("❌ Failed to delete credentials")
    else:
        print("❌ Failed to store credentials")


def main():
    """Run all tests."""
    print("="*60)
    print("E-commerce Platform Connectors - Test Suite")
    print("="*60)
    
    # Test credentials manager first
    test_credentials_manager()
    
    # Test platform connectors (will fail without real credentials)
    print("\n\n⚠️  Platform connector tests require valid credentials")
    print("Update the credentials in the test functions before running")
    
    # Uncomment to test with real credentials:
    # test_shopify()
    # test_woocommerce()
    # test_prestashop()
    
    print("\n" + "="*60)
    print("✅ Tests completed")
    print("="*60)


if __name__ == "__main__":
    main()
