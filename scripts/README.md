# scripts/ — index

Généré le 26/08/2026 dans le cadre de l'audit du projet. Ce dossier contient
~80 scripts autonomes (lancés à la main via `python scripts/<nom>.py`, pas
importés par l'application) accumulés au fil du développement. Ils ne sont
**pas** tous encore pertinents — certains sont des migrations déjà exécutées,
d'autres des scripts de debug ponctuels. Cet index les regroupe par usage
pour qu'un futur développeur (ou vous, dans 6 mois) puisse s'y retrouver
sans avoir à ouvrir chaque fichier. Les descriptions sont dérivées du nom de
fichier — à corriger/préciser au fur et à mesure si un nom prête à confusion.

## Migrations de base de données (SQLite → Postgres, ou évolutions de schéma)

Scripts de migration : normalement à exécuter **une seule fois** par
environnement, avec `--dry-run` avant l'exécution réelle (voir les deux
scripts les plus récents pour le pattern à suivre — idempotents, lecture
seule côté source).

- `migrate_passwords_credentials_to_postgres.py` — mots de passe/identifiants stockés → Postgres.
- `migrate_manual_payments_to_postgres.py` — IBAN clients + paiements manuels → Postgres.
- `migrate_sqlite_to_postgres.py` — migration générale (probablement plus ancienne/générique que les deux ci-dessus).
- `migrate_to_supabase.py` — migration spécifique Supabase.
- `migrate_existing_users.py` — migration ponctuelle d'utilisateurs existants.
- `migrate_add_pod_columns.py` / `add_notification_prefs_column.py` — ajouts de colonnes ponctuels (ALTER TABLE).
- `ensure_db_schema.py` / `prepare_db.py` / `run_migration.py` — préparation/bootstrap de schéma.
- `init_supabase.py` / `populate_neon_db.py` — initialisation de bases cloud spécifiques.

## Données de démonstration / comptes de test

- `create_demo_account.py`, `create_test_account.py`, `create_demo_disputes.py`,
  `create_demo_sqlite.py`, `create_backmarket_demo.py`, `create_chatbot_demo_data.py`,
  `create_pod_test_data.py`, `setup_demo_data.py`, `insert_test_claims.py`,
  `insert_test_claims_neon.py` — génèrent des données factices pour démos/tests manuels.
- `reset_demo_password.py`, `setup_default_passwords.py` — (ré)initialisent des mots de passe de démo.

## Vérification / diagnostic (lecture seule, sans danger à relancer)

- `check_db_connection.py`, `check_db_users.py`, `check_deadlines_cron.py`, `check_order.py`
- `verify_ocr_setup.py`, `verify_postgres.py`
- `diag_streamlit.py`, `dump_settings.py`
- `debug_bot.py`, `debug_google_import.py`, `debug_google_import_v2.py`, `debug_pdf.py`

## Simulations de bout en bout (pour tester un parcours complet sans vrai client)

- `simulate_full_client_journey.py` — parcours client complet (le plus utilisé cette session).
- `simulate_carrier_email.py`, `simulate_image_upload.py`, `simulate_rejection_email.py`

## Scripts `test_*` (manuels, hors suite pytest)

⚠️ À ne pas confondre avec `tests/test_*.py` (la vraie suite pytest, lancée en CI).
Ceux-ci sont des scripts d'exploration manuelle, lancés ponctuellement pendant le développement :
`test_ai_sync.py`, `test_assistant_tracking.py`, `test_client_submission_journey.py`,
`test_email_sending.py`, `test_email_sync_mock.py`, `test_new_templates.py`,
`test_orange_mail.py`, `test_playwright_tracking.py`, `test_supabase.py`,
`test_urls.py`, `test_urls2.py`.
Si certains sont devenus redondants avec la vraie suite `tests/`, ils sont
candidats à suppression — à vérifier au cas par cas.

## Automatisation GitHub (CI/PR)

- `comment_pr.py`, `comment_pr_ci.py`, `comment_pr_e2e.py`, `comment_pr_on_vulns.py`, `comment_pr_pipwork.py`
- `create_issues.py`, `create_pr.py`, `label_pr.py`, `request_reviewers.py`
- `get_repo.py`, `list_branches.py`

## Tâches planifiées (cron) et workers ponctuels

- `check_deadlines_cron.py`, `scan_disputes_cron.py`, `weekly_reports_cron.py`
- `pod_fetch_worker.py`, `pod_retry_scheduler.py`
- `manual_sync.py`, `purge_email_queue.py`

## Administration

- `admin_dashboard.py`, `delete_client.py`, `promote_admin.py`, `fix_prod_db.py`

## Divers

- `live_tracking_analysis.py`, `mass_scrape_trustpilot.py`, `performance_report_generator.py`,
  `list_gemini_models.py`, `pre-commit-audit.py`

---

**Recommandation** : au prochain nettoyage, passer en revue les scripts
`create_demo_*` / `test_*` / `debug_*` les plus anciens (voir dates de
modification) et supprimer ceux qui ne sont plus utilisés — ce fichier
facilite la décision mais ne la prend pas à votre place.
