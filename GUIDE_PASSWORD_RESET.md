# 🔐 Guide de Réinitialisation de Mot de Passe

Ce guide explique comment configurer et utiliser le système de réinitialisation de mot de passe par email.

## 📧 CONFIGURATION EMAIL

### Option 1 : Gmail (Recommandé pour test)

1. **Créer un App Password Google** :
   - Allez sur <https://myaccount.google.com/apppasswords>
   - Sélectionnez "Mail" et "Windows Computer"
   - Générez le mot de passe (16 caractères)

2. **Configurer les variables d'environnement** :

   ```bash
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=votre-email@gmail.com
   SMTP_PASSWORD=abcd efgh ijkl mnop  # App Password généré
   FROM_EMAIL=votre-email@gmail.com
   FROM_NAME=Agent IA Recouvrement
   ```

### Option 2 : SendGrid (Production)

1. **Créer compte SendGrid** : <https://sendgrid.com/>
2. **Générer API Key**
3. **Configurer** :

   ```bash
   SMTP_HOST=smtp.sendgrid.net
   SMTP_PORT=587
   SMTP_USER=apikey
   SMTP_PASSWORD=votre-api-key-sendgrid
   FROM_EMAIL=noreply@votre-domaine.com
   FROM_NAME=Agent IA Recouvrement
   ```

### Option 3 : Mailgun, AWS SES, etc

Consultez la documentation du provider pour les paramètres SMTP.

---

## 🔧 INSTALLATION

### 1. Installer python-dotenv (si pas déjà fait)

```bash
pip install python-dotenv
```

### 2. Créer fichier .env à la racine

```bash
# Copier .env.example vers .env
copy .env.example .env

# Éditer .env avec vos credentials
notepad .env
```

### 3. Charger les variables dans l'app

Ajouter en haut de `client_dashboard.py` :

```python
from dotenv import load_dotenv
load_dotenv()
```

---

## 🧪 TEST EN MODE DEV

Sans configuration SMTP, le système fonctionne en **mode DEV** :

- Génère les tokens correctement
- Affiche l'URL de reset dans la console au lieu d'envoyer l'email
- Parfait pour tester avant la prod !

---

## 🎯 UTILISATION

### Côté Client

1. Clic "Mot de passe oublié ?" sur page de connexion
2. Entre son email
3. Reçoit email avec lien (valide 24h)
4. Clic lien → formulaire nouveau mot de passe
5. Entre nouveau password (min 8 caractères)
6. Confirmation → peut se connecter

### Côté Admin

- Les tokens sont stockés dans `data/reset_tokens.json`
- Expiration auto après 24h
- Token invalidé après utilisation

---

## 🔒 SÉCURITÉ

### Implémenté ✅

- Tokens sécurisés (secrets.token_urlsafe)
- Expiration 24h
- Validation token avant reset
- Pas de révélation si email existe

### TODO Production ⚠️

- [ ] Implémenter bcrypt pour hash password
- [ ] Rate limiting (max 3 tentatives/heure)
- [ ] Logs des tentatives de reset
- [ ] Email de confirmation après reset
- [ ] 2FA optionnel

---

## 📊 MONITORING

### Vérifier les tokens actifs

```python
python -c "import json; print(json.dumps(json.load(open('data/reset_tokens.json')), indent=2))"
```

### Nettoyer tokens expirés manuellement

```python
from utils.email_service import EmailService
service = EmailService()
# Les tokens expirés sont auto-nettoyés lors de la validation
```

---

## ❓ TROUBLESHOOTING

### Email ne part pas

- Vérifier SMTP_USER et SMTP_PASSWORD dans .env
- Vérifier que .env est chargé (load_dotenv())
- Pour Gmail : utiliser App Password, pas password normal
- Vérifier logs console

### Lien invalide

- Token expiré (>24h)
- Token déjà utilisé
- Vérifier `data/reset_tokens.json`

### Password pas sauvegardé

- TODO: Implémenter storage hash password
- Actuellement juste le token est invalidé
