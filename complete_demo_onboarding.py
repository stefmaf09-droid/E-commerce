"""
Marquer le compte démo comme onboarding complété.
"""
import sys
import os

root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(root_dir, 'src'))
sys.path.insert(0, root_dir)

from onboarding.onboarding_manager import OnboardingManager

def complete_demo_onboarding():
    """Marque l'onboarding du compte démo comme complet."""
    print("🔧 Finalisation de l'onboarding du compte démo...")
    
    email = "demo@refundly.ai"
    onboarding = OnboardingManager()
    
    # Initialiser le statut
    try:
        onboarding.initialize_onboarding(email)
        print("✅ Onboarding initialisé")
    except Exception as e:
        print(f"⚠️ Erreur initialisation: {e}")
    
    # Marquer toutes les étapes comme complètes
    steps = ['account_created', 'store_setup', 'bank_info']
    
    for step in steps:
        try:
            onboarding.mark_step_complete(email, step)
            print(f"✅ Étape '{step}' marquée comme complète")
        except Exception as e:
            print(f"⚠️ Erreur step {step}: {e}")
    
    # Vérifier
    status = onboarding.get_onboarding_status(email)
    print("\n📊 Statut final:")
    print(f"   Account Created: {status['account_created']}")
    print(f"   Store Connected: {status['store_connected']}")
    print(f"   Bank Info Added: {status['bank_info_added']}")
    print(f"   Onboarding Complete: {status['onboarding_complete']}")
    
    if status['onboarding_complete']:
        print("\n✨ SUCCESS ! Le compte démo peut accéder au dashboard !")
    else:
        print("\n⚠️ Onboarding pas encore complet")

if (__name__ == "__main__"):
    complete_demo_onboarding()
