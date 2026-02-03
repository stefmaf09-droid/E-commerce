# 💳 Système de Paiement Stripe Connect - Notes pour Activation

## ✅ Ce qui a été créé

### 📁 Fichiers créés

1. **`docs/STRIPE_SETUP.md`** - Guide complet de configuration Stripe
2. **`src/payments/payment_processor.py`** - Module de traitement des paiements
3. **`.env.example`** - Variables d'environnement mises à jour

### 📦 Dépendances ajoutées

Dans `requirements.txt` :

```text
stripe>=5.0.0
python-dotenv>=1.0.0
bcrypt>=4.0.0  (déjà installé)
```

---

## 🎯 Quand vous serez prêt à activer

### Étape 1 : Créer compte Stripe

1. Allez sur : **<https://dashboard.stripe.com/register>**
2. Type de compte : **Marketplace / Plateforme**
3. Activez **Stripe Connect** (mode Express)
4. Complétez la vérification KYC (SIRET, RIB, pièce d'identité)

### Étape 2 : Récupérer les clés API

1. Testez d'abord en **mode Test** :
   - Dashboard → **Developers → API keys**
   - Copiez `sk_test_xxxxx` et `pk_test_xxxxx`

2. Quand prêt pour production :
   - Basculez en mode **Live**
   - Copiez `sk_live_xxxxx` et `pk_live_xxxxx`

### Étape 3 : Configurer `.env`

Créez un fichier `.env` à la racine :

```env
STRIPE_SECRET_KEY=sk_test_xxxxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxxxx
STRIPE_MODE=test
PLATFORM_COMMISSION_RATE=0.20
```

### Étape 4 : Installer les dépendances

```bash
pip install stripe python-dotenv
```

### Étape 5 : Tester

```bash
python src/payments/payment_processor.py
```

Vous devriez voir :

```text
💳 Configuration:
  Stripe API Key: ✅ Configured
  Mode: test
  Commission Rate: 20.0%
```

---

## 💰 Comment ça marchera

### Scénario : Réclamation de 100€ acceptée

```text
1. Transporteur vous paie 100€ (virement bancaire)
2. Vous déclenchez le paiement dans le système
3. Stripe reverse automatiquement 80€ au client
4. Vous gardez 20€ - 1.65€ (frais Stripe) = 18.35€ net
```

### Fonctions disponibles

```python
from payments.payment_processor import create_client_account, pay_client

# 1. À l'inscription du client
result = create_client_account("client@email.com")
# → Retourne un lien d'onboarding Stripe pour le client

# 2. Quand vous recevez 100€ du transporteur
result = pay_client(
    amount=100.0,
    client_stripe_id="acct_xxxxx",
    claim_reference="CLM-xxx"
)
# → Transfert automatique de 80€ au client
```

---

## 🎯 Tarification

**Frais Stripe** :

- 1.4% + 0.25€ par transaction EU
- Virements SEPA : Gratuit
- Pas d'abonnement mensuel

**Exemple** :

```text
Réclamation : 100.00€
Frais Stripe : -1.65€
Part client (80%) : -80.00€
──────────────────
Votre net : 18.35€
```

**Rentabilité** : ~92% de votre commission conservée

---

## 📞 Support

- **Documentation complète** : `docs/STRIPE_SETUP.md`
- **Support Stripe** : <support@stripe.com>
- **Docs API** : <https://stripe.com/docs/connect>

---

## ⏰ À faire plus tard

**Quand vous aurez du temps** :

1. [ ] Créer compte Stripe
2. [ ] Activer Stripe Connect
3. [ ] Récupérer clés API test
4. [ ] Configurer `.env`
5. [ ] Installer stripe (`pip install stripe`)
6. [ ] Tester avec cartes de test
7. [ ] Passer en production quand prêt

**Pas d'urgence** - Le système fonctionnera en mode manuel jusqu'à l'activation.

---

✅ **Tout est prêt côté code, il ne reste qu'à configurer Stripe quand vous voulez !**
