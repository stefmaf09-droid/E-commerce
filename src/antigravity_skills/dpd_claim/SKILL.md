---
name: DPD Claim Submission
description: Automatically navigate DPD portal and submit delivery claim
---

# DPD Claim Submission Skill

## 🎯 Objective

Automatically submit delivery dispute claims on DPD professional portal.

## 📋 Prerequisites

- `tracking_number`: DPD tracking (e.g., "0123456789012")
- `claim_type`: retard/perdu/endommagé/pod_invalide
- `claim_text`: Generated claim
- `client_email`, `client_name`
- `order_value`, `documents`
- `dpd_account`: Professional credentials (recommended)

## 🔄 Workflow

### Step 1: Access Portal

```text
URL: https://www.dpd.fr/espace-client
Claims: https://www.dpd.fr/reclamation
```

### Step 2: Authentication

**Pro Account** (Recommended):

- Login with contract number + password
- Access reclamations dashboard

**Guest Flow**:

- "Réclamation sans compte"
- Tracking + email verification

### Step 3: Shipment Lookup

- Enter tracking: 13-digit format
- Verify shipment details auto-loaded
- Confirm sender/recipient

### Step 4: Claim Type

Map to DPD categories:

- `retard` → "Délai livraison non respecté"
- `perdu` → "Colis non retrouvé"
- `endommagé` → "Marchandise détériorée"
- `pod_invalide` → "Contestation livraison"

### Step 5: Claim Details

Fill form:

- Description: `claim_text` (max 2000 chars)
- Montant: `order_value`
- Contact: `client_email`, `client_name`

**DPD Pickup Points**:

- If delivery to Pickup: Code point requis
- Same as Mondial Relay logic

### Step 6: Documents

**Required**:

- Facture commerciale (MANDATORY)
- Bordereau DPD

**Optional**:

- POD contestée
- Photos dommages

Upload limit: 5MB/file, 5 files max

### Step 7: Submit

- Check legal confirmations
- Handle captcha if present (2captcha)
- Submit claim

### Step 8: Confirmation

Extract:

- Claim reference: Pattern "DPD-REC-#######"
- Response time: "3-5 jours ouvrés"
- Screenshot + HTML save

## 🔧 Error Handling

| Error | Action |
| :--- | :--- |
| Tracking invalid | Verify 13-digit format |
| Invoice missing | CRITICAL - Cannot proceed |
| Duplicate claim | Retrieve existing ref |

## ⚠️ DPD Specifics

- **Réseau Pickup** : Similar to Mondial Relay
- **Coverage limit** : €600-800 standard
- **Response time** : 3-5 days (faster than MR)
- **Pro account** : Priority processing

## ✅ Success

Return:

```json
{
  "status": "success",
  "carrier": "dpd",
  "claim_reference": "DPD-REC-1234567",
  "tracking_number": "0123456789012",
  "estimated_response": "3-5 jours ouvrés"
}
```

**Last Updated**: 2026-01-20  
**Version**: 1.0  
**Carrier**: DPD Group
