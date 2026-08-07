"""
Script pour créer un compte démo avec données variées.
Utilise les vrais modules d'authentification.
"""
import sys
import os

# Path setup
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(root_dir, 'src'))
sys.path.insert(0, root_dir)

from database.database_manager import DatabaseManager
from auth.credentials_manager import CredentialsManager
from auth.password_manager import set_client_password
from datetime import datetime, timedelta
import random

def create_demo_account():
    """Crée le compte démo@refundly.ai avec mot de passe."""
    print("🚀 Création du compte démo...")
    
    db = DatabaseManager()
    cm = CredentialsManager()
    
    email = "demo@refundly.ai"
    password = "Demo123!"
    
    # 1. Créer le client en base
    print("\n1. Création du client...")
    try:
        client_id = db.create_client(email, company_name="Refundly Demo SAS")
        print(f"✅ Client créé avec ID: {client_id}")
    except Exception as e:
        # Client existe peut-être déjà
        client = db.get_client(email=email)
        if client:
            client_id = client['id']
            print(f"✅ Client existe déjà avec ID: {client_id}")
        else:
            print(f"❌ Erreur: {e}")
            return None
    
    # 2. Définir le mot de passe
    print("\n2. Configuration du mot de passe...")
    try:
        set_client_password(email, password)
        print("✅ Mot de passe défini")
    except Exception as e:
        print(f"⚠️ Erreur mot de passe: {e}")
    
    # 3. Ajouter credentials Shopify
    print("\n3. Ajout du store Shopify...")
    try:
        cm.store_credentials(
            client_id=email,
            platform='shopify',
            credentials={
                'shop_url': 'demo-refundly.myshopify.com',
                'access_token': 'shpat_demo_token_1234567890',
                'store_name': 'Refundly Demo Store'
            }
        )
        print("✅ Store Shopify ajouté")
    except Exception as e:
        print(f"⚠️ Erreur store: {e}")
    
    # 4. Ajouter IBAN
    print("\n4. Ajout des informations bancaires...")
    try:
        conn = db.get_connection()
        conn.execute("""
            INSERT OR REPLACE INTO payment_info (client_id, iban, titulaire, bic)
            VALUES (?, ?, ?, ?)
        """, (client_id, "FR7612345678901234567890123", "Refundly Demo SAS", "BNPAFRPP"))
        conn.commit()
        conn.close()
        print("✅ IBAN ajouté")
    except Exception as e:
        print(f"⚠️ Erreur IBAN: {e}")
    
    return client_id


def create_demo_claims(client_id):
    """Crée des claims variés pour la démo."""
    print("\n5. Création de 15 claims variés...")
    
    db = DatabaseManager()
    carriers = ['Chronopost', 'UPS', 'DHL', 'FedEx', 'Colissimo', 'DPD']
    dispute_types = ['lost', 'damaged', 'late']
    statuses = ['submitted', 'accepted', 'rejected', 'under_review']
    
    for i in range(1, 16):
        base_date = datetime.now() - timedelta(days=random.randint(1, 90))
        
        claim_ref = f"CLM-DEMO-{i:03d}"
        carrier = random.choice(carriers)
        dispute_type = random.choice(dispute_types)
        amount = round(random.uniform(50, 500), 2)
        status = random.choice(statuses)
        payment_status = 'paid' if status == 'accepted' else 'unpaid'
        
        try:
            db.create_claim(
                client_id=client_id,
                claim_reference=claim_ref,
                order_id=f"ORD-{i:04d}",
                carrier=carrier,
                dispute_type=dispute_type,
                amount_requested=amount,
                currency='EUR',
                tracking_number=f"TRACK{random.randint(100000, 999999)}",
                customer_name=f"Client Demo {i}",
                delivery_address=f"{i} Rue de la Demo, 75001 Paris",
                submitted_at=base_date.isoformat()
            )
            
            # Mettre à jour le statut
            claim = db.get_claim(claim_reference=claim_ref)
            if claim:
                db.update_claim(
                    claim['id'],
                    status=status,
                    payment_status=payment_status,
                    accepted_amount=amount if status == 'accepted' else None
                )
            
            print(f"   ✅ Claim {claim_ref}: {carrier}, {status}, {amount}€")
        except Exception as e:
            print(f"   ⚠️ Erreur claim {claim_ref}: {e}")
    
    print("✅ 15 claims créés")


def create_escalations(client_id):
    """Crée quelques escalations pour la démo."""
    print("\n6. Création d'escalations...")
    
    db = DatabaseManager()
    from database.escalation_logger import EscalationLogger
    logger = EscalationLogger()
    
    # Récupérer claims et prendre les 5 premiers
    all_claims = db.get_client_claims(client_id)
    claims = all_claims[:5] if len(all_claims) >= 5 else all_claims
    
    for i, claim in enumerate(claims):
        try:
            level = (i % 3) + 1  # Niveaux 1, 2, 3
            action_types = ['status_request', 'warning', 'formal_notice']
            
            logger.log_escalation_action(
                claim_id=claim['id'],
                claim_reference=claim['claim_reference'],
                escalation_level=level,
                action_type=action_types[level-1],
                email_sent=True,
                email_to=f"{claim['carrier'].lower()}@transport.com",
                pdf_generated=True,
                notes=f"Escalation niveau {level} - {claim['claim_reference']}"
            )
            print(f"   ✅ Escalation niveau {level} pour {claim['claim_reference']}")
        except Exception as e:
            print(f"   ⚠️ Erreur escalation: {e}")
    
    print("✅ Escalations créées")


def main():
    """Script principal."""
    print("=" * 60)
    print("🎯 CRÉATION COMPTE DÉMO - Refundly.ai")
    print("=" * 60)
    
    client_id = create_demo_account()
    
    if client_id:
        create_demo_claims(client_id)
        create_escalations(client_id)
        
        print("\n" + "=" * 60)
        print("✨ TERMINÉ ! Compte démo prêt !")
        print("=" * 60)
        print("\n🔐 Credentials de connexion:")
        print("   Email:    demo@refundly.ai")
        print("   Password: Demo123!")
        print("\n🚀 Accédez au dashboard: http://localhost:8501")
        print("=" * 60)
    else:
        print("\n❌ Échec de la création du compte")


if __name__ == "__main__":
    main()
