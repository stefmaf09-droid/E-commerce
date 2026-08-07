"""
Script to mark admin account onboarding as complete.
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from onboarding.onboarding_manager import OnboardingManager

def complete_admin_onboarding():
    """Mark admin account onboarding as complete."""
    
    email = "admin@refundly.ai"
    
    onboarding_mgr = OnboardingManager()
    
    # Initialize if not exists
    onboarding_mgr.initialize_onboarding(email)
    
    # Mark all steps as complete using CORRECT step names
    print(f"🔄 Completing steps for {email}...")
    
    # Step 1: Store Setup
    if onboarding_mgr.mark_step_complete(email, 'store_setup'):
        print("  ✅ Store setup marked complete")
    else:
        print("  ❌ Failed to mark store setup complete")
        
    # Step 2: Bank Info
    if onboarding_mgr.mark_step_complete(email, 'bank_info'):
        print("  ✅ Bank info marked complete")
    else:
        print("  ❌ Failed to mark bank info complete")
    
    # Final: Mark fully complete
    if onboarding_mgr.mark_complete(email):
        print("  ✅ Onboarding fully marked complete")
    else:
        print("  ❌ Failed to mark onboarding complete")
    
    # Verify completion
    is_complete = onboarding_mgr.is_onboarding_complete(email)
    status = onboarding_mgr.get_onboarding_status(email)
    
    if is_complete:
        print(f"\n🎉 SUCCESS: Onboarding is complete for {email}")
        print(f"Current status: {status}")
        print(f"🚀 You can now log in to the dashboard!")
    else:
        print(f"\n❌ FAILURE: Onboarding still incomplete")
        print(f"Current status: {status}")

if __name__ == "__main__":
    complete_admin_onboarding()
