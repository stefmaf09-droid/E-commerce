import logging
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.connectors.dhl_connector import DHLConnector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_dhl_connection():
    # Credentials from the created app
    API_KEY = "OCaoGF7up5Df9JBSGnds8QJWUCVKA9qJ"
    
    print(f"Testing DHL API with Key: {API_KEY[:5]}...")
    
    connector = DHLConnector(api_key=API_KEY)
    
    # Test with a potentially valid (or at least formatted) tracking number
    # DHL Express often looks like 10 digits
    TEST_TRACKING_NUMBER = "1234567890" 
    
    result = connector.get_tracking(TEST_TRACKING_NUMBER)
    
    print("\n--- Result ---")
    if result:
        print(f"Status: {result.get('status')}")
        print(f"Delivered: {result.get('is_delivered')}")
        print(f"Full Data: {result}")
        
        if result.get('status') == 'not_found':
            print("\n✅ Connection Successful! (Even if tracking number is not found, the API replied)")
        else:
            print("\n✅ Connection Successful! Data retrieved.")
    else:
        print("\n❌ Connection Failed or No Data.")

if __name__ == "__main__":
    test_dhl_connection()
