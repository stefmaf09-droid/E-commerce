# 📧 Configuration Email Gmail - Guide Complet

## 🎯 Étapes pour Activer l'Envoi d'Emails

### 1. Créer un Mot de Passe d'Application Gmail

1. **Allez sur** : <https://myaccount.google.com/apppasswords>
2. **Connectez-vous** à votre compte Gmail
3. **Important** : Vous devez avoir la **vérification en 2 étapes activée**
   - Si pas encore fait : <https://myaccount.google.com/security>
4. Dans **"Sélectionner l'application"** : choisissez "Autre (nom personnalisé)"
5. Entrez le nom : **"Agent IA Recouvrement"**
6. Cliquez sur **"Générer"**
7. **Copiez** le mot de passe de 16 caractères (format: `xxxx xxxx xxxx xxxx`)

### 2. Configurer les Variables d'Environnement

**Option A - Fichier `.env` (Local)** :

1. Créez un fichier `.env` à la racine du projet
2. Ajoutez ces lignes :

```env
GMAIL_SENDER=votre-email@gmail.com
GMAIL_APP_PASSWORD=xxxxyyyyzzzzwwww
```

(Remplacez par vos vraies valeurs, **sans espaces** dans le mot de passe)

**Option B - Variables d'Environnement Système** :

**Windows (PowerShell)** :

```powershell
$env:GMAIL_SENDER="votre-email@gmail.com"
$env:GMAIL_APP_PASSWORD="xxxxyyyyzzzzwwww"
```

**Linux/Mac** :

```bash
export GMAIL_SENDER="votre-email@gmail.com"
export GMAIL_APP_PASSWORD="xxxxyyyyzzzzwwww"
```

### 3. Installer python-dotenv (pour lire le .env)

```bash
pip install python-dotenv
```

### 4. Tester l'Envoi d'Email

```bash
python src/notifications/email_sender.py
```

Vous devriez voir :

```text
📧 Configuration:
  SMTP Server: smtp.gmail.com:465
  Sender: votre-email@gmail.com
  Password configured: ✅ Yes
```

---

## 📧 Types d'Emails Envoyés

### 1. Email de Bienvenue

- **Quand** : Après inscription d'un nouveau client
- **Contenu** : Message de bienvenue + lien vers le dashboard
- **Template** : HTML professionnel avec styles

### 2. Email de Réinitialisation de Mot de Passe

- **Quand** : Après réinitialisation du mot de passe
- **Contenu** : Confirmation + conseils de sécurité
- **Alerte** : Avertissement si ce n'est pas le client

### 3. Email de Confirmation de Réclamation

- **Quand** : Après soumission automatique d'une réclamation
- **Contenu** :
  - Référence du dossier
  - Montant demandé
  - Transporteur
  - Délai légal de réponse
  - Prochaines étapes

---

## 🔒 Sécurité

### ⚠️ Important

- **Ne JAMAIS** committer le fichier `.env` sur Git
- Le `.env` est déjà dans `.gitignore`
- Utilisez `.env.example` comme template
- Le mot de passe d'application est **spécifique** à cette app (pas votre mot de passe Gmail)

### 🛡️ Bonnes Pratiques

- Créez un compte Gmail dédié pour l'application (ex: `noreply-agentia@gmail.com`)
- Ne réutilisez pas votre compte personnel
- Limitez les tentatives d'envoi (Gmail limite à ~500 emails/jour)

---

## 📊 Limites Gmail SMTP

| Critère | Limite |
| :--- | :--- |
| Emails/jour | ~500 |
| Destinataires/email | 1 (notre cas) |
| Taille max | 25 MB |
| Délivrabilité | Bonne (Gmail réputé) |

---

## 🚀 Intégration dans l'Application

Les emails sont automatiquement envoyés dans ces cas :

1. **Inscription** → `send_welcome_email()`
2. **Réinitialisation MDP** → `send_password_reset_email()`
3. **Soumission réclamation** → `send_claim_confirmation_email()`

**Code activé dans** :

- `client_dashboard.py` (inscription, reset mot de passe)
- `claim_automation.py` (confirmation réclamation)

---

## 🐛 Dépannage

### Erreur "Application-specific password required"

➡️ Vous devez créer un **mot de passe d'application**, pas utiliser votre mot de passe Gmail normal

### Erreur "Username and Password not accepted"

➡️ Vérifiez que :

- La vérification en 2 étapes est activée
- Le mot de passe d'application est correct (sans espaces)
- L'email expéditeur est correct

### Erreur "SMTPAuthenticationError"

➡️ Le compte Gmail bloque l'accès. Solutions :

- Utilisez un mot de passe d'application
- Vérifiez <https://myaccount.google.com/lesssecureapps>

### Emails ne partent pas

➡️ Vérifiez les logs :

- Le module log "✅ Email sent" si envoyé
- Regardez les erreurs dans la console

---

## 📝 Test Rapide

```python
from notifications.email_sender import send_welcome_email

# Envoyez-vous un email de test
send_welcome_email("votre-email@test.com", "Test Client")
```

Si ça fonctionne, vous recevrez un email de bienvenue professionnel ! 🎉
