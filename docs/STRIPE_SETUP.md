# 💳 Configuration Stripe Connect - Guide Complet

## 🎯 Vue d'ensemble

**Stripe Connect** permet de créer une marketplace où :

- Vous recevez les paiements des transporteurs (100€)
- Stripe reverse automatiquement la part client (80€)
- Vous gardez votre commission (20€)

---

## 📋 Étape 1 : Créer un Compte Stripe

### 1.1 Inscription

1. Allez sur : <https://dashboard.stripe.com/register>
2. Cliquez sur **"Créer un compte"**
3. Remplissez :
   - Email professionnel
   - Nom de l'entreprise : "Agent IA Recouvrement" (ou votre raison sociale)
   - Pays : France
   - Type de business : **Marketplace / Plateforme**

### 1.2 Vérification d'Identité

Vous devrez fournir :

- 📄 SIRET / SIREN
- 🏦 RIB (IBAN de votre compte pro)
- 🪪 Pièce d'identité du représentant légal
- 📍 Justificatif de domicile de l'entreprise

> [!NOTE]
> La vérification prend en général 1 à 3 jours ouvrés.

---

## 🔧 Étape 2 : Activer Stripe Connect

### 2.1 Activer le Mode Marketplace

1. Dans le **Dashboard Stripe** : <https://dashboard.stripe.com>
2. Allez dans **Settings** (Paramètres) → **Connect**
3. Cliquez sur **"Get started with Connect"**
4. Choisissez le type : **"Standard" ou "Express"**

Pour votre cas, choisissez l'option **Express** :

- Plus simple pour les clients
- Stripe gère l'onboarding
- Interface simplifiée

### 2.2 Configurer les Paramètres

**Settings → Connect → Settings** :

- ✅ **Enable OAuth** : OFF (pas besoin)
- ✅ **Express dashboard branding** : Personnalisez avec votre logo
- ✅ **Payout schedule** : Daily (paiements quotidiens aux clients)

---

## 🔑 Étape 3 : Obtenir les Clés API

### 3.1 Clés de Test (Développement)

1. Dans le Dashboard, activez le **Mode Test** (toggle en haut)
2. Allez dans **Developers → API keys**
3. Notez :
   - **Publishable key** : `pk_test_xxxxx`
   - **Secret key** : `sk_test_xxxxx`

### 3.2 Clés de Production

1. Basculez en **Mode Live** (production)
2. **Developers → API keys**
3. Notez :
   - **Publishable key** : `pk_live_xxxxx`
   - **Secret key** : `sk_live_xxxxx`

⚠️ **IMPORTANT** : Ne JAMAIS partager la Secret Key !

---

## 💰 Étape 4 : Configuration des Frais

### 4.1 Tarification Stripe

**Frais Stripe standard** :

- Transactions européennes : **1.4% + 0.25€**
- Transactions internationales : **2.9% + 0.25€**
- Virements vers comptes clients : **Gratuit** (SEPA)

**Pour 100€ de réclamation** :

- Vous recevez : 100€
- Frais Stripe : ~1.65€
- Vous reversez : 80€ au client (gratuit)
- Votre net : 20€ - 1.65€ = **18.35€**

### 4.2 Application Fee (Votre Commission)

Dans votre code, vous définirez :

```python
application_fee_amount = int(total_amount * 0.20 * 100)  # 20% en centimes
```

---

## 📱 Étape 5 : Onboarding des Clients

### 5.1 Flux d'Onboarding

Quand un client s'inscrit sur votre plateforme :

1. **Vous créez** un compte Stripe Connect pour lui
2. **Stripe génère** un lien d'onboarding
3. **Le client clique** sur le lien
4. **Il remplit** ses informations :
   - Nom/Prénom
   - IBAN (pour recevoir l'argent)
   - Pièce d'identité (KYC)
5. **Validation** par Stripe (quelques minutes)
6. **Le client peut recevoir** des paiements

### 5.2 KYC (Know Your Customer)

**Documents requis pour les clients** :

- Pièce d'identité (CNI, Passeport)
- IBAN du compte bancaire

**Seuils KYC en France** :

- Jusqu'à 1000€ cumulés : Pas de vérification stricte
- Au-delà : Documents obligatoires

---

## 🔐 Étape 6 : Configuration des Variables d'Environnement

### 6.1 Fichier `.env`

Ajoutez ces lignes dans votre `.env` :

```env
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_xxxxx  # Mode test au début
STRIPE_PUBLISHABLE_KEY=pk_test_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx  # Pour la production

# Commission (en pourcentage)
PLATFORM_COMMISSION_RATE=0.20  # 20%
```

### 6.2 Mode Test vs Production

**Développement** :

```env
STRIPE_SECRET_KEY=sk_test_xxxxx
STRIPE_MODE=test
```

**Production** (quand prêt) :

```env
STRIPE_SECRET_KEY=sk_live_xxxxx
STRIPE_MODE=live
```

---

## 🎯 Étape 7 : Webhooks (Important !)

### 7.1 Créer un Webhook Endpoint

Les webhooks vous notifient quand :

- Un paiement est reçu
- Un virement est effectué
- Un compte client est validé

**Setup** :

1. **Dashboard → Developers → Webhooks**
2. **Add endpoint** → URL de votre serveur : `https://votre-domaine.com/webhook/stripe`
3. **Sélectionnez les événements** :
   - `transfer.created`
   - `payout.paid`
   - `account.updated`
   - `charge.succeeded`

4. Copiez le **Webhook signing secret** : `whsec_xxxxx`

---

## 📦 Étape 8 : Installation de la Librairie

```bash
pip install stripe
```

Ajoutez dans `requirements.txt` :

```text
stripe>=5.0.0
```

---

## 🧪 Étape 9 : Mode Test

### 9.1 Tester avec des Cartes Fictives

**Carte de test Stripe** :

- Numéro : `4242 4242 4242 4242`
- Date : N'importe quelle date future
- CVC : N'importe quel 3 chiffres

### 9.2 Simuler des Payouts

En mode test, vous pouvez simuler :

- Paiements instantanés
- Virements bancaires
- Erreurs de paiement

---

## 💡 Résumé des Coûts

### Exemple : Réclamation de 100€ acceptée

```text
Transporteur paie : 100.00€
─────────────────────────────
Frais Stripe (1.4% + 0.25€) : -1.65€
Votre brut : 98.35€

Part client (80%) : -80.00€
Virement Stripe → Client : Gratuit
─────────────────────────────
VOTRE NET : 18.35€ (au lieu de 20€)
```

**Rentabilité** : ~92% de votre commission (le reste = frais)

---

## 📞 Support Stripe

- 🌐 Documentation : <https://stripe.com/docs/connect>
- 💬 Support : <support@stripe.com>
- 📚 Guide Connect : <https://stripe.com/docs/connect/enable-payment-acceptance-guide>

---

## ✅ Checklist Finale

Avant de passer en production :

- [ ] Compte Stripe créé et vérifié
- [ ] Stripe Connect activé (mode Express)
- [ ] Clés API récupérées (test + live)
- [ ] Variables d'environnement configurées
- [ ] Webhooks configurés
- [ ] Tests effectués en mode test
- [ ] KYC complété pour votre entreprise
- [ ] Compte bancaire vérifié
- [ ] Logo et branding configurés

---

## 🎉 Vous êtes Prêt

Une fois tout configuré, le module `payment_processor.py` s'occupera de tout automatiquement ! 🚀
