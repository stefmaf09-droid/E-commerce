"""
Delete Client Script - Remove all data for a specific client email

This script removes:
- Credentials from database/credentials.db
- Onboarding status from database/client_data.db
- Password from database/client_passwords.db
- Payment data from database/manual_payments.db
"""

import sys
import sqlite3
from pathlib import Path

sys.path.insert(0, 'src')


def list_recent_clients():
    """List recent clients for selection."""
    try:
        conn = sqlite3.connect('database/credentials.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT client_id, platform, created_at 
            FROM credentials 
            ORDER BY created_at DESC
            LIMIT 10
        """)
        
        clients = cursor.fetchall()
        conn.close()
        
        if not clients:
            print("No clients found.")
            return []
        
        print("\n" + "="*70)
        print("RECENT CLIENTS")
        print("="*70)
        
        for idx, (email, platform, created_at) in enumerate(clients, 1):
            print(f"{idx}. {email} ({platform}) - Created: {created_at}")
        
        return [c[0] for c in clients]
        
    except Exception as e:
        print(f"Error listing clients: {e}")
        return []


def delete_client_data(client_email: str):
    """Delete all data for a client across all databases."""
    print(f"\n{'='*70}")
    print(f"DELETING DATA FOR: {client_email}")
    print(f"{'='*70}\n")
    
    deleted_count = 0
    
    # 1. Delete from credentials.db
    try:
        conn = sqlite3.connect('database/credentials.db')
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM sync_status WHERE client_id = ?", (client_email,))
        cursor.execute("DELETE FROM credentials WHERE client_id = ?", (client_email,))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        if deleted > 0:
            print(f"✅ Deleted credentials ({deleted} row(s))")
            deleted_count += deleted
        else:
            print("⏭️  No credentials found")
            
    except Exception as e:
        print(f"❌ Error deleting credentials: {e}")
    
    # 2. Delete from client_data.db (onboarding)
    try:
        conn = sqlite3.connect('database/client_data.db')
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM onboarding_status WHERE client_email = ?", (client_email,))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        if deleted > 0:
            print(f"✅ Deleted onboarding status ({deleted} row(s))")
            deleted_count += deleted
        else:
            print("⏭️  No onboarding status found")
            
    except Exception as e:
        print(f"❌ Error deleting onboarding status: {e}")
    
    # 3. Delete from client_passwords.db
    try:
        if Path('database/client_passwords.db').exists():
            conn = sqlite3.connect('database/client_passwords.db')
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM passwords WHERE client_email = ?", (client_email,))
            
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            
            if deleted > 0:
                print(f"✅ Deleted password ({deleted} row(s))")
                deleted_count += deleted
            else:
                print("⏭️  No password found")
        else:
            print("⏭️  No password database found")
            
    except Exception as e:
        print(f"❌ Error deleting password: {e}")
    
    # 4. Delete from manual_payments.db
    try:
        if Path('database/manual_payments.db').exists():
            conn = sqlite3.connect('database/manual_payments.db')
            cursor = conn.cursor()
            
            # Delete IBAN
            cursor.execute("DELETE FROM client_ibans WHERE client_email = ?", (client_email,))
            iban_deleted = cursor.rowcount
            
            # Delete payment records
            cursor.execute("DELETE FROM payment_records WHERE client_email = ?", (client_email,))
            payment_deleted = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            if iban_deleted > 0 or payment_deleted > 0:
                print(f"✅ Deleted payment data (IBAN: {iban_deleted}, Records: {payment_deleted})")
                deleted_count += iban_deleted + payment_deleted
            else:
                print("⏭️  No payment data found")
        else:
            print("⏭️  No payment database found")
            
    except Exception as e:
        print(f"❌ Error deleting payment data: {e}")
    
    print(f"\n{'='*70}")
    if deleted_count > 0:
        print(f"✅ DELETION COMPLETE - Total rows deleted: {deleted_count}")
    else:
        print(f"⚠️  NO DATA FOUND FOR {client_email}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("CLIENT DELETION TOOL")
    print("="*70)
    
    # List recent clients
    clients = list_recent_clients()
    
    if not clients:
        print("\nNo clients to delete.")
        sys.exit(0)
    
    print("\nOptions:")
    print("  - Enter a number (1-10) to select a client")
    print("  - Enter an email address directly")
    print("  - Enter 'cancel' to exit")
    print()
    
    choice = input("Your choice: ").strip()
    
    if choice.lower() == 'cancel':
        print("Cancelled.")
        sys.exit(0)
    
    # Check if it's a number
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(clients):
            client_email = clients[idx]
        else:
            print(f"Invalid selection. Must be between 1 and {len(clients)}")
            sys.exit(1)
    else:
        client_email = choice
    
    # Confirm deletion
    print(f"\n⚠️  WARNING: This will permanently delete ALL data for: {client_email}")
    confirm = input("Type 'DELETE' to confirm: ").strip()
    
    if confirm == 'DELETE':
        delete_client_data(client_email)
    else:
        print("Deletion cancelled.")
