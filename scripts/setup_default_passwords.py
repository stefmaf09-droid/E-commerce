"""
Setup Default Passwords - Initialize passwords for existing clients.

This script should be run once after deploying the password authentication system.
It creates default passwords for all existing clients in the credentials database.
"""

import sys
sys.path.insert(0, 'src')

from auth.credentials_manager import CredentialsManager
from auth.password_manager import PasswordManager, set_client_password
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default password for all clients (should be changed after first login)
DEFAULT_PASSWORD = "demo123"


def setup_default_passwords():
    """Initialize default passwords for all existing clients."""
    print("="*70)
    print("SETUP DEFAULT PASSWORDS")
    print("="*70)
    
    # Get all clients
    creds_manager = CredentialsManager()
    clients = creds_manager.list_clients()
    
    if not clients:
        print("\n⚠️ No clients found in database")
        return
    
    print(f"\n📊 Found {len(clients)} client(s)")
    print()
    
    # Password manager
    pwd_manager = PasswordManager()
    
    results = []
    
    for client_id, platform, created_at in clients:
        print(f"Processing: {client_id} ({platform})...")
        
        # Check if password already exists
        if pwd_manager.has_password(client_id):
            print(f"  ℹ️  Password already set - skipping")
            results.append({
                'email': client_id,
                'status': 'SKIPPED (already has password)',
                'password': 'N/A'
            })
        else:
            # Set default password
            success = pwd_manager.set_client_password(client_id, DEFAULT_PASSWORD)
            
            if success:
                print(f"  ✅ Password set successfully")
                results.append({
                    'email': client_id,
                    'status': 'SUCCESS',
                    'password': DEFAULT_PASSWORD
                })
            else:
                print(f"  ❌ Failed to set password")
                results.append({
                    'email': client_id,
                    'status': 'FAILED',
                    'password': 'N/A'
                })
        
        print()
    
    # Summary
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print()
    
    success_count = len([r for r in results if r['status'] == 'SUCCESS'])
    skipped_count = len([r for r in results if r['status'].startswith('SKIPPED')])
    failed_count = len([r for r in results if r['status'] == 'FAILED'])
    
    print(f"✅ Successfully set: {success_count}")
    print(f"ℹ️  Skipped: {skipped_count}")
    print(f"❌ Failed: {failed_count}")
    print()
    
    # Print credentials for new passwords
    new_passwords = [r for r in results if r['status'] == 'SUCCESS']
    
    if new_passwords:
        print("="*70)
        print("NEW CLIENT CREDENTIALS")
        print("="*70)
        print()
        print("⚠️  IMPORTANT: Communicate these credentials to the clients")
        print("   They should change their password after first login")
        print()
        
        for result in new_passwords:
            print(f"Email:    {result['email']}")
            print(f"Password: {result['password']}")
            print("-" * 50)
        
        # Save to file
        with open('data/default_passwords.txt', 'w', encoding='utf-8') as f:
            f.write("DEFAULT CLIENT CREDENTIALS\n")
            f.write("="*70 + "\n\n")
            f.write("⚠️ IMPORTANT: These are temporary passwords.\n")
            f.write("   Clients should change them after first login.\n\n")
            
            for result in new_passwords:
                f.write(f"Email:    {result['email']}\n")
                f.write(f"Password: {result['password']}\n")
                f.write("-" * 50 + "\n")
        
        print()
        print(f"✅ Credentials saved to: data/default_passwords.txt")
    
    print()
    print("="*70)
    print("✅ Setup Complete")
    print("="*70)


if __name__ == "__main__":
    import os
    
    # Create data directory if needed
    os.makedirs('data', exist_ok=True)
    
    # Run setup
    setup_default_passwords()
