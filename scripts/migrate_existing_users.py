"""
Migration Script: Mark Existing Users as Onboarding Complete

This script marks all existing users in the system as having completed
the onboarding process, so they can access the dashboard directly without
going through the onboarding steps.

Run this script ONCE after deploying the onboarding feature.
"""

import sys
sys.path.insert(0, 'src')

from auth.credentials_manager import CredentialsManager
from onboarding.onboarding_manager import OnboardingManager


def migrate_existing_users():
    """Mark all existing users as onboarding complete."""
    print("=" * 60)
    print("Migration: Marking Existing Users as Onboarding Complete")
    print("=" * 60)
    print()
    
    # Get all stored clients
    manager = CredentialsManager()
    onboarding_manager = OnboardingManager()
    
    # Get all stored clients (from credentials database)
    try:
        import sqlite3
        conn = sqlite3.connect('database/credentials.db')
        cursor = conn.cursor()
        
        # Get unique client emails
        cursor.execute("""
            SELECT DISTINCT client_id FROM credentials
        """)
        
        clients = cursor.fetchall()
        conn.close()
        
        if not clients:
            print("✅ No existing clients found. Migration complete.")
            return
        
        print(f"Found {len(clients)} existing client(s).")
        print()
        
        # Mark each as onboarding complete
        migrated_count = 0
        
        for (client_email,) in clients:
            print(f"Processing: {client_email}")
            
            # Check if already has onboarding status
            if onboarding_manager.is_onboarding_complete(client_email):
                print(f"  ➜ Already marked as complete. Skipping.")
            else:
                # Initialize and immediately mark as complete
                onboarding_manager.initialize_onboarding(client_email)
                onboarding_manager.mark_complete(client_email)
                print(f"  ✅ Marked as onboarding complete")
                migrated_count += 1
            
            print()
        
        print("=" * 60)
        print(f"✅ Migration complete!")
        print(f"   - Total clients: {len(clients)}")
        print(f"   - Migrated: {migrated_count}")
        print(f"   - Already migrated: {len(clients) - migrated_count}")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print()
    print("⚠️  WARNING: This script will mark ALL existing users as onboarding complete.")
    print("   New users will still go through the onboarding flow.")
    print()
    
    response = input("Continue? (yes/no): ").strip().lower()
    
    if response == "yes":
        migrate_existing_users()
    else:
        print("Migration cancelled.")
