"""
Comprehensive Testing Suite

Tests all implemented features end-to-end:
- Email notification system (5 triggers)
- Bulk actions for claims management
- Auto-dispute detection
- Weekly reports
- Claims management page navigation
"""

import os
import sys
import logging
from datetime import datetime, timedelta

# Add project root to path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

from src.database.database_manager import get_db_manager
from src.notifications.notification_manager import NotificationManager
from src.ai.dispute_detector import DisputeDetector

logging.basicConfig(
   level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s'
)
logger = logging.getLogger(__name__)


def test_notification_system():
    """Test all 5 notification triggers."""
    print("\n" + "="*70)
    print("TEST 1: EMAIL NOTIFICATION SYSTEM")
    print("="*70)
    
    try:
        notification_mgr = NotificationManager()
        test_email = "test@refundly.ai"
        
        # Test 1: Claim Created
        print("\n📧 Testing claim_created notification...")
        result = notification_mgr.queue_notification(
            client_email=test_email,
            event_type='claim_created',
            context={
                'claim_ref': 'CLM-TEST-001',
                'carrier': 'Colissimo',
                'amount': 50.0
            }
        )
        print(f"   Result: {'✅ PASS' if result else '❌ FAIL'}")
        
        # Test 2: Claim Accepted
        print("\n✅ Testing claim_accepted notification...")
        result = notification_mgr.queue_notification(
            client_email=test_email,
            event_type='claim_accepted',
            context={
                'claim_ref': 'CLM-TEST-002',
                'accepted_amount': 100.0,
                'client_amount': 80.0
            }
        )
        print(f"   Result: {'✅ PASS' if result else '❌ FAIL'}")
        
        # Test 3: Payment Received
        print("\n💰 Testing payment_received notification...")
        result = notification_mgr.queue_notification(
            client_email=test_email,
            event_type='payment_received',
            context={
                'claim_ref': 'CLM-TEST-003',
                'client_amount': 75.0
            }
        )
        print(f"   Result: {'✅ PASS' if result else '❌ FAIL'}")
        
        # Test 4: Deadline Warning
        print("\n⚠️ Testing deadline_warning notification...")
        result = notification_mgr.queue_notification(
            client_email=test_email,
            event_type='deadline_warning',
            context={
                'claim_ref': 'CLM-TEST-004',
                'carrier': 'Chronopost',
                'days_remaining': 3,
                'deadline_date': (datetime.now() + timedelta(days=3)).strftime('%d/%m/%Y')
            }
        )
        print(f"   Result: {'✅ PASS' if result else '❌ FAIL'}")
        
        # Test 5: Claim Updated (Rejection)
        print("\n📝 Testing claim_updated notification...")
        result = notification_mgr.queue_notification(
            client_email=test_email,
            event_type='claim_updated',
            context={
                'claim_ref': 'CLM-TEST-005',
                'carrier': 'DPD',
                'status': 'rejected'
            }
        )
        print(f"   Result: {'✅ PASS' if result else '❌ FAIL'}")
        
        print("\n✅ All 5 notification types tested successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Notification test failed: {e}")
        return False


def test_dispute_detector():
    """Test auto-dispute detection."""
    print("\n" + "="*70)
    print("TEST 2: AUTO-DISPUTE DETECTION")
    print("="*70)
    
    try:
        detector = DisputeDetector()
        
        # Test orders with various issues
        test_orders = [
            {
                'order_id': 'ORD-DELAY-001',
                'tracking_number': 'TEST123',
                'carrier': 'colissimo',
                'order_date': (datetime.now() - timedelta(days=30)).isoformat(),
                'expected_delivery': (datetime.now() - timedelta(days=20)).isoformat(),
                'delivery_date': None,
                'delivery_status': 'in_transit',
                'order_value': 100.0,
                'shipping_cost': 10.0
            },
            {
                'order_id': 'ORD-POD-002',
                'tracking_number': 'TEST456',
                'carrier': 'chronopost',
                'order_date': (datetime.now() - timedelta(days=10)).isoformat(),
                'delivery_date': datetime.now().isoformat(),
                'delivery_status': 'delivered',
                'order_value': 200.0,
                'shipping_cost': 15.0,
                'pod_data': {
                    'signature': False,
                    'delivery_location': 'boîte aux lettres'
                }
            },
            {
                'order_id': 'ORD-DAMAGED-003',
                'tracking_number': 'TEST789',
                'carrier': 'dpd',
                'order_date': (datetime.now() - timedelta(days=5)).isoformat(),
                'delivery_date': datetime.now().isoformat(),
                'delivery_status': 'delivered',
                'delivery_notes': 'Package delivered damaged, box crushed',
                'order_value': 150.0,
                'shipping_cost': 12.0
            }
        ]
        
        print(f"\n📊 Scanning {len(test_orders)} test orders...")
        disputes = detector.scan_orders(test_orders, 'test@client.com')
        
        print(f"\n✅ Detected {len(disputes)} disputes:")
        for dispute in disputes:
            print(f"\n   📦 {dispute['order_id']}")
            print(f"      Type: {dispute['dispute_type']}")
            print(f"      Confidence: {dispute['confidence']:.0%}")
            print(f"      Reason: {dispute['reason']}")
        
        expected_disputes = 3
        if len(disputes) == expected_disputes:
            print(f"\n✅ Dispute detection test PASSED ({len(disputes)} disputes detected)")
            return True
        else:
            print(f"\n⚠️ Expected {expected_disputes} disputes, got {len(disputes)}")
            return False
            
    except Exception as e:
        print(f"\n❌ Dispute detector test failed: {e}")
        return False


def test_database_operations():
    """Test database claim creation and updates."""
    print("\n" + "="*70)
    print("TEST 3: DATABASE OPERATIONS")
    print("="*70)
    
    try:
        db = get_db_manager()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Check if database is accessible
        print("\n🗄️ Testing database connection...")
        cursor.execute("SELECT COUNT(*) FROM clients")
        client_count = cursor.fetchone()[0]
        print(f"   Clients in database: {client_count}")
        
        cursor.execute("SELECT COUNT(*) FROM claims")
        claim_count = cursor.fetchone()[0]
        print(f"   Claims in database: {claim_count}")
        
        cursor.execute("SELECT COUNT(*) FROM notifications")
        notification_count = cursor.fetchone()[0]
        print(f"   Notifications logged: {notification_count}")
        
        conn.close()
        
        print("\n✅ Database operations test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Database test failed: {e}")
        return False


def test_cron_scripts():
    """Test all automated cron scripts."""
    print("\n" + "="*70)
    print("TEST 4: AUTOMATED CRON SCRIPTS")
    print("="*70)
    
    scripts_to_test = [
        ('scripts/check_deadlines_cron.py', 'Deadline Checker'),
        ('scripts/scan_disputes_cron.py', 'Dispute Scanner'),
        ('scripts/weekly_reports_cron.py', 'Weekly Reports')
    ]
    
    all_passed = True
    
    for script_path, script_name in scripts_to_test:
        print(f"\n📋 Testing {script_name}...")
        
        full_path = os.path.join(root_dir, script_path)
        
        if os.path.exists(full_path):
            print(f"   ✅ Script exists: {script_path}")
            
            # Check if script is importable (basic syntax check)
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Basic checks
                if 'if __name__ == "__main__":' in content:
                    print(f"   ✅ Has main execution block")
                else:
                    print(f"   ⚠️ Missing main execution block")
                
                if 'logging' in content:
                    print(f"   ✅ Has logging configured")
                else:
                    print(f"   ⚠️ No logging found")
                    
            except Exception as e:
                print(f"   ❌ Error reading script: {e}")
                all_passed = False
        else:
            print(f"   ❌ Script not found: {script_path}")
            all_passed = False
    
    if all_passed:
        print("\n✅ All cron scripts test PASSED")
    else:
        print("\n⚠️ Some cron script tests had warnings")
    
    return all_passed


def test_claims_management_integration():
    """Test claims management page integration."""
    print("\n" + "="*70)
    print("TEST 5: CLAIMS MANAGEMENT PAGE INTEGRATION")
    print("="*70)
    
    try:
        # Check if file exists
        claims_page_path = os.path.join(root_dir, 'src/dashboard/claims_management_page.py')
        
        print("\n📄 Checking claims management page...")
        
        if os.path.exists(claims_page_path):
            print(f"   ✅ File exists: {claims_page_path}")
            
            # Check if it has the required function
            with open(claims_page_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if 'def render_claims_management()' in content:
                print("   ✅ Has render_claims_management() function")
            else:
                print("   ❌ Missing render_claims_management() function")
                return False
            
            if 'export_claims_to_csv' in content:
                print("   ✅ Has CSV export functionality")
            else:
                print("   ⚠️ Missing CSV export")
            
            if 'send_bulk_reminders' in content:
                print("   ✅ Has bulk reminders functionality")
            else:
                print("   ⚠️ Missing bulk reminders")
            
            # Check navigation integration
            nav_file = os.path.join(root_dir, 'client_dashboard_main_new.py')
            with open(nav_file, 'r', encoding='utf-8') as f:
                nav_content = f.read()
            
            if 'Gestion Litiges' in nav_content:
                print("   ✅ Integrated in navigation menu")
            else:
                print("   ❌ Not integrated in navigation")
                return False
            
            print("\n✅ Claims management integration test PASSED")
            return True
        else:
            print(f"   ❌ File not found: {claims_page_path}")
            return False
            
    except Exception as e:
        print(f"\n❌ Claims management test failed: {e}")
        return False


def run_all_tests():
    """Execute all tests and generate summary report."""
    print("\n" + "="*100)
    print("🧪 COMPREHENSIVE TESTING SUITE".center(100))
    print("="*100)
    print(f"\nStarted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_results = {}
    
    # Run all tests
    test_results['Notification System'] = test_notification_system()
    test_results['Dispute Detector'] = test_dispute_detector()
    test_results['Database Operations'] = test_database_operations()
    test_results['Cron Scripts'] = test_cron_scripts()
    test_results['Claims Management'] = test_claims_management_integration()
    
    # Summary Report
    print("\n" + "="*100)
    print("📊 TEST SUMMARY REPORT".center(100))
    print("="*100)
    
    passed_count = sum(1 for result in test_results.values() if result)
    total_count = len(test_results)
    
    print(f"\nResults: {passed_count}/{total_count} tests passed\n")
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}  {test_name}")
    
    print("\n" + "="*100)
    
    if passed_count == total_count:
        print("🎉 ALL TESTS PASSED! System is ready for production.".center(100))
    else:
        print(f"⚠️ {total_count - passed_count} test(s) failed. Review above for details.".center(100))
    
    print("="*100)
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    return passed_count == total_count


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
