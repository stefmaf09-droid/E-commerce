# 🔐 Configuration Rapide Gmail - <stefmaf09@gmail.com>

## ⚠️ IMPORTANT SÉCURITÉ

**N'utilisez JAMAIS votre mot de passe Gmail principal dans le code !**

Gmail requiert un **"Mot de passe d'application"** pour les applications tierces. C'est plus sécurisé car :

- ✅ Vous pouvez le révoquer sans changer votre mot de passe principal
- ✅ Il est spécifique à cette application
- ✅ Pas de risque si le code est compromis

---

## 🚀 Configuration en 3 Minutes

### Étape 1: Activer l'Authentification à 2 Facteurs (2FA)

1. Allez sur <https://myaccount.google.com/security>
2. Section **"Validation en deux étapes"**
3. Cliquez **"Activer"** si ce n'est pas déjà fait
4. Suivez les instructions (SMS ou application Google Authenticator)

> 📱 **Si déjà activée:** Passez directement à l'Étape 2

---

### Étape 2: Créer un Mot de Passe d'Application

1. **Allez sur:** <https://myaccount.google.com/apppasswords>
2. **Connectez-vous** avec votre compte `stefmaf09@gmail.com`
3. **Si vous voyez "Les mots de passe d'application ne sont pas disponibles":**
   - Retournez activer la 2FA (Étape 1)
4. Dans **"Sélectionner l'application"**: Choisissez **"Mail"**
5. Dans **"Sélectionner l'appareil"**: Choisissez **"Autre (nom personnalisé)"**
6. Tapez: **"Recours Ecommerce"**
7. Cliquez **"Générer"**
8. **📋 COPIEZ LE MOT DE PASSE** qui apparaît (format: `xxxx xxxx xxxx xxxx`)

**Exemple du mot de passe généré:**

```text
abcd efgh ijkl mnop
```

> ⚠️ Vous ne pourrez plus le revoir ! Copiez-le maintenant.

---

### Étape 3: Configurer le Fichier .env

1. Ouvrez le fichier `.env` à la racine du projet
2. Remplacez cette ligne:

   ```env
   GMAIL_APP_PASSWORD=REMPLACER_PAR_MOT_DE_PASSE_APP
   ```

   Par (avec le mot de passe que vous avez copié):

   ```env
   GMAIL_APP_PASSWORD=abcd efgh ijkl mnop
   ```

**Exemple final dans .env:**

```bash
GMAIL_SENDER=stefmaf09@gmail.com
GMAIL_APP_PASSWORD=xmqp ytkr wvsd phql
```

---

### Étape 4: Tester l'Envoi d'Email

```bash
python test_real_email.py
```

**Ce qui va se passer:**

1. ✅ Vérification des credentials
2. 📧 Envoi d'un email de test
3. 📬 Email arrive dans votre boîte `stefmaf09@gmail.com`

---

## 🎯 Résumé Rapide

| Étape | Action | Lien |
| :--- | :--- | :--- |
| 1 | Activer 2FA | <https://myaccount.google.com/security> |
| 2 | Créer App Password | <https://myaccount.google.com/apppasswords> |
| 3 | Copier le mot de passe | `xxxx xxxx xxxx xxxx` |
| 4 | Coller dans .env | `GMAIL_APP_PASSWORD=...` |
| 5 | Tester | `python test_real_email.py` |

---

## ✅ Vérification Rapide

Votre fichier `.env` doit ressembler à ça:

```bash
GMAIL_SENDER=stefmaf09@gmail.com
GMAIL_APP_PASSWORD=abcd efgh ijkl mnop  # ← Votre mot de passe d'app (16 caractères)
```

**PAS comme ça:**

```bash
# ❌ NE PAS FAIRE ÇA
GMAIL_APP_PASSWORD=Siobhane5607!  # ← Mot de passe principal = NE MARCHE PAS
```

---

## 🐛 Problèmes Courants

### "Les mots de passe d'application ne sont pas disponibles"

**Solution:** Activez d'abord la 2FA (Étape 1)

### "Nom d'utilisateur et mot de passe non acceptés"

**Solution:**

- Vérifiez que vous utilisez le **mot de passe d'app** (pas le principal)
- Vérifiez qu'il n'y a pas d'espaces en trop
- Régénérez un nouveau mot de passe d'app

### Email ne part pas

**Solution:**

```bash
# Vérifier que .env est chargé
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('GMAIL_SENDER'))"
```

---

## 🎉 C'est Prêt

Une fois configuré, tous vos emails seront envoyés depuis **<stefmaf09@gmail.com>** automatiquement !

**Les clients recevront:**

- 📧 Notifications de litiges détectés
- ✅ Confirmations de réclamations
- 🎉 Notifications d'acceptation
- 💰 Informations de paiement

---

**Temps total: ~3 minutes** ⏱️
