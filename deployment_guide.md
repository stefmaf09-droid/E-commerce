# Guide de Déploiement : Refundly.ai 🚀

Ce guide vous accompagne pas à pas pour mettre votre application en ligne de manière sécurisée et professionnelle.

## 1. Préparation de Supabase

Supabase remplace votre base de données locale par une base PostgreSQL performante dans le cloud.

1. **Créer un projet** : Allez sur [supabase.com](https://supabase.com), créez un compte et un nouveau projet.
2. **Initialiser la base** :
    - Allez dans l'onglet **SQL Editor**.
    - Copiez-collez le contenu de votre fichier local [schema_postgres.sql](file:///d:/Recours_Ecommerce/database/schema_postgres.sql).
    - Cliquez sur **Run**. Vos tables sont prêtes !
3. **Configurer le Stockage** :
    - Allez dans l'onglet **Storage**.
    - Créez un nouveau bucket nommé `evidence`.
    - Choisissez **Public** (pour la démo) ou configurez des politiques d'accès (RLS) pour la sécurité.
4. **Récupérer les Clés** :
    - Allez dans **Project Settings** > **API**.
    - Notez votre `Project URL`, votre `anon public key` et surtout votre `service_role secret key`.

---

## 2. Mise à jour sur GitHub

Toutes les modifications doivent être sur votre dépôt distant pour que Streamlit Cloud puisse les lire.

```bash
git add .
git commit -m "feat: mise a jour config"
git push origin main
```

---

## 3. Lancement sur Streamlit Cloud

1. Connectez-vous sur [share.streamlit.io](https://share.streamlit.io).
2. Cliquez sur **New app**.
3. **Repository** : Choisissez votre dépôt.
4. **Main file path** : `client_dashboard_main_new.py`.
5. **Secrets (CRUCIAL)** :
    - Allez dans **Advanced settings...** > **Secrets**.
    - Copiez et configurez les variables suivantes :

```toml
# Configuration Base de Données
DATABASE_TYPE = "postgres"
DATABASE_URL = "votre_url_de_connexion_postgres_supabase"

# Configuration Supabase Cloud
SUPABASE_URL = "https://votre-projet.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "votre_clé_service_role"
SUPABASE_STORAGE_BUCKET = "evidence"

# Autres configurations (Stripe, OpenAI, SMTP)
OPENAI_API_KEY = "votre_clé"
SMTP_PASSWORD = "votre_mot_de_passe_app_gmail"
# ... etc
```

---

## 4. Vérification Finale

Une fois l'application déployée :

1. Connectez-vous à votre dashboard en ligne.
2. Uploadez une preuve.
3. Vérifiez dans votre console Supabase Storage que le fichier apparaît bien dans le bucket `evidence`.

> [!IMPORTANT]
> Ne partagez jamais votre clé `service_role` ou votre `DATABASE_URL` publiquement. Streamlit Secrets s'occupe de les garder privées.
