# ROADMAP & Backlog

Ce document priorise les améliorations fonctionnelles recommandées et propose une estimation rapide (T-shirt sizing) et critères d'acceptation.

## Priorité haute (à planifier en next sprint) ✅

1. E2E Playwright — Onboarding (signup -> redirect -> first-login)
   - Estimation: Small (1-2 days)
   - Labels: e2e, ci, high-priority
   - Critères d'acceptation:
     - Test simule création d'un compte, suit le magic link / auto-login, vérifie redirection vers le dashboard client et présence d'un message de bienvenue.
     - Test passe en CI sur push vers `main`/PR.

2. CI job — Playwright E2E
   - Estimation: Small (1 day)
   - Labels: ci, e2e
   - Critères d'acceptation:
     - Job GitHub Actions exécute Playwright tests en mode headless (matrix: smoke/slow)
     - Tests critiques (onboarding) marquent la PR en échec si échouent.

3. Retrys & Idempotence — Shopify connector
   - Estimation: Medium (3-7 days)
   - Labels: integrations, reliability
   - Critères d'acceptation:
     - Appel externe enveloppé avec retry exponentiel et jitter.
     - Requests idempotentes (idempotency-key) pour éviter doublons.
     - Tests unitaires et d’intégration simulant erreurs transitoires.

4. Audit & logging — actions sensibles
   - Estimation: Small (2-3 days)
   - Labels: observability, compliance
   - Critères d'acceptation:
     - Implémentation d'un `src/logging/audit.py` pour events structuré.
     - Evènements émis: user_created, user_login, stripe_activation, ticket_fallback_created.
     - Logs format JSON et exemples ajoutés à la doc.

## Priorité moyenne
- Automatisation tickets fallback (create/assign after 3 continuous failures) — Medium (1-2 weeks)
- E2E complet CSV → détection → récupération — Medium (2-3 weeks)
- Monitoring & SLOs (Prometheus/Grafana) — Medium (2-4 weeks)

## Priorité basse / long terme
- RBAC & roles avancés — Large (3-6 weeks)
- Feature flags & canary releases — Medium/Large (2-4 weeks)
- GDPR flows & automated data deletion — Medium (2-4 weeks)

---

## Prochaine étape proposée
- Créer des tickets GitHub pour les éléments en **Priorité haute** et assigner un cycle court (sprint) pour les terminer.
- Commencer par l'item 1 (E2E Playwright) et l'item 2 (CI job) simultanément.
