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

## 7. Code vs Data : Quelle est la différence ?

C'est une confusion fréquente lors du passage au Cloud :

* **GitHub (Code)** : C'est le "moteur" de votre voiture. Quand vous faites une mise à jour sur GitHub, vous changez le moteur, ajoutez des fonctionnalités, corrigez des bugs. Cela se déploie automatiquement sur le Cloud.
* **Base de Données (Data)** : C'est le "carburant" (vos clients, vos dossiers). GitHub ne touche JAMAIS à vos données pour des raisons de sécurité.
* **Le bouton "Cloud Sync"** : C'est la pompe à essence qui permet de transférer votre carburant (données locales) vers le nouveau moteur (Cloud).

**En résumé :**
* Je modifie l'appli (couleurs, boutons) -> **GitHub**
* Je veux voir mes clients sur le site web -> **Cloud Sync**
