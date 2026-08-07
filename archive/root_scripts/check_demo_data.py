"""
Script to check if admin user has demo data (disputes).
"""
import sys
import os
import sqlite3

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from database.database_manager import DatabaseManager

def check_admin_data():
    """Check data for admin@refundly.ai."""
    
    email = "admin@refundly.ai"
    
    # Get client ID
    conn = sqlite3.connect('data/recours_ecommerce.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, email FROM clients WHERE email = ?", (email,))
    client = cursor.fetchone()
    
    if not client:
        print(f"❌ Client {email} not found in database!")
        return
        
    client_id = client[0]
    print(f"✅ Found Client ID: {client_id}")
    
    # Check claims
    cursor.execute("SELECT COUNT(*), SUM(amount_requested) FROM claims WHERE client_id = ?", (client_id,))
    claims_stats = cursor.fetchone()
    
    count = claims_stats[0]
    total = claims_stats[1] or 0
    
    print(f"\n📊 Data Statistics:")
    print(f"   - Claims: {count}")
    print(f"   - Total Amount: {total:.2f}€")
    
    if count == 0:
        print("\n⚠️ No data found! Recommended to generate demo data.")
    else:
        print("\n✅ Data present for demo.")
        
    conn.close()

if __name__ == "__main__":
    check_admin_data()
