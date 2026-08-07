"""
Test Complete Registration and Onboarding Flow

This script simulates a new user registration and verifies:
1. Account creation succeeds
2. Store credentials are saved
3. Onboarding is initialized with store_setup marked complete
4. User starts at step 2 (bank_info)
"""

import sys
sys.path.insert(0, 'src')

from auth.credentials_manager import CredentialsManager
from auth.password_manager import set_client_password
from onboarding.onboarding_manager import OnboardingManager
import random

# Test data
test_email = f"test.onboarding.{random.randint(1000, 9999)}@example.com"
test_password = "TestPass123!"
test_platform = "Shopify"
test_store_name = "Test Boutique Onboarding"
test_store_url = "https://test-onboarding.myshopify.com"
test_api_key = "test-shop-url.myshopify.com"
test_api_secret = "shpat_test123456789"

print("="*70)
print("TESTING COMPLETE REGISTRATION & ONBOARDING FLOW")
print("="*70)
print(f"\nTest Email: {test_email}")
print(f"Platform: {test_platform}")
print(f"Store: {test_store_name}")
print()

# Step 1: Create credentials (simulating registration)
print("Step 1: Creating store credentials...")
manager = CredentialsManager()

credentials = {
    'shop_url': test_api_key,
    'access_token': test_api_secret,
    'store_name': test_store_name,
}

success = manager.store_credentials(
    client_id=test_email,
    platform=test_platform.lower(),
    credentials=credentials
)

if success:
    print("  ✅ Store credentials saved")
else:
    print("  ❌ Failed to save credentials")
    sys.exit(1)

# Step 2: Set password
print("\nStep 2: Setting password...")
pwd_success = set_client_password(test_email, test_password)

if pwd_success:
    print("  ✅ Password set")
else:
    print("  ❌ Failed to set password")
    sys.exit(1)

# Step 3: Initialize onboarding
print("\nStep 3: Initializing onboarding...")
onboarding_mgr = OnboardingManager()
onboarding_mgr.initialize_onboarding(test_email)
print("  ✅ Onboarding initialized")

# Step 4: Mark store setup as complete (this happens during registration)
print("\nStep 4: Marking store setup as complete (done during registration)...")
onboarding_mgr.mark_step_complete(test_email, 'store_setup')
print("  ✅ Store setup marked complete")

# Step 5: Verify onboarding status
print("\nStep 5: Verifying onboarding status...")
status = onboarding_mgr.get_onboarding_status(test_email)
current_step = onboarding_mgr.get_current_step(test_email)

print(f"  Current Step: {current_step}")
print(f"  Store Connected: {status['store_connected']}")
print(f"  Bank Info Added: {status['bank_info_added']}")
print(f"  Onboarding Complete: {status['onboarding_complete']}")

# Step 6: Verify expected state
print("\n" + "="*70)
print("VERIFICATION")
print("="*70)

tests_passed = 0
tests_total = 3

# Test 1: Current step should be 'bank_info'
if current_step == 'bank_info':
    print("✅ Test 1: User starts at bank_info step (66% progress)")
    tests_passed += 1
else:
    print(f"❌ Test 1: Expected 'bank_info', got '{current_step}'")

# Test 2: Store should be connected
if status['store_connected']:
    print("✅ Test 2: Store setup marked as complete")
    tests_passed += 1
else:
    print("❌ Test 2: Store setup not marked complete")

# Test 3: Onboarding should not be complete yet
if not status['onboarding_complete']:
    print("✅ Test 3: Onboarding not complete (as expected)")
    tests_passed += 1
else:
    print("❌ Test 3: Onboarding incorrectly marked as complete")

print("\n" + "="*70)
if tests_passed == tests_total:
    print(f"✅ ALL TESTS PASSED ({tests_passed}/{tests_total})")
    print("\nYou can now login with:")
    print(f"  Email: {test_email}")
    print(f"  Password: {test_password}")
    print("\nExpected behavior:")
    print("  - Progress bar shows 66%")
    print("  - First screen is 'Informations bancaires' (Step 2)")
    print("  - No duplicate store setup screen")
else:
    print(f"❌ SOME TESTS FAILED ({tests_passed}/{tests_total})")

print("="*70)

def test_multi_store_onboarding():
    """Test onboarding avec plusieurs boutiques pour un même utilisateur."""
    manager = CredentialsManager()
    onboarding_mgr = OnboardingManager()
    email = f"multi.store.{random.randint(1000,9999)}@example.com"
    stores = [
        {"platform": "Shopify", "store_name": "Boutique1", "store_url": "https://b1.myshopify.com", "api_key": "b1.myshopify.com", "api_secret": "shpat_1"},
        {"platform": "WooCommerce", "store_name": "Boutique2", "store_url": "https://b2.woocommerce.com", "api_key": "ck_2", "api_secret": "cs_2"},
    ]
    for s in stores:
        manager.store_credentials(email, s["platform"], {"shop_url": s["store_url"]}, s["store_name"])
    onboarding_mgr.initialize_onboarding(email)
    status = onboarding_mgr.get_onboarding_status(email)
    assert status["account_created"] is True
    assert status["current_step"] == 1
    print(f"Multi-store onboarding OK for {email}")
