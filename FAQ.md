# Refundly.ai - Foire Aux Questions (FAQ)

Ce document explique le fonctionnement concret de la solution Refundly.ai dans un environnement e-commerce réel.

## 1. Comment fonctionne le processus de récupération ?

### Quel est le déclencheur d'un litige ?

Tout commence par un incident de livraison (colis perdu, volé ou endommagé). Le marchand est responsable de la livraison vis-à-vis de son client final. S'il rembourse le client, il subit une perte financière qu'il doit récupérer auprès du transporteur.

### Pourquoi utiliser Refundly.ai ?

Les transporteurs rejettent souvent les réclamations pour des motifs techniques ou abusifs. Les marchands n'ont souvent pas le temps de gérer ces "micros-litiges". Refundly automatise la détection et la contre-attaque juridique.

---

## 2. Comment Refundly récupère-t-il les données ?

Il existe trois modes d'intégration principaux :

1. **Synchronisation Automatique** : Connexion directe via API aux boutiques (Shopify, PrestaShop, etc.) et aux transporteurs (DHL, Colissimo).
2. **Import CSV** : Le marchand exporte ses données de livraison et les importe en masse dans l'outil.
3. **Analyse de Documents (OCR)** : Le marchand upload une capture d'écran ou un PDF de refus du transporteur. Notre IA "lit" le document pour identifier le motif du rejet et préparer la réponse.

---

## 3. Comment gérer les "petits" transporteurs ?

Pour les transporteurs locaux ou moins technologiques qui n'ont pas d'API :

* **Web Scraping** : L'outil automatise la consultation des pages de suivi publiques.
* **Parsing d'Emails** : Analyse des emails d'incidents envoyés par le transporteur.
* **Upload .EML** : Le marchand peut glisser-déposer un email d'échange directement. Refundly extrait le texte et les justificatifs (photos, documents) automatiquement.

---

## 4. Confidentialité et Aspect Juridique

### L'application "espionne"-t-elle les boîtes mails ?

Non. Pour rester conforme au **RGPD**, nous favorisons deux méthodes :

* **L'Alias / Transfert** : Le marchand configure sa boîte mail pour transférer uniquement les emails suspects vers une adresse technique Refundly.
* **Le dépôt manuel (Dropzone)** : Le marchand choisit activement de partager un document ou un email.

### Quelle est la force juridique de Refundly ?

L'outil s'appuie sur le **Code de Commerce (Article L. 133-3)** qui rend le transporteur garant de la perte ou de l'avarie. Les courriers générés par Refundly sont des documents formels qui forcent le transporteur à réévaluer sa position.
