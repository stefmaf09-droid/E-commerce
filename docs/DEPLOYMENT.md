# 🚀 Déploiement & Monitoring

## 1. Prérequis
- Python 3.11+
- Variables d’environnement (.env) correctement configurées
- SENTRY_DSN obligatoire en production

## 2. Lancer l’application
```bash
python main.py
```

## 3. Monitoring
- **Sentry** : Toutes les erreurs critiques sont remontées automatiquement.
- **Prometheus** : Les métriques sont exposées sur `/metrics`.
- **Logs** : Niveau INFO et ERROR, rotation automatique.

## 4. CI/CD
- Les tests de sécurité, performance et onboarding sont lancés automatiquement à chaque push.
- Utilisez `pip-audit` pour vérifier les dépendances.

## 5. Procédures d’urgence
- En cas d’erreur critique non remontée, vérifier la variable SENTRY_DSN et les logs système.

---

Pour toute question, contactez l’équipe DevOps.
