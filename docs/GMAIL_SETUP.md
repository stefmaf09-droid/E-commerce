# 📧 Guide de Configuration Gmail pour Emails Réels

## 🎯 Objectif

Envoyer de VRAIS emails en production avec Gmail au lieu d'utiliser les mocks de test.

---

## 📝 Étape 1: Créer un Mot de Passe d'Application Gmail

### 1.1 Activer l'Authentification à 2 Facteurs

1. Allez sur <https://myaccount.google.com>
2. Cliquez sur **Sécurité** dans le menu de gauche
3. Trouvez **Validation en deux étapes**
4. **Activez-la** si ce n'est pas déjà fait

> ⚠️ **Important:** Les mots de passe d'application nécessitent la 2FA activée.

### 1.2 Générer un Mot de Passe d'Application

1. Allez sur <https://myaccount.google.com/apppasswords>
2. Dans "Sélectionner l'application", choisissez **Mail**
3. Dans "Sélectionner l'appareil", choisissez **Autre (nom personnalisé)**
4. Entrez: **Recours Ecommerce**
5. Cliquez sur **Générer**
6. **⚠️ COPIEZ LE MOT DE PASSE** (16 caractères comme `abcd efgh ijkl mnop`)
7. Vous ne pourrez plus le revoir !

---

## 🔧 Étape 2: Configurer le Fichier .env

Éditez votre fichier `.env` à la racine du projet:

```bash
# Email Configuration - GMAIL (PRODUCTION)
GMAIL_SENDER=votre.email@gmail.com
GMAIL_APP_PASSWORD=abcd efgh ijkl mnop
```

**Remplacez par:**

- `votre.email@gmail.com` → Votre adresse Gmail
- `abcd efgh ijkl mnop` → Le mot de passe d'app que vous avez copié

**Exemple réel:**

```bash
GMAIL_SENDER=contact@mon-ecommerce.com
GMAIL_APP_PASSWORD=xmqp ytkr wvsd phql
```

---

## 🧪 Étape 3: Tester l'Envoi d'Email

### 3.1 Installer les dépendances

```bash
pip install python-dotenv
```

### 3.2 Lancer le test

```bash
python test_real_email.py
```

### 3.3 Ce que le script fait

1. ✅ Vérifie que `GMAIL_SENDER` et `GMAIL_APP_PASSWORD` sont configurés
2. ✅ Vous demande l'email de destination (ou utilise `GMAIL_SENDER`)
3. ✅ Envoie un email de test "Nouveaux litiges détectés"
4. ✅ Optionnel: Envoie un email "Réclamation soumise"
5. ✅ Affiche le résultat

### 3.4 Exemple d'exécution

```text
🔍 Vérification de la configuration...
------------------------------------------------------------
✅ GMAIL_SENDER: contact@mon-ecommerce.com
✅ GMAIL_APP_PASSWORD: **************** (masqué)
------------------------------------------------------------

⚠️  ATTENTION: Ce script va envoyer de VRAIS emails !
Continuer ? (oui/non): oui

📧 Test 1: Email 'Nouveaux litiges détectés'
------------------------------------------------------------
Entrez votre email de test (ou appuyez sur Enter pour utiliser GMAIL_SENDER): 
📨 Envoi vers: contact@mon-ecommerce.com
✅ Email envoyé avec succès !
📬 Vérifiez votre boîte mail: contact@mon-ecommerce.com
```

---

## ✅ Étape 4: Vérification

1. **Ouvrez votre boîte mail** (celle que vous avez indiquée)
2. **Cherchez l'email** avec le sujet: "🚨 3 nouveaux litiges détectés - 450€ récupérables"
3. **Vérifiez le contenu:**
   - Template HTML professionnel ✅
   - Montant total affiché ✅
   - Liste des litiges ✅
   - Bouton "Voir Mon Dashboard" ✅

### Si vous ne recevez pas l'email

1. **Vérifiez les Spams** - Gmail peut filtrer
2. **Vérifiez le mot de passe d'app** - Copiez-le exactement (avec espaces)
3. **Vérifiez GMAIL_SENDER** - Doit être l'email exact du compte
4. **Réessayez** avec `python test_real_email.py`

---

## 🚀 Étape 5: Utiliser en Production

Une fois les tests réussis, **aucune modification de code n'est nécessaire** !

### Le code est déjà prêt

```python
# Dans order_sync_worker.py (DÉJÀ IMPLÉMENTÉ)
from email_service import send_disputes_detected_email

# Envoie automatiquement un VRAI email si credentials configurés
send_disputes_detected_email(
    client_email=client_id,
    disputes_count=new_disputes_count,
    total_amount=total_recoverable,
    disputes_summary=disputed_orders
)
```

### Comment ça marche ?

Les helper functions lisent automatiquement les variables d'environnement:

```python
# Dans email_sender.py
sender = EmailSender(
    smtp_user=os.getenv('GMAIL_SENDER'),        # ✅ Lit depuis .env
    smtp_password=os.getenv('GMAIL_APP_PASSWORD'), # ✅ Lit depuis .env
    from_email=os.getenv('GMAIL_SENDER')
)
```

---

## 📊 Types d'Emails Disponibles

Tous ces emails sont déjà implémentés et prêts à l'emploi:

1. **Disputes détectés** 🚨

   ```python
   send_disputes_detected_email(client_email, disputes_count, total_amount, disputes_summary)
   ```

2. **Réclamation soumise** ✅

   ```python
   send_claim_submitted_email(client_email, claim_reference, carrier, amount_requested, order_id, submission_method)
   ```

3. **Réclamation acceptée** 🎉

   ```python
   send_claim_accepted_email(client_email, claim_reference, carrier, accepted_amount, client_share, platform_fee)
   ```

4. **Réclamation refusée** ⚠️

   ```python
   send_claim_rejected_email(client_email, claim_reference, carrier, rejection_reason)
   ```

---

## 🔒 Sécurité

### ✅ Bonnes Pratiques

1. **Ne JAMAIS commiter .env** dans Git
   - `.env` est déjà dans `.gitignore` ✅

2. **Utiliser des variables d'environnement** pour production:

   ```bash
   # Sur Heroku
   heroku config:set GMAIL_SENDER=contact@example.com
   heroku config:set GMAIL_APP_PASSWORD=xxxx
   ```

3. **Rotation des mots de passe:**
   - Changez le mot de passe d'app tous les 6 mois
   - Révoquez les anciens mots de passe

### ⚠️ Limitations Gmail

- **Quota gratuit:** 500 emails/jour
- **Délai entre envois:** Recommandé 1-2 secondes
- **Limites débit:** 10 emails/minute max

Si vous dépassez ces limites, Gmail peut temporairement bloquer l'envoi.

### 🔄 Alternative pour Volume Élevé

Si vous avez besoin d'envoyer **plus de 500 emails/jour**, considérez:

1. **SendGrid** - 100 emails/jour gratuit, puis payant
2. **Mailgun** - 1000 emails/mois gratuit
3. **Amazon SES** - Très bon marché (0.10$/1000 emails)

---

## 🐛 Dépannage

### Erreur: "Username and Password not accepted"

**Solution:**

1. Vérifiez que la 2FA est activée
2. Régénérez un nouveau mot de passe d'application
3. Copiez-le EXACTEMENT (avec les espaces)

### Erreur: "SMTPAuthenticationError"

**Solution:**

1. Vérifiez `GMAIL_SENDER` = email exact du compte
2. Vérifiez `GMAIL_APP_PASSWORD` = mot de passe d'app (pas mot de passe normal)

### Email va dans Spam

**Solutions:**

1. Ajoutez un enregistrement SPF dans votre DNS:

   ```text
   v=spf1 include:_spf.google.com ~all
   ```

2. Utilisez un domaine personnalisé (au lieu de @gmail.com)
3. Augmentez progressivement le volume (warm-up)

### Test réussit mais production échoue

**Vérifiez:**

1. Variables d'environnement chargées (`load_dotenv()`)
2. Fichier `.env` présent dans le bon répertoire
3. Permissions de lecture du fichier `.env`

---

## ✅ Checklist Finale

- [ ] 2FA activée sur Gmail
- [ ] Mot de passe d'application généré
- [ ] `GMAIL_SENDER` configuré dans `.env`
- [ ] `GMAIL_APP_PASSWORD` configuré dans `.env`
- [ ] Test avec `python test_real_email.py` réussi
- [ ] Email reçu dans la boîte mail
- [ ] `.env` dans `.gitignore`

---

## 🎉 Félicitations

Vos emails sont maintenant configurés et **PRODUCTION-READY** !

Chaque fois que votre application appelle `send_*_email()`, un **vrai email** sera envoyé à vos clients.

---

**🚀 Prêt pour envoyer des milliers d'emails automatiques !**
