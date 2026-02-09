# Refundly.ai - Foire Aux Questions (FAQ)

Ce document explique le fonctionnement concret de la solution Refundly.ai dans un environnement e-commerce réel.

## 1. Que se passe-t-il après l'upload des preuves ?

Une fois que vous avez déposé vos documents (photo de colis, email de rejet, PDF), Refundly.ai lance une chaîne de traitement automatisée :

1. **Analyse Immédiate (OCR & IA)** : Le système "lit" le document. S'il s'agit d'un email (.eml), il extrait automatiquement les photos jointes et le texte. S'il s'agit d'une image de refus, l'IA identifie le motif exact du rejet.
2. **Diagnostic et Score de Succès** : L'outil compare le motif du refus aux bases de données juridiques et vous donne un **score de probabilité de récupération**.
3. **Conseils Personnalisés** : Si une pièce manque (ex: une attestation sur l'honneur du client final), l'appli vous l'indique immédiatement pour compléter le dossier.
4. **Génération de la Contre-Attaque** : Refundly génère une **Mise en Demeure personnalisée**. Ce document cite les articles de loi précis (Ex: Article L. 133-3) adaptés à votre cas particulier.
5. **Expédition et Tracking** : L'email de mise en demeure est envoyé. Le système active alors un compte à rebours (généralement 15 jours) et vous alerte si le transporteur ne répond pas.
6. **Recouvrement** : Une fois que le transporteur valide l'indemnisation, les fonds sont récupérés et le litige est marqué comme "Résolu".

---

## 2. Comment fonctionne le processus de récupération ?

### Quel est le déclencheur d'un litige ?

Tout commence par un incident de livraison (colis perdu, volé ou endommagé). Le marchand est responsable de la livraison vis-à-vis de son client final. S'il rembourse le client, il subit une perte financière qu'il doit récupérer auprès du transporteur.

### Pourquoi utiliser Refundly.ai ?

Les transporteurs rejettent souvent les réclamations pour des motifs techniques ou abusifs. Les marchands n'ont souvent pas le temps de gérer ces "micros-litiges". Refundly automatise la détection et la contre-attaque juridique.

---

## 3. Comment Refundly récupère-t-il les données ?

Il existe trois modes d'intégration principaux :

1. **Synchronisation Automatique** : Connexion directe via API aux boutiques (Shopify, PrestaShop, etc.) et aux transporteurs (DHL, Colissimo).
2. **Import CSV** : Le marchand exporte ses données de livraison et les importe en masse dans l'outil.
3. **Analyse de Documents (OCR)** : Le marchand upload une capture d'écran ou un PDF de refus du transporteur. Notre IA "lit" le document pour identifier le motif du rejet et préparer la réponse.

---

## 4. Comment gérer les "petits" transporteurs ?

Pour les transporteurs locaux ou moins technologiques qui n'ont pas d'API :

* **Web Scraping** : L'outil automatise la consultation des pages de suivi publiques.
* **Parsing d'Emails** : Analyse des emails d'incidents envoyés par le transporteur.
* **Upload .EML** : Le marchand peut glisser-déposer un email d'échange directement. Refundly extrait le texte et les justificatifs (photos, documents) automatiquement.

---

## 5. Confidentialité et Aspect Juridique

### L'application "espionne"-t-elle les boîtes mails ?

Non. Pour rester conforme au **RGPD**, nous favorisons deux méthodes :

* **L'Alias / Transfert** : Le marchand configure sa boîte mail pour transférer uniquement les emails suspects vers une adresse technique Refundly.
* **Le dépôt manuel (Dropzone)** : Le marchand choisit activement de partager un document ou un email.

### Quelle est la force juridique de Refundly ?

L'outil s'appuie sur des textes de lois précis selon la zone géographique (voir section suivante). Les courriers générés sont des documents formels qui forcent le transporteur à réévaluer sa position.

---

## 6. Couverture Internationale et Textes de Lois

Refundly.ai est conçu pour fonctionner dans plusieurs pays et zones géographiques, en adaptant automatiquement ses arguments juridiques :

| Zone / Pays | Texte de Loi de Référence |
| :--- | :--- |
| **France** | **Article L. 133-3 du Code de Commerce** (Garantie contre les avaries et pertes). |
| **Union Européenne** | **Convention CMR** (Convention relative au contrat de transport international de marchandises par route). |
| **Royaume-Uni** | **Carriage of Goods by Road Act** (Dérivé de la convention CMR). |
| **États-Unis** | **Carmack Amendment** (U.S. Code § 14706 - Responsabilité fédérale des transporteurs). |
| **Hong Kong** | **Control of Exemption Clauses Ordinance** & Common Law. |
| **Singapour** | **Carriage of Goods by Road Act** & Application of English Law Act. |

---

## 7. Comment Refundly récupère-t-il automatiquement les preuves de livraison ?

### Qu'est-ce qu'un POD (Proof of Delivery) ?

Le **POD** est la preuve de livraison fournie par le transporteur. C'est un document essentiel pour construire un dossier solide face aux refus abusifs. Il contient :

* La signature du destinataire ou photo de dépôt
* L'heure et la date exacte de livraison
* Le lieu de remise du colis
* Des informations sur l'état du colis à la livraison

### Récupération automatique intelligente

Refundly se connecte **automatiquement** aux systèmes des transporteurs pour récupérer ces preuves :

* **Transporteurs supportés** : Colissimo, Chronopost, UPS, DHL, FedEx, GLS, Mondial Relay, et bien d'autres
* **Temps réel** : Dès qu'une livraison est confirmée, le système interroge le transporteur pour obtenir le POD
* **Notification instantanée** : Vous recevez un email dès qu'un POD est récupéré avec un lien de téléchargement
* **Stockage sécurisé** : Les documents sont automatiquement attachés à votre dossier de réclamation

### Pourquoi est-ce important pour vous ?

Quand un transporteur prétend qu'un colis a été livré alors que votre client ne l'a jamais reçu, **le POD est votre arme**. Refundly l'utilise automatiquement pour :

1. Vérifier la signature (est-ce vraiment votre client ?)
2. Comparer l'adresse de livraison avec celle de la commande
3. Renforcer votre mise en demeure avec des preuves concrètes

**Vous n'avez rien à faire** : tout est automatisé en arrière-plan.

---

## 8. Assistant IA : Votre expert disponible 24/7

### Qu'est-ce que l'Assistant Refundly ?

C'est un chatbot intelligent qui répond instantanément à toutes vos questions sur :

* Le fonctionnement de la plateforme
* L'état de vos réclamations
* Les démarches juridiques
* Les textes de lois applicables à votre situation

### Comment l'utiliser ?

L'Assistant est accessible directement depuis votre tableau de bord. Il a été formé sur :

* L'ensemble de cette FAQ
* Les textes de lois internationaux (Article L. 133-3, CMR, Carmack Amendment...)
* Les meilleures pratiques de récupération
* **VOS données personnelles** : réclamations, statistiques, litiges détectés

### L'assistant connaît vos données

L'Assistant a accès en temps réel à **votre compte** pour vous donner des réponses précises et personnalisées :

* Vos statistiques (taux de succès, montants récupérés)
* Vos réclamations en cours et leur statut exact
* Vos litiges détectés mais pas encore réclamés
* Vos boutiques connectées

**Exemple de conversation** :

* **Vous** : "Combien de réclamations j'ai en cours ?"
* **Assistant** : "Vous avez actuellement 3 réclamations en cours : CLM-20260205-001 (Chronopost, sous examen), CLM-20260203-002 (Colissimo, acceptée), et CLM-20260201-003 (UPS, en attente de réponse)."

* **Vous** : "Quel est mon taux de succès ?"
* **Assistant** : "Votre taux de succès est de 75% (9 réclamations acceptées sur 12 au total). Vous avez récupéré 1,245.50 EUR dont 996.40 EUR ont été versés sur votre compte."

---
---

## 9. Exportation et Rapports CSV

### Comment exporter mes données ?

Refundly.ai permet d'exporter vos réclamations et litiges à tout moment pour une analyse plus poussée dans Excel ou Google Sheets :

* **Export via l'Assistant** : Demandez simplement au chatbot "Exporte mes litiges en CSV".
* **Téléchargement Direct** : Une fois le traitement terminé, un bouton **"Télécharger le CSV"** apparaît instantanément.
* **Format Standard** : Le fichier généré est au format CSV standard (UTF-8) avec point-virgule comme séparateur, prêt à être ouvert.

---

## 10. Gestion des Pièces Jointes Emails

### Comment fonctionne l'extraction automatique des documents ?

Le système de gestion des pièces jointes élimine la saisie manuelle de vos justificatifs :

1. **Surveillance IMAP** : Refundly se connecte (avec votre accord) à votre boîte mail de support ou de litiges.
2. **Extraction de Documents** : L'IA détecte les pièces jointes (PDF, signatures, photos de dommages) et les télécharge automatiquement.
3. **Liaison Intelligente** : Si l'objet de l'email contient votre référence de réclamation (ex: CLM-XXXX), le fichier est automatiquement lié au dossier correspondant.
4. **Interface de Gestion** : Dans l'onglet **"Pièces Jointes"**, vous pouvez synchroniser manuellement, visualiser les fichiers non assignés et les lier en un clic à vos litiges.

## 11. BypassScorer : Prédire le succès de vos réclamations

Le **BypassScorer** est un outil d'intelligence artificielle qui évalue la probabilité que votre réclamation soit acceptée par le transporteur avant même que vous ne la poussiez plus loin.

* **Score en temps réel** : Une barre de progression sur chaque litige vous indique le niveau de confiance de l'IA.
* **Critères d'analyse** : Le score prend en compte le type de litige, la fiabilité historique du transporteur sur ce motif précis, et les preuves déjà fournies.
* **Apprentissage continu** : Plus vous l'utilisez, plus il devient précis en apprenant des décisions réelles des transporteurs.

## 12. Conseil Stratégique IA (Bypass Advice)

Lorsqu'un transporteur rejette une réclamation, Refundly.ai ne se contente pas de changer le statut. L'IA analyse la lettre de rejet et vous propose immédiatement un **Conseil Stratégique** :

* **Motif Décodé** : L'IA traduit le jargon du transporteur (ex: "Poids conforme", "Badge d'accès") en termes clairs.
* **Action Recommandée** : Le système vous dit exactement quelle preuve manque pour renverser la situation (ex: "Demandez une photo de l'étiquette au client" ou "Produisez une attestation de non-réception").
* **Force Juridique** : Les conseils incluent les références aux articles de loi (L133-3, CMR) pour renforcer votre réponse.

---
**Refundly.ai** : L'automatisation au service de votre trésorerie.
