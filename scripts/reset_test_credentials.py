"""
scripts/reset_test_credentials.py

Audit du 26/08/2026 : vide les tables `credentials` et `sync_status` (données
de test chiffrées avec l'ancienne clé config/.secret_key, qui a été exposée
publiquement sur GitHub) AVANT de faire tourner l'app avec une clé neuve.

Sans ce nettoyage, les anciennes lignes deviendraient illisibles (erreur de
déchiffrement) une fois la clé changée, et pourraient faire planter
"Réglages -> Vos boutiques connectées" (get_all_stores() abandonne toute la
liste si une seule ligne ne se déchiffre pas).

Usage :
    python scripts/reset_test_credentials.py             # demande confirmation
    python scripts/reset_test_credentials.py --dry-run    # affiche juste les comptes, ne supprime rien

Étapes complètes de la rotation (voir la conversation) :
    1. Arrêter l'app Streamlit (Ctrl+C).
    2. python scripts/reset_test_credentials.py
    3. Supprimer config/.secret_key (une nouvelle clé propre sera générée
       automatiquement au prochain lancement de l'app).
    4. Relancer l'app, vérifier que "Réglages" est vide et sans erreur.
    5. Nettoyer l'historique Git (git-filter-repo) pour retirer l'ancienne
       clé de tous les commits passés, puis push --force.
"""
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.database_manager import get_db_manager


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Afficher seulement les comptes de lignes concernées, ne rien supprimer.",
    )
    args = parser.parse_args()

    db = get_db_manager()
    conn = db.get_connection()
    try:
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM credentials")
        n_creds = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM sync_status")
        n_sync = cur.fetchone()[0]

        print(f"Base active : {db.db_type}")
        print(f"  - table 'credentials'  : {n_creds} ligne(s)")
        print(f"  - table 'sync_status'  : {n_sync} ligne(s)")

        if args.dry_run:
            print("\n--dry-run : rien n'a été supprimé.")
            return

        if n_creds == 0 and n_sync == 0:
            print("\nRien à nettoyer.")
            return

        confirm = input(
            f"\nSupprimer définitivement ces {n_creds + n_sync} ligne(s) ? [oui/N] "
        )
        if confirm.strip().lower() not in ("oui", "o", "yes", "y"):
            print("Annulé — rien n'a été supprimé.")
            return

        cur.execute("DELETE FROM sync_status")
        cur.execute("DELETE FROM credentials")
        conn.commit()

        print("\n✅ Tables 'credentials' et 'sync_status' vidées.")
        print("Étape suivante : supprimez config/.secret_key puis relancez l'app")
        print("pour générer automatiquement une nouvelle clé de chiffrement propre.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
