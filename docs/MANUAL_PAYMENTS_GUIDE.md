# 💰 Gestion Manuelle des Paiements - Guide Pratique

## 📋 Processus Complet

### Étape 1 : Réclamation Acceptée par le Transporteur

Quand un transporteur accepte une réclamation et vous paie 100€ :

1. **Notez** :
   - Référence de la réclamation : `CLM-xxx`
   - Montant reçu : 100€
   - Email du client
   - Date de réception

### Étape 2 : Enregistrer le Paiement Reçu

Dans votre dashboard (à venir) ou manuellement :

```python
from payments.manual_payment_manager import create_pending_payment

create_pending_payment(
    claim_reference="CLM-20260122-XXX",
    client_email="client@example.com",
    total_amount=100.0  # Montant reçu du transporteur
)
```

**Cela crée automatiquement** :

- Client à payer : 80€ (80%)
- Votre commission : 20€ (20%)
- Statut : "pending"

### Étape 3 : Récupérer l'IBAN du Client

**Option A - Le client le fournit** :

```python
from payments.manual_payment_manager import add_bank_info

add_bank_info(
    client_email="client@example.com",
    iban="FR76 3000 6000 0112 3456 7890 189",
    bic="BNPAFRPP",  # Optionnel
    account_holder_name="Jean Dupont",
    bank_name="BNP Paribas"  # Optionnel
)
```

**Option B - Demandez par email** :

"Bonjour, pour procéder au virement de vos 80€, merci de nous communiquer votre IBAN."

### Étape 4 : Effectuer le Virement

**Via votre banque en ligne** :

1. **Connectez-vous** à votre banque pro
2. **Nouveau virement** :
   - Bénéficiaire : Nom du client
   - IBAN : (celui fourni)
   - Montant : 80.00€
   - Motif : "Réclamation CLM-xxx acceptée"
3. **Validez** le virement
4. **Notez** la référence de transaction

### Étape 5 : Marquer comme Payé

```python
from payments.manual_payment_manager import mark_as_paid

mark_as_paid(
    claim_reference="CLM-20260122-XXX",
    payment_method="Virement bancaire",
    transaction_reference="VIR-2026-001",
    notes="Virement effectué via BNP Paribas"
)
```

---

## 📊 Suivi des Paiements

### Voir les paiements en attente

```python
from payments.manual_payment_manager import ManualPaymentManager

manager = ManualPaymentManager()
pending = manager.get_pending_payments()

for payment in pending:
    print(f"À payer : {payment['client_share']}€")
    print(f"Client : {payment['client_email']}")
    print(f"IBAN : {payment['iban'] or 'Non fourni'}")
    print(f"Réclamation : {payment['claim_reference']}")
    print("---")
```

### Historique des paiements

```python
history = manager.get_payment_history(limit=50)

for payment in history:
    print(f"{payment['payment_date']} - {payment['client_share']}€ - {payment['payment_status']}")
```

---

## 🎯 Exemple Complet

### Scénario : Colissimo vous paie 100€

#### 1. Réception des fonds

Vous recevez 100€ de Colissimo (virement ou chèque).

#### 2. Enregistrement dans le système

Enregistrez le paiement reçu :

```python
create_pending_payment(
    claim_reference="CLM-20260122193217-KLBC",
    client_email="success.test@example.com",
    total_amount=100.0
)
```

→ Système calcule : Client = 80€, Vous = 20€

#### 3. Récupération de l'IBAN

Récupérez l'IBAN du client :

- Email automatique au client (si activé)
- Ou demande manuelle

#### 4. Ajout des informations bancaires

Le client vous envoie son IBAN :

```python
add_bank_info(
    client_email="success.test@example.com",
    iban="FR76 3000 6000 0112 3456 7890 189",
    account_holder_name="Test User"
)
```

#### 5. Virement au client

Faites le virement de 80€ depuis votre banque.

#### 6. Validation finale

Marquez comme payé :

```python
mark_as_paid(
    claim_reference="CLM-20260122193217-KLBC",
    transaction_reference="VIR20260122001"
)
```

**7. Vous gardez 20€** ✅

---

## 📁 Fichiers Créés

Le système crée automatiquement :

```text
database/
└── manual_payments.db
    ├── client_bank_info (IBAN des clients)
    └── manual_payments (historique paiements)
```

---

## 📝 Template Email pour Demander IBAN

```text
Objet : Votre réclamation acceptée - Paiement de 80€

Bonjour,

Excellente nouvelle ! Votre réclamation CLM-xxx a été acceptée 
par le transporteur.

Montant récupéré : 100€
Votre part (80%) : 80€
Frais de gestion (20%) : 20€

Pour recevoir votre paiement de 80€, merci de nous communiquer :

- Votre IBAN : 
- Titulaire du compte :
- Banque (optionnel) :

Nous effectuerons le virement sous 3-5 jours ouvrés.

Cordialement,
L'équipe Agent IA
```

---

## 💡 Conseils

### Délais

- **Virement SEPA** : 1-2 jours ouvrés
- **Chèque** : 5-7 jours

### Coûts

- **Virement SEPA national** : Gratuit (la plupart des banques pro)
- **Virement SEPA UE** : ~0.20€ - 0.50€

### Tracking

- Notez toujours la référence de transaction
- Conservez les preuves de virement (justificatifs bancaires)
- Archivez les emails de confirmation

### Sécurité

- Vérifiez l'IBAN avec un validateur en ligne
- Confirmez par email avant le virement
- Ne jamais envoyer vers un IBAN non vérifié

---

## 🔄 Transition vers Stripe

Quand vous activerez Stripe Connect :

- Tous ces virements deviendront **automatiques**
- Plus besoin de demander les IBAN
- Paiements en 1-2 jours automatiquement
- Ce système manuel restera pour l'historique

---

## ✅ Checklist par Réclamation

- [ ] Réclamation acceptée par transporteur
- [ ] Argent reçu sur votre compte
- [ ] Paiement enregistré dans le système
- [ ] IBAN client récupéré
- [ ] Virement effectué
- [ ] Référence transaction notée
- [ ] Paiement marqué comme "paid"
- [ ] Client notifié
