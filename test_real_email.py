"""
Test d'envoi d'email réel avec Gmail.

ATTENTION: Ce script envoie de VRAIS emails !
Assurez-vous d'avoir configuré vos credentials Gmail dans .env

Configuration requise dans .env:
    GMAIL_SENDER=votre.email@gmail.com
    GMAIL_APP_PASSWORD=abcd efgh ijkl mnop
"""

import os
import sys
from dotenv import load_dotenv

# Charger variables d'environnement
load_dotenv()

# Ajouter src au path
sys.path.insert(0, 'src')

from email_service.email_sender import send_disputes_detected_email, send_claim_submitted_email


def check_configuration():
    """Vérifier que les credentials sont configurés."""
    print("🔍 Vérification de la configuration...")
    print("-" * 60)
    
    gmail_sender = os.getenv('GMAIL_SENDER')
    gmail_password = os.getenv('GMAIL_APP_PASSWORD')
    
    if not gmail_sender:
        print("❌ GMAIL_SENDER non configuré dans .env")
        return False
    
    if not gmail_password:
        print("❌ GMAIL_APP_PASSWORD non configuré dans .env")
        return False
    
    print(f"✅ GMAIL_SENDER: {gmail_sender}")
    print(f"✅ GMAIL_APP_PASSWORD: {'*' * len(gmail_password)} (masqué)")
    print("-" * 60)
    
    return True


def test_disputes_detected_email():
    """Tester l'email 'Nouveaux litiges détectés'."""
    print("\n📧 Test 1: Email 'Nouveaux litiges détectés'")
    print("-" * 60)
    
    # CHANGEZ CETTE ADRESSE PAR LA VÔTRE !
    test_email = input("Entrez votre email de test (ou appuyez sur Enter pour utiliser GMAIL_SENDER): ").strip()
    
    if not test_email:
        test_email = os.getenv('GMAIL_SENDER')
    
    print(f"📨 Envoi vers: {test_email}")
    
    result = send_disputes_detected_email(
        client_email=test_email,
        disputes_count=3,
        total_amount=450.00,
        disputes_summary=[
            {
                'order_id': 'ORD-TEST-001',
                'carrier': 'Colissimo',
                'dispute_type': 'late_delivery',
                'total_recoverable': 150.0,
                'tracking_number': 'FR123456789'
            },
            {
                'order_id': 'ORD-TEST-002',
                'carrier': 'Chronopost',
                'dispute_type': 'lost',
                'total_recoverable': 200.0,
                'tracking_number': 'CH987654321'
            },
            {
                'order_id': 'ORD-TEST-003',
                'carrier': 'DHL',
                'dispute_type': 'damaged',
                'total_recoverable': 100.0,
                'tracking_number': 'DHL555666777'
            }
        ]
    )
    
    if result:
        print("✅ Email envoyé avec succès !")
        print(f"📬 Vérifiez votre boîte mail: {test_email}")
        return True
    else:
        print("❌ Échec de l'envoi de l'email")
        print("\nVérifications à faire:")
        print("  1. Vérifiez GMAIL_SENDER et GMAIL_APP_PASSWORD dans .env")
        print("  2. Vérifiez votre connexion internet")
        print("  3. Vérifiez que l'authentification 2FA est activée sur Gmail")
        print("  4. Vérifiez que le mot de passe d'application est correct")
        return False


def test_claim_submitted_email():
    """Tester l'email 'Réclamation soumise'."""
    print("\n📧 Test 2: Email 'Réclamation soumise'")
    print("-" * 60)
    
    test_email = input("Entrez votre email de test (ou appuyez sur Enter pour utiliser GMAIL_SENDER): ").strip()
    
    if not test_email:
        test_email = os.getenv('GMAIL_SENDER')
    
    print(f"📨 Envoi vers: {test_email}")
    
    result = send_claim_submitted_email(
        client_email=test_email,
        claim_reference='CLM-20260125-TEST',
        carrier='colissimo',
        amount_requested=150.00,
        order_id='ORD-TEST-001',
        submission_method='api'
    )
    
    if result:
        print("✅ Email envoyé avec succès !")
        print(f"📬 Vérifiez votre boîte mail: {test_email}")
        return True
    else:
        print("❌ Échec de l'envoi de l'email")
        return False


def main():
    """Point d'entrée principal."""
    print("=" * 60)
    print("🧪 TEST D'ENVOI D'EMAIL RÉEL - GMAIL")
    print("=" * 60)
    
    # Vérifier configuration
    if not check_configuration():
        print("\n⚠️  Configuration incomplète !")
        print("\n📖 Guide de configuration:")
        print("1. Allez sur https://myaccount.google.com/apppasswords")
        print("2. Créez un mot de passe d'application pour 'Mail'")
        print("3. Copiez le mot de passe (16 caractères)")
        print("4. Ajoutez dans .env:")
        print("   GMAIL_SENDER=votre.email@gmail.com")
        print("   GMAIL_APP_PASSWORD=abcd efgh ijkl mnop")
        print("\n")
        sys.exit(1)
    
    print("\n⚠️  ATTENTION: Ce script va envoyer de VRAIS emails !")
    confirm = input("Continuer ? (oui/non): ").strip().lower()
    
    if confirm not in ['oui', 'o', 'yes', 'y']:
        print("❌ Test annulé")
        sys.exit(0)
    
    # Test 1: Disputes détectés
    success1 = test_disputes_detected_email()
    
    if success1:
        print("\n" + "=" * 60)
        cont = input("\nTester un autre type d'email ? (oui/non): ").strip().lower()
        
        if cont in ['oui', 'o', 'yes', 'y']:
            # Test 2: Réclamation soumise
            success2 = test_claim_submitted_email()
            
            if success2:
                print("\n" + "=" * 60)
                print("🎉 Tous les tests ont réussi !")
                print("=" * 60)
        else:
            print("\n✅ Test terminé avec succès !")
    
    print("\n💡 Les emails sont maintenant configurés pour production !")
    print("   Les fonctions send_*_email() enverront de vrais emails.")


if __name__ == "__main__":
    main()
