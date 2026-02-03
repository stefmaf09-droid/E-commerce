
import os
import sys
from datetime import datetime, timedelta
import logging

# Configuration du logging pour voir les actions du FollowUpManager
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Ajout du dossier racine au path pour les imports
sys.path.append(os.getcwd())

from src.database.database_manager import DatabaseManager
from src.automation.follow_up_manager import FollowUpManager
from src.utils.i18n import format_currency

def run_simulation():
    db_path = "database/simulation_complete.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # S'assurer que le schéma est copié pour le DatabaseManager
    import shutil
    if not os.path.exists("database/schema.sql"):
        # Si on est dans un sous-dossier, adapter le path (normalement on est à la racine)
        pass 

    print("=== 🚀 DÉBUT DE LA SIMULATION COMPLÈTE ===")
    db = DatabaseManager(db_path=db_path)
    manager = FollowUpManager(db)
    
    # 1. Création Client et Boutiques
    client_id = db.create_client("simu_pro@example.com", full_name="Expert E-commerce", company_name="Global Trade SAS")
    
    # Boutique FR
    conn = db.get_connection()
    conn.execute("INSERT INTO stores (client_id, platform, store_name, country, currency) VALUES (?, ?, ?, ?, ?)",
                 (client_id, "shopify", "Ma Boutique FR", "FR", "EUR"))
    store_fr_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    
    # Boutique US
    conn.execute("INSERT INTO stores (client_id, platform, store_name, country, currency) VALUES (?, ?, ?, ?, ?)",
                 (client_id, "woocommerce", "My US Store", "US", "USD"))
    store_us_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    conn.close()

    print(f"✅ Client et Boutiques (FR & US) créés.")

    # 2. Préparation des Réclamations (Multi-cas)
    now = datetime.now()
    
    scenarios = [
        {
            "ref": "CLM-FR-J25",
            "store_id": store_fr_id,
            "days_ago": 25,
            "amount": 150.0,
            "currency": "EUR",
            "type": "Colis Perdu",
            "tracking": "FR-123-LOST",
            "desc": "Cas FR : Doit déclencher une MISE EN DEMEURE (J+21)"
        },
        {
            "ref": "CLM-US-J22",
            "store_id": store_us_id,
            "days_ago": 22,
            "amount": 89.90,
            "currency": "USD",
            "type": "Damaged",
            "tracking": "US-999-DAM",
            "desc": "Cas US : Doit déclencher une FORMAL NOTICE en EN (J+21)"
        },
        {
            "ref": "CLM-FR-J10",
            "store_id": store_fr_id,
            "days_ago": 10,
            "amount": 45.0,
            "currency": "EUR",
            "type": "Retard",
            "tracking": "FR-456-LATE",
            "desc": "Cas FR : Doit déclencher une RELANCE SIMPLE (J+7)"
        },
        {
            "ref": "CLM-BYPASS",
            "store_id": store_fr_id,
            "days_ago": 5,
            "amount": 200.0,
            "currency": "EUR",
            "type": "Perte",
            "tracking": "TRACK-BYPASS-PRO",
            "desc": "Cas BYPASS : Doit générer une ALERTE ADMIN (Mock API = Compensated)"
        }
    ]

    for s in scenarios:
        submitted_at = (now - timedelta(days=s['days_ago'])).isoformat()
        claim_id = db.create_claim(
            claim_reference=s['ref'],
            client_id=client_id,
            order_id=f"ORD-{s['ref']}",
            carrier="Colissimo" if "FR" in s['ref'] else "UPS",
            dispute_type=s['type'],
            amount_requested=s['amount'],
            store_id=s['store_id'],
            currency=s['currency'],
            tracking_number=s['tracking'],
            customer_name="John Doe"
        )
        # On injecte manuellement le statut et la date de soumission pour simuler le passé
        conn = db.get_connection()
        conn.execute("UPDATE claims SET status = 'submitted', submitted_at = ? WHERE id = ?", (submitted_at, claim_id))
        conn.commit()
        conn.close()
        print(f"📩 Réclamation {s['ref']} créée ({s['desc']})")

    # 3. Exécution du Suivi (Escalade)
    print("\n--- ⚖️ EXÉCUTION DU FOLLOW-UP MANAGER ---")
    stats = manager.process_follow_ups()
    print(f"Stats d'escalade : {stats}")

    # 4. Exécution de la Détection Anti-Bypass
    print("\n--- 🛡️ EXÉCUTION DE LA DÉTECTION BYPASS ---")
    alerts = manager.detect_potential_bypass()
    print(f"Alertes de contournement détectées : {alerts}")

    # 5. Vérification des résultats
    print("\n--- 📊 VÉRIFICATION FINALE ---")
    conn = db.get_connection()
    
    # Vérifier les dossiers mis en demeure
    print("\n[Dossiers Niveau 3 - Mise en Demeure]")
    rows = conn.execute("SELECT claim_reference, follow_up_level, currency FROM claims WHERE follow_up_level = 3").fetchall()
    for row in rows:
        print(f"  - {row[0]} : Niveau {row[1]} ({row[2]})")
        
    # Vérifier l'alerte Bypass
    print("\n[Alertes Système]")
    alerts_rows = conn.execute("SELECT alert_type, severity, message FROM system_alerts").fetchall()
    for alert in alerts_rows:
        print(f"  - [{alert[0].upper()}] {alert[1]} : {alert[2]}")
        
    # Vérifier les PDFs générés
    print("\n[Fichiers PDF générés dans data/legal_docs]")
    if os.path.exists("data/legal_docs"):
        files = os.listdir("data/legal_docs")
        for f in files:
            if f.endswith(".pdf"):
                print(f"  - {f}")
    else:
        print("  - Aucun PDF trouvé.")

    conn.close()
    print("\n=== ✨ SIMULATION TERMINÉE AVEC SUCCÈS ===")

if __name__ == "__main__":
    run_simulation()
