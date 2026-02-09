# Base de Connaissances Refundly.ai

Ce document sert de référence complète pour l'Assistant IA Refundly. Il contient toutes les informations sur les fonctionnalités, processus, intégrations et textes de lois de la plateforme.

---

## Vue d'ensemble de la plateforme

### Mission

Refundly.ai automatise la récupération de fonds auprès des transporteurs pour les e-commerçants victimes de litiges de livraison (colis perdus, endommagés, retards, etc.).

### Proposition de valeur

- **Automatisation complète** : De la détection du litige à la génération de mise en demeure juridique
- **Multi-transporteur** : Support de 10+ transporteurs majeurs
- **Multi-pays** : Textes de lois adaptés à chaque juridiction (FR, EU, US, UK, HK, SG)
- **Multi-boutique** : Gestion centralisée de plusieurs boutiques e-commerce
- **IA & Scoring** : Probabilité de succès calculée pour chaque réclamation

---

## Types de litiges supportés

| Type de litige | Code | Description |
|---|---|---|
| **Colis perdu** | `lost` | Le colis n'a jamais été livré et est introuvable |
| **Colis endommagé** | `damaged` | Le colis est arrivé avec des dégâts visibles |
| **Retard de livraison** | `late_delivery` | Le colis est arrivé après la date garantie |
| **POD invalide** | `invalid_pod` | La preuve de livraison ne correspond pas (mauvaise adresse, signature frauduleuse) |

---

## Cycle de vie d'une réclamation

### Statuts possibles

1. **`pending`** : Réclamation créée, en attente de soumission
2. **`submitted`** : Envoyée au transporteur, en attente de réponse
3. **`under_review`** : Le transporteur examine le dossier
4. **`accepted`** : Transporteur accepte l'indemnisation
5. **`rejected`** : Transporteur rejette la réclamation
6. **`paid`** : Argent récupéré et versé au client

### Workflow détaillé

1. **Détection automatique du litige**
   - Intégration e-commerce sync les commandes
   - AI Dispute Detector analyse les anomalies
   - Création d'un enregistrement dans table `disputes`

2. **Création de la réclamation**
   - Client peut transformer un dispute en claim (ou automatique si règle activée)
   - Génération de référence unique : `CLM-YYYYMMDD-XXXX`
   - Collecte des preuves (photos, emails, POD)

3. **Enrichissement automatique**
   - **POD Fetcher** récupère la preuve de livraison auprès du transporteur
   - **OCR Analyzer** extrait les informations des documents uploadés
   - **AI Predictor** calcule le `success_probability` score

4. **Génération de mise en demeure**
   - Legal Document Generator crée un PDF personnalisé
   - Cite les articles de loi adaptés au pays du client
   - Références : Article L. 133-3 (FR), CMR (EU), Carmack Amendment (US)

5. **Soumission et suivi**
   - Email envoyé au transporteur avec PDF en pièce jointe
   - `response_deadline` calculé (généralement 15 jours)
   - Système de relances automatiques si pas de réponse

6. **Traitement de la réponse**
   - Si accepté : mise à jour `status = accepted`, création d'un `payment`
   - Si rejeté : `rejection_reason` enregistré, option de relance juridique

7. **Paiement**
   - Stripe Connect (si configuré) ou suivi manuel
   - Commission plateforme : 20% par défaut
   - Client reçoit email de confirmation avec `client_share`

---

## Intégrations E-commerce

### Plateformes supportées

| Plateforme | Code | Fonctionnalités |
|---|---|---|
| **Shopify** | `shopify` | Sync commandes, tracking, clients |
| **WooCommerce** | `woocommerce` | Sync commandes, tracking, clients |
| **PrestaShop** | `prestashop` | Sync commandes, tracking |
| **Magento** | `magento` | Sync commandes, tracking |
| **BigCommerce** | `bigcommerce` | Sync commandes, tracking |
| **Wix** | `wix` | Sync commandes, tracking |

### Données synchronisées

- **Commandes** : order_id, date, montant, statut
- **Clients** : nom, email, adresse de livraison
- **Tracking** : numéro de suivi, transporteur, événements de livraison
- **Produits** : nom, prix, quantité (pour calcul indemnisation)

---

## Intégrations Transporteurs

### Transporteurs avec API officielle

| Transporteur | Code | POD Auto-Fetch | Tracking |
|---|---|---|---|
| **Colissimo (La Poste)** | `colissimo` | ✅ | ✅ |
| **Chronopost** | `chronopost` | ✅ | ✅ |
| **UPS** | `ups` | ✅ | ✅ |
| **DHL** | `dhl` | ✅ | ✅ |
| **FedEx** | `fedex` | ✅ | ✅ |
| **GLS** | `gls` | ✅ | ✅ |
| **Mondial Relay** | `mondial_relay` | ✅ | ✅ |

### POD Auto-Fetching (Phase 2)

Le système récupère **automatiquement** les preuves de livraison :

- **Worker en arrière-plan** : Interroge les API transporteurs toutes les heures
- **Rate-limiting intelligent** : File d'attente pour respecter les limites API
- **Retry automatique** : En cas d'échec, 3 tentatives avec backoff exponentiel
- **Notification client** : Email automatique avec lien de téléchargement du POD

**Informations extraites du POD** :

- Signature du destinataire (image)
- Photo du colis déposé
- Date et heure exacte de livraison
- Nom du livreur
- Localisation GPS (si disponible)
- Instructions de livraison

---

## Système de scoring IA

### Success Probability

Chaque réclamation reçoit un score de 0 à 1 (0% à 100%) calculé par l'AI Predictor :

**Facteurs positifs** :

- POD obtenu et valide (+30%)
- Photos de dommages claires (+25%)
- Historique de succès avec ce transporteur (+15%)
- Email de rejet du transporteur disponible (+10%)
- Délai de déclaration < 48h (+10%)

**Facteurs négatifs** :

- Pas de POD disponible (-40%)
- Colis marqué "livré" sans preuve de dommage (-30%)
- Délai > 30 jours après livraison (-20%)
- Transporteur connu pour refus systématique (-15%)

**Interprétation** :

- **80-100%** : Excellent, récupération quasi certaine
- **60-79%** : Bon, forte probabilité de succès
- **40-59%** : Moyen, nécessite renforcement du dossier
- **0-39%** : Faible, recommandé de collecter plus de preuves

### Predicted Days to Recovery

Estimation du délai moyen selon le transporteur et le type de litige :

- Colissimo : 12-18 jours
- Chronopost : 10-15 jours
- UPS : 15-25 jours
- DHL : 20-30 jours

---

## Textes de lois par juridiction

### France

**Article L. 133-3 du Code de Commerce**
> "Le transporteur est responsable de plein droit de la perte ou des avaries qui se produisent entre le moment de la prise en charge de la marchandise et celui de la livraison."

### Union Européenne

**Convention CMR (Convention relative au contrat de transport international de marchandises par route)**
> Articles 17-29 : Responsabilité du transporteur pour perte, avarie ou retard

### États-Unis

**Carmack Amendment (49 U.S.C. § 14706)**
> "A carrier providing transportation or service subject to jurisdiction [...] shall issue a receipt or bill of lading for property it receives for transportation."

### Royaume-Uni

**Carriage of Goods by Road Act 1965**
> Application de la Convention CMR au Royaume-Uni

---

## Fonctionnalités du tableau de bord client

### Page principale (Overview)

- **Métriques clés** :
  - Total réclamations
  - Taux de succès
  - Montant total récupéré
  - Montant versé au client
  - Nombre de litiges en attente

### Page Réclamations (Claims Management)

- Liste de toutes les réclamations avec filtres (statut, transporteur, date)
- Détail d'une réclamation : timeline, documents, communications
- Actions : ajouter preuves, envoyer relance, marquer comme payé

### Page Litiges (Disputes)

- Litiges détectés automatiquement mais pas encore réclamés
- Tri par montant récupérable, probabilité de succès
- Action : transformer en réclamation en un clic

### Page Analytics

- Graphiques de performance par transporteur
- Tendances temporelles
- Analyse par type de litige
- Comparaison multi-boutiques

### Page Assistant IA

- Chat en temps réel avec l'assistant Refundly
- Accès au contexte du client (ses réclamations, statistiques)
- Suggestions de questions

### Page Paramètres (Settings)

- Gestion des boutiques e-commerce
- Préférences de notifications
- Configuration Stripe Connect
- Données personnelles (RGPD)

---

## Notifications automatiques

### Emails envoyés aux clients

| Type | Déclencheur | Contenu |
|---|---|---|
| **Welcome** | Inscription | Guide de démarrage |
| **Claim Created** | Nouvelle réclamation | Référence, détails, actions à suivre |
| **Claim Submitted** | Soumission transporteur | Confirmation, deadline de réponse |
| **Claim Updated** | Changement de statut | Nouveau statut, détails |
| **Claim Accepted** | Acceptation transporteur | Montant accepté, délai de paiement |
| **Claim Rejected** | Rejet transporteur | Raison du rejet, options de recours |
| **Payment Received** | Paiement effectué | Montant versé, commission |
| **POD Retrieved** | POD récupéré | Lien de téléchargement POD |
| **Disputes Detected** | Litiges détectés | Nombre, montant récupérable |

---

## FAQ Techniques

### "Combien de temps pour récupérer mon argent ?"

En moyenne 15-30 jours selon le transporteur. Le système vous alerte automatiquement si le délai est dépassé.

### "Pourquoi ma réclamation a été rejetée ?"

Consultez la raison dans le détail de votre réclamation. Les motifs fréquents :

- Délai de déclaration dépassé
- Preuves insuffisantes
- Colis marqué livré avec signature valide
- Emballage inadéquat (pour dommages)

### "Comment améliorer mes chances de succès ?"

- Déclarez rapidement (< 48h après incident)
- Fournissez des photos claires (colis, dommages, emballage)
- Gardez tous les échanges avec le transporteur
- Laissez Refundly récupérer le POD automatiquement

### "Je peux récupérer combien ?"

- **Valeur déclarée** : Montant assuré lors de l'expédition
- **Valeur réelle** : Prix de vente au client (si pas d'assurance)
- **Maximum transporteur** : Plafonné selon CGV du transporteur

### "Refundly prend quelle commission ?"

20% par défaut (Success Fee uniquement si récupération réussie).

---

## Sécurité et conformité

### RGPD

- Consentement explicite lors de l'inscription
- Export de données personnelles en un clic
- Suppression de compte et données associées
- Logs d'activité pour audit

### Stockage des documents

- Documents uploadés chiffrés (AES-256)
- Accès limité au client propriétaire
- Rétention : 5 ans (conformité légale)

### Paiements

- Stripe Connect (PCI-DSS compliant)
- Aucune donnée bancaire stockée sur nos serveurs
- Traçabilité complète des transactions

---

## Glossaire

- **POD** : Proof of Delivery (preuve de livraison)
- **CMR** : Convention relative au contrat de transport de Marchandises par Route
- **OCR** : Optical Character Recognition (reconnaissance optique de caractères)
- **Success Fee** : Commission prélevée uniquement si récupération réussie
- **Dispute** : Litige détecté mais pas encore réclamé
- **Claim** : Réclamation formelle soumise au transporteur
- **Mise en Demeure** : Document juridique formel exigeant paiement
- **Rate-limiting** : Limitation du nombre de requêtes API par unité de temps
