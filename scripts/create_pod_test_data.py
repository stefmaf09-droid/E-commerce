"""
POD Test Data Generator

Creates test claims with various POD fetch statuses for testing bulk retry functionality.
"""

import os
import sys
from datetime import datetime, timedelta
import random

# Add project to path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

from src.database.database_manager import get_db_manager


def create_pod_test_data():
    """Create test claims with various POD statuses."""
    db = get_db_manager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Get or create test client
    cursor.execute("SELECT id FROM clients WHERE email = ?", ('pod_test@refundly.ai',))
    result = cursor.fetchone()
    
    if not result:
        # Create test client
        cursor.execute("""
            INSERT INTO clients (email, company_name, stripe_connect_id, created_at)
            VALUES (?, ?, ?, ?)
        """, ('pod_test@refundly.ai', 'POD Test Company', None, datetime.now()))
        client_id = cursor.lastrowid
        print(f"✅ Created test client: pod_test@refundly.ai (ID: {client_id})")
    else:
        client_id = result[0]
        print(f"✅ Using existing test client (ID: {client_id})")
    
    # Test data configuration
    test_claims = [
        # Failed PODs (for bulk retry testing)
        {
            'carrier': 'Colissimo',
            'tracking': 'COL123456789FR',
            'pod_status': 'failed',
            'pod_error': 'API timeout - Connection lost'
        },
        {
            'carrier': 'Chronopost',
            'tracking': 'CH987654321FR',
            'pod_status': 'failed',
            'pod_error': 'Package not yet delivered'
        },
        {
            'carrier': 'UPS',
            'tracking': 'UPS1Z999AA10123456',
            'pod_status': 'failed',
            'pod_error': 'Tracking number not found'
        },
        {
            'carrier': 'Colissimo',
            'tracking': 'COL555666777FR',
            'pod_status': 'failed',
            'pod_error': 'Rate limit exceeded'
        },
        {
            'carrier': 'Chronopost',
            'tracking': 'CH111222333FR',
            'pod_status': 'failed',
            'pod_error': 'Authentication failed'
        },
        # Successful PODs
        {
            'carrier': 'Colissimo',
            'tracking': 'COL999888777FR',
            'pod_status': 'success',
            'pod_error': None,
            'pod_url': 'https://example.com/pod/COL999888777FR.pdf'
        },
        {
            'carrier': 'UPS',
            'tracking': 'UPS1Z888BB20456789',
            'pod_status': 'success',
            'pod_error': None,
            'pod_url': 'https://example.com/pod/UPS1Z888BB20456789.pdf'
        },
        # Pending PODs
        {
            'carrier': 'Chronopost',
            'tracking': 'CH444555666FR',
            'pod_status': 'pending',
            'pod_error': None
        },
        # No POD requested
        {
            'carrier': 'DHL',
            'tracking': 'DHL123456789',
            'pod_status': None,
            'pod_error': None
        },
    ]
    
    created_count = 0
    
    for idx, claim_data in enumerate(test_claims, 1):
        claim_ref = f"TEST-POD-{datetime.now().strftime('%Y%m%d')}-{idx:03d}"
        
        # Check if claim already exists
        cursor.execute("SELECT id FROM claims WHERE claim_reference = ?", (claim_ref,))
        if cursor.fetchone():
            print(f"⏭️  Claim {claim_ref} already exists, skipping")
            continue
        
        # Create claim
        cursor.execute("""
            INSERT INTO claims (
                client_id,
                claim_reference,
                order_id,
                carrier,
                tracking_number,
                dispute_type,
                amount_requested,
                status,
                submitted_at,
                response_deadline,
                pod_fetch_status,
                pod_url,
                pod_fetch_error,
                pod_fetched_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            client_id,
            claim_ref,
            f"ORD-TEST-{idx:04d}",  # Generate test order_id
            claim_data['carrier'],
            claim_data['tracking'],
            'lost',  # Required dispute_type
            random.uniform(50, 500),
            'submitted',
            datetime.now() - timedelta(days=random.randint(1, 30)),
            datetime.now() + timedelta(days=random.randint(5, 15)),
            claim_data['pod_status'],
            claim_data.get('pod_url'),
            claim_data['pod_error'],
            datetime.now() if claim_data['pod_status'] == 'success' else None
        ))
        
        created_count += 1
        
        # Show status
        status_emoji = {
            'success': '✅',
            'failed': '❌',
            'pending': '⏳',
            None: '➖'
        }
        emoji = status_emoji.get(claim_data['pod_status'], '❓')
        print(f"{emoji} Created {claim_ref}: {claim_data['carrier']} - POD status: {claim_data['pod_status']}")
    
    conn.commit()
    conn.close()
    
    print(f"\n🎉 Test data created: {created_count} new claims")
    print(f"📧 Test client email: pod_test@refundly.ai")
    print(f"\n💡 To test bulk retry:")
    print(f"   1. Login with pod_test@refundly.ai")
    print(f"   2. Go to 'Gestion des Litiges'")
    print(f"   3. Click 'Réessayer tous les échecs' button")


if __name__ == "__main__":
    print("🔧 POD Test Data Generator\n")
    try:
        create_pod_test_data()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
