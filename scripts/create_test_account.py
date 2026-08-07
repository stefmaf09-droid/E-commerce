"""
Script to create a test admin account for the dashboard.
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from auth.credentials_manager import CredentialsManager
from auth.password_manager import set_client_password

def create_test_account():
    """Create a test admin account."""
    
    email = "admin@refundly.ai"
    password = "admin123"
    
    # Create credentials
    manager = CredentialsManager()
    
    # Store basic credentials
    credentials = {
        'shop_url': 'demo-store.myshopify.com',
        'access_token': 'demo_access_token',
        'store_name': 'Demo Admin Store',
    }
    
    success = manager.store_credentials(
        client_id=email,
        platform='shopify',
        credentials=credentials
    )
    
    if success:
        print(f"✅ Credentials stored for {email}")
        
        # Set password
        pwd_success = set_client_password(email, password)
        
        if pwd_success:
            print(f"✅ Password set successfully")
            print(f"\n📧 Email: {email}")
            print(f"🔑 Password: {password}")
            print(f"\n✨ You can now log in to the dashboard!")
        else:
            print(f"❌ Failed to set password")
    else:
        print(f"❌ Failed to store credentials")

if __name__ == "__main__":
    create_test_account()
