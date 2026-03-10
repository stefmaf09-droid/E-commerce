"""Crée le compte demo@refundly.ai avec mdp 'demo' dans la DB passwords."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.auth.password_manager import PasswordManager
pm = PasswordManager()
email = "demo@refundly.ai"
if pm.set_client_password(email, "demo"):
    print(f"✅ Compte {email} configuré avec le mot de passe 'demo'")
else:
    print(f"❌ Echec pour {email}")
