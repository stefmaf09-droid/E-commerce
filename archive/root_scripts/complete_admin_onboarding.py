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
    
    # Mark all steps as complete
    onboarding_mgr.mark_step_complete(email, 'store_setup')
    onboarding_mgr.mark_step_complete(email, 'banking_info')
    onboarding_mgr.mark_step_complete(email, 'welcome_tour')
    
    # Verify completion
    is_complete = onboarding_mgr.is_onboarding_complete(email)
    
    if is_complete:
        print(f"✅ Onboarding marked as complete for {email}")
        print(f"🎯 The account can now access the full dashboard!")
    else:
        print(f"❌ Failed to complete onboarding")
        
        # Show status
        status = onboarding_mgr.get_onboarding_status(email)
        print(f"\nCurrent status: {status}")

if __name__ == "__main__":
    complete_admin_onboarding()
