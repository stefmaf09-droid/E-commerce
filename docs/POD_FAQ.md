# POD System - FAQ Complète pour Débutants

*Guide complet pour comprendre et utiliser le système de Preuve de Livraison (POD)*

---

## 🤔 Les Bases

### Qu'est-ce qu'un POD ?

**POD** signifie "**Proof of Delivery**" (Preuve de Livraison en français).

C'est un **document officiel** fourni par le transporteur qui prouve qu'un colis a bien été livré. Il contient généralement :

- ✅ La date et l'heure de livraison
- ✅ Le nom de la personne qui a reçu le colis
- ✅ Parfois une signature ou une photo

**Exemple concret :**  
Vous avez envoyé un colis à un client via Chronopost. Le client dit qu'il n'a jamais reçu le colis. Vous demandez le POD à Chronopost, et celui-ci montre que le colis a été livré le 5 février à 14h32, signé par "M. Dupont". C'est votre preuve !

---

### Pourquoi ai-je besoin de PODs ?

Les PODs sont **essentiels** pour :

1. **Prouver une livraison** lors d'un litige client
2. **Réclamer une indemnisation** si le transporteur a perdu/endommagé le colis
3. **Justifier un refus de remboursement** si le client ment
4. **Documentation légale** en cas de procédure judiciaire

**Sans POD = Vous perdez 80% des litiges !**

---

### Comment les PODs sont-ils récupérés automatiquement ?

Notre système contacte directement les **API des transporteurs** (Chronopost, UPS, Colissimo, DHL, etc.) pour télécharger les PODs.

**Voici comment ça marche :**

1. Vous créez une réclamation dans l'application
2. Le système détecte le numéro de suivi (*tracking number*)
3. Il envoie une requête API au transporteur
4. Le transporteur répond avec le PDF du POD
5. Le POD est stocké et disponible immédiatement

**Vous n'avez RIEN à faire !** Tout est automatique.

---

### Combien de temps faut-il pour récupérer un POD ?

| Situation | Temps moyen |
|-----------|-------------|
| **POD disponible** | 2-5 secondes |
| **POD pas encore généré** | Réessai automatique après 1h-6h-24h-72h |
| **Erreur temporaire** | Réessai automatique selon backoff |
| **Erreur persistante** | Email d'alerte envoyé |

**💡 Conseil :** La plupart des PODs sont disponibles **24-48h après livraison**.

---

## 📊 Analytics Dashboard (POD Analytics)

### Comment accéder au dashboard ?

**Étape 1 :** Lancez l'application

```powershell
streamlit run client_dashboard_main_new.py
```

**Étape 2 :** Connectez-vous avec vos identifiants

**Étape 3 :** Dans le menu latéral, cliquez sur **"📊 POD Analytics"**

C'est tout ! 🎉

---

### Que signifie "Success Rate" (Taux de Réussite) ?

**Définition simple :**  
Le pourcentage de PODs récupérés avec succès parmi toutes les tentatives.

**Formule :**

```
Success Rate = (PODs réussis / Total tentatives) × 100
```

**Exemple :**

- Tentatives totales : 100
- Réussies : 87
- Échouées : 13
- **Success Rate = 87%**

**📈 Benchmark :**

- ✅ **> 85%** = Excellent
- ⚠️ **70-85%** = Correct (vérifiez les erreurs)
- ❌ **< 70%** = Problème (contactez le support)

---

### Pourquoi mon temps de récupération moyen est-il élevé ?

**Causes courantes :**

1. **Transporteur lent à répondre**
   - Solution : Normal pour certains transporteurs (ex: DHL = 3-4s, Chronopost = 1-2s)

2. **API en surcharge**
   - Solution : Attendez 1-2h, le système réessaie automatiquement

3. **Beaucoup de réessais**
   - Solution : Vérifiez la section "Retry Analysis" pour voir combien de tentatives échouent

4. **Connexion Internet lente**
   - Solution : Vérifiez votre connexion

**💡 Temps acceptable :**

- **< 5 secondes** = Excellent
- **5-10 secondes** = Normal
- **> 10 secondes** = Vérifier

---

### Comment lire la section "Carrier Performance" ?

Cette section montre les performances de **chaque transporteur**.

**Colonnes expliquées :**

| Colonne | Signification | Bon si... |
|---------|--------------|-----------|
| **Carrier** | Nom du transporteur | - |
| **Success Rate** | % de PODs récupérés | > 85% |
| **Avg Time** | Temps moyen de récupération | < 5s |
| **Total PODs** | Nombre total de PODs traités | - |

**Exemple d'utilisation :**

Si vous voyez :

- Chronopost : 92% success, 2.1s
- UPS : 78% success, 8.5s

➡️ **Action :** Vérifiez pourquoi UPS a un taux plus bas (voir section Errors)

---

### Que faire si un transporteur a de mauvaises performances ?

**Étape 1 : Identifier le problème**

- Allez dans "Error Classification"
- Regardez les erreurs pour ce transporteur

**Étape 2 : Comprendre l'erreur**

| Type d'erreur | Cause | Solution |
|---------------|-------|----------|
| `Authentication failed` | Clés API invalides | Vérifiez `.streamlit/secrets.toml` |
| `Rate limit exceeded` | Trop de requêtes | Attendez, le système gère automatiquement |
| `POD not found` | POD pas encore disponible | Normal, réessai automatique |
| `Connection timeout` | Problème réseau | Vérifiez votre connexion |

**Étape 3 : Agir**

- Si erreur persistante → Contactez support
- Si erreur temporaire → Laissez le système gérer

---

## 🔄 Système Auto-Retry (Réessais Automatiques)

### Comment fonctionne le système de réessais ?

Le système utilise un **backoff exponentiel** pour réessayer intelligemment.

**Timeline des réessais :**

```
Échec initial
    ↓
⏰ Attendre 1 heure
    ↓
Réessai #1 (après 1h)
    ↓ (si échec)
⏰ Attendre 6 heures
    ↓
Réessai #2 (après 7h total)
    ↓ (si échec)
⏰ Attendre 24 heures
    ↓
Réessai #3 (après 31h total)
    ↓ (si échec)
⏰ Attendre 72 heures
    ↓
Réessai #4 FINAL (après 103h total)
    ↓ (si échec)
❌ Abandon + Email d'alerte
```

**Pourquoi ce système ?**

- Évite de bombarder les APIs
- Laisse le temps au transporteur de générer le POD
- Maximise les chances de succès

---

### Pourquoi certains PODs échoués ne sont-ils PAS réessayés ?

Le système **classe les erreurs** en 2 catégories :

**1. Erreurs temporaires** (⏳ Réessai automatique)

- `Connection timeout` - Problème réseau passager
- `Rate limit exceeded` - API surchargée temporairement
- `POD not available yet` - Pas encore généré

**2. Erreurs persistantes** (❌ PAS de réessai)

- `Invalid tracking number` - Numéro incorrect, réessayer ne changera rien
- `Authentication failed` - Clés API invalides
- `Access denied` - Permissions manquantes

**💡 Pourquoi ?**  
➡️ Réessayer une erreur persistante = gaspiller des ressources API

**Que faire avec erreurs persistantes ?**

- Vérifiez le numéro de tracking
- Vérifiez vos clés API
- Corrigez manuellement dans "Gestion Litiges"

---

### Puis-je forcer un réessai manuel ?

**OUI ! Voici comment :**

**Méthode 1 : Réessai individuel**

1. Allez dans **"Gestion Litiges"**
2. Trouvez la réclamation avec POD échoué
3. Cliquez sur le bouton **"🔄 Réessayer"**
4. Attendez 2-5 secondes

**Méthode 2 : Réessai en masse**

1. Allez dans **"Gestion Litiges"**
2. Sélectionnez plusieurs réclamations
3. Cliquez sur **"Réessayer les échecs sélectionnés"**
4. Le système traite chaque POD (respecte les limites API)

**⚠️ Attention :**  
Ne spammez pas les réessais manuels ! Respectez les limites API :

- Chronopost : 60 req/min
- UPS : 30 req/min

---

## ⚠️ Dépannage (Troubleshooting)

### Le POD affiche "Failed" - que faire maintenant ?

**Étape 1 : Voir l'erreur exacte**

1. Dans "Gestion Litiges", cherchez la réclamation
2. Regardez le message d'erreur sous "POD Status"

**Étape 2 : Diagnostiquer**

**Si l'erreur dit :**

**❌ "Invalid tracking number"**

```
Problème : Le numéro de suivi est incorrect
Solution :
1. Vérifiez le numéro sur votre commande
2. Corrigez dans "Gestion Litiges"
3. Réessayez manuellement
```

**❌ "POD not found"**

```
Problème : Le transporteur n'a pas encore généré le POD
Solution :
1. Attendez 24h après livraison
2. Le système réessaiera automatiquement
3. Si > 72h, contactez le transporteur
```

**❌ "Authentication failed"**

```
Problème : Vos clés API sont invalides/expirées
Solution :
1. Ouvrez .streamlit/secrets.toml
2. Vérifiez les clés pour ce transporteur
3. Mettez à jour si nécessaire
4. Redémarrez l'application
```

**❌ "Rate limit exceeded"**

```
Problème : Trop de requêtes API (limite atteinte)
Solution :
1. Attendez 1h (le système gère automatiquement)
2. NE PAS réessayer manuellement
3. Normal si vous traitez beaucoup de PODs
```

---

### Je ne vois pas "POD Analytics" dans le menu

**Vérification #1 : Version à jour ?**

```powershell
# Vérifiez que le fichier existe
dir src\dashboard\pod_analytics_page.py
```

Si le fichier n'existe pas → Version obsolète, mettez à jour.

**Vérification #2 : Menu intégré ?**

```powershell
# Ouvrez client_dashboard_main_new.py
# Cherchez "POD Analytics" dans le code
```

Si absent → Suivez `quick_start.md` pour l'intégration.

**Vérification #3 : Redémarrage**

```powershell
# Arrêtez l'application (Ctrl+C)
# Relancez
streamlit run client_dashboard_main_new.py
```

---

### Le scheduler automatique ne fonctionne pas

**Windows : Vérification Task Scheduler**

**Étape 1 : Vérifier que la tâche existe**

```powershell
schtasks /query /tn "PODRetryScheduler"
```

**Résultat attendu :**

```
Nom de la tâche: \PODRetryScheduler
Prochaine exécution: 06/02/2026 17:00:00
Statut: Prêt
```

**Étape 2 : Vérifier les logs**

```powershell
type logs\pod_retry_scheduler.log | Select-Object -Last 50
```

**Si pas de logs récents :**

1. La tâche n'a jamais démarré
2. Vérifiez les permissions (admin requis)

**Étape 3 : Tester manuellement**

```powershell
python scripts\pod_retry_scheduler.py --batch-size 5
```

Si erreur → Corrigez (`pip install -r requirements.txt`)  
Si OK → Problème avec Task Scheduler

**Recréer la tâche :**

```powershell
# Supprimer
schtasks /delete /tn "PODRetryScheduler" /f

# Recréer
schtasks /create /tn "PODRetryScheduler" /tr "python D:\Recours_Ecommerce\scripts\pod_retry_scheduler.py" /sc hourly /mo 1 /f
```

---

## 🔧 Questions Techniques

### Quels sont les intervalles de réessai exacts ?

```python
RETRY_INTERVALS = {
    0: "Échec initial",
    1: "1 heure (3600s)",
    2: "6 heures (21600s)",
    3: "24 heures (86400s)",
    4: "72 heures (259200s)"
}
```

**Calcul total :** 1h + 6h + 24h + 72h = **103 heures** (~4.3 jours)

---

### Comment vérifier les logs du scheduler ?

**Localisation du fichier :**

```
D:\Recours_Ecommerce\logs\pod_retry_scheduler.log
```

**Commandes utiles :**

**Voir les 100 dernières lignes :**

```powershell
type logs\pod_retry_scheduler.log | Select-Object -Last 100
```

**Filtrer les erreurs uniquement :**

```powershell
type logs\pod_retry_scheduler.log | Select-String "ERROR"
```

**Surveiller en temps réel :**

```powershell
Get-Content logs\pod_retry_scheduler.log -Wait -Tail 50
```

**Logs d'une date spécifique :**

```powershell
type logs\pod_retry_scheduler.log | Select-String "2026-02-06"
```

---

### Puis-je personnaliser les intervalles de réessai ?

**OUI, mais déconseillé.** Voici comment :

**Étape 1 : Ouvrir le fichier**

```powershell
notepad scripts\pod_retry_scheduler.py
```

**Étape 2 : Trouver la variable** (ligne ~50)

```python
RETRY_DELAYS = [
    3600,    # 1 heure
    21600,   # 6 heures
    86400,   # 24 heures
    259200   # 72 heures
]
```

**Étape 3 : Modifier** (exemple : réessais plus rapides)

```python
RETRY_DELAYS = [
    1800,    # 30 minutes
    7200,    # 2 heures
    43200,   # 12 heures
    86400    # 24 heures
]
```

**⚠️ Attention :**

- Des intervalles trop courts = risque de ban API
- Respectez les limites transporteurs
- Testez d'abord avec `--batch-size 1`

---

### Combien d'API calls le scheduler fait-il par exécution ?

**Calcul :**

```
Nombre de calls = MIN(batch_size, nombre de PODs éligibles)
```

**Exemple :**

- Batch size configuré : 10
- PODs échoués éligibles : 25
- **Résultat : 10 calls** (puis attendre prochaine exécution)

**Limite de sécurité :** Max 50 PODs par exécution (configurable)

**Par défaut :**

- Scheduler exécuté : **toutes les heures**
- Batch size : **20**
- Maximum théorique : **480 PODs/jour** (20 × 24)

---

### Comment exporter les données analytics en CSV ?

**Actuellement :** Pas implémenté nativement (Phase B en attente)

**Solution temporaire :**

**Méthode manuelle (via code) :**

```python
import pandas as pd
from src.database.database_manager import get_db_manager

db = get_db_manager()
conn = db.get_connection()

# Requête complète
query = """
SELECT 
    claim_reference,
    carrier,
    pod_fetch_status,
    pod_fetched_at,
    pod_retry_count,
    pod_fetch_error
FROM claims
WHERE pod_fetch_status IS NOT NULL
"""

df = pd.read_sql(query, conn)
df.to_csv('pod_analytics_export.csv', index=False)
conn.close()

print("✅ Export terminé : pod_analytics_export.csv")
```

**Exécution :**

```powershell
python export_script.py
```

---

## 📞 Support & Ressources

### Où trouver plus d'aide ?

**📖 Documentation complète :**

- `docs/POD_RETRY_SETUP.md` - Configuration scheduler
- `docs/user_guide_pod_analytics.md` - Guide Analytics (à venir Phase E)
- `quick_start.md` - Démarrage rapide

**🎥 Vidéo démo :**

- *À venir Phase E*

**📧 Contact support :**

- Email : <admin@refundly.ai>
- Discord : *lien à venir*

---

## 🎯 Astuces & Bonnes Pratiques

### ✅ Checklist hebdomadaire

Chaque **lundi matin**, vérifiez :

- [ ] Success rate global (target: > 85%)
- [ ] Transporteurs avec performances < 80%
- [ ] Logs du scheduler (erreurs critiques ?)
- [ ] PODs échoués depuis > 7 jours

**Temps nécessaire : 5 minutes**

---

### 💡 Optimisations recommandées

1. **Laissez tourner le scheduler H24**
   - Ne l'arrêtez jamais
   - Il se réveille seulement quand nécessaire

2. **Surveillez les pics d'erreurs**
   - Si > 50 erreurs/jour → Problème API
   - Vérifiez les clés immédiatement

3. **Archivez les vieux logs**
   - Logs > 90 jours → Supprimez
   - Gardez juste les 3 derniers mois

4. **Mettez à jour régulièrement**
   - Nouvelle version = nouveaux transporteurs
   - Check GitHub releases

---

### 🚫 Erreurs à éviter

**❌ NE PAS :**

- Réessayer manuellement 10× d'affilée (ban API)
- Modifier les delay trop court (< 30min)
- Ignorer les erreurs `Authentication failed`
- Lancer 2 schedulers en parallèle

**✅ À LA PLACE :**

- Laissez le système gérer les réessais
- Gardez les delays par défaut
- Corrigez les auth errors immédiatement
- 1 seul scheduler suffit

---

## 🎓 Glossaire

| Terme | Définition |
|-------|------------|
| **POD** | Proof of Delivery - preuve de livraison |
| **Success Rate** | % de PODs récupérés avec succès |
| **Backoff exponentiel** | Augmentation progressive du délai entre réessais |
| **Rate limit** | Limite du nombre de requêtes API par minute |
| **Batch size** | Nombre de PODs traités par exécution |
| **Retry count** | Nombre de tentatives effectuées |
| **Persistent error** | Erreur qui ne se résoudra  pas avec le temps |
| **Temporary error** | Erreur passagère qui peut se résoudre |
| **API endpoint** | URL d'accès à l'API transporteur |
| **Tracking number** | Numéro de suivi du colis |

---

**Dernière mise à jour : 6 février 2026**  
**Version : 1.0**  
**Auteur : Refundly Team**
