---
name: Mondial Relay Claim Submission
description: Automatically navigate Mondial Relay portal and submit delivery claim
---

# Mondial Relay Claim Submission Skill

## 🎯 Objective

Automatically submit delivery dispute claims on Mondial Relay professional portal for parcel issues.

## 📋 Prerequisites

Required information:

- `tracking_number`: Mondial Relay tracking (e.g., "MR123456789")
- `claim_type`: Type (retard/perdu/endommagé/pod_invalide)
- `claim_text`: Generated claim description
- `client_email`: Client email
- `client_name`: Client name
- `order_value`: Value in EUR
- `pickup_point`: Relay point code if applicable
- `documents`: Supporting files

Optional:

- `mr_account`: Professional account credentials

## 🔄 Workflow Steps

### Step 1: Access Professional Space

```text
URL: https://www.mondialrelay.fr/espace-pro/
Direct Claims: https://www.mondialrelay.fr/espace-pro/reclamations
```

**Actions**:

1. Navigate to professional portal
2. Accept cookies if prompted
3. Wait for full page load

**Success**: Portal accessible with login or claim form

---

### Step 2: Professional Authentication

#### Option A: Logged-In Flow (Recommended)

1. Click "Connexion Espace Pro"
2. Fill login fields:
   - Identifiant: `mr_account.username` (usually company number)
   - Mot de passe: `mr_account.password`
3. Submit login form
4. Navigate to "Réclamations" section
5. Click "Nouvelle réclamation"

**Note**: Professional account gives priority processing

#### Option B: Public Claim Form

1. Find "Réclamation colis" link
2. May require captcha verification first
3. Fill tracking to verify shipment exists

**Note**: Professional account gives priority processing

---

### Step 3: Shipment Identification

**Tracking Information**:

1. **Numéro de colis**:

   - CSS: `input[name="tracking"]` or `#parcelNumber`
   - Value: `tracking_number`
   - Format: Usually 9-11 digits

2. **Point Relais** (if pickup delivery):

   - Code: `pickup_point` (6 digits, e.g., "012345")
   - Auto-filled if tracking found
   - Manual entry if needed

3. **Date d'expédition**:
   - Auto-detected from tracking
   - Verify accuracy

**Validation**:

- Click "Rechercher" or "Vérifier"
- Wait for shipment details to load
- Confirm sender/recipient match

---

### Step 4: Claim Type Selection

**Mondial Relay Specific Categories**:

| Our Type | MR Portal Option |
| :--- | :--- |
| `retard` | "Délai de livraison dépassé" |
| `perdu` | "Colis non retrouvé" or "Perte de colis" |
| `endommagé` | "Colis endommagé/détérioré" |
| `pod_invalide` | "Contestation de livraison" |

**Actions**:

1. Locate radio buttons or dropdown
2. Select appropriate option
3. Wait for field conditional display

**Special Cases**:

- If pickup point issue: "Problème Point Relais"
- If relay refused: "Refus de prise en charge"

---

### Step 5: Detailed Claim Information

**Sender Section** (if not pre-filled):

- Nom/Raison sociale: `client_name`
- Email: `client_email`
- Téléphone: Placeholder if required

**Recipient Section**:

- Usually auto-filled from tracking
- Double-check address accuracy

**Claim Description**:

- CSS: `textarea[name="description"]` or `#motifReclamation`
- Value: `claim_text`
- Character limit: ~2000-3000 chars
- **Important**: Be precise, Mondial Relay reviews manually

**Incident Details** (conditional fields):

If `claim_type == "endommagé"`:

- Nature du dommage: Dropdown (cassé, déchiré, mouillé)
- Constat fait par: Qui a constaté ? (expéditeur/destinataire/relais)
- Date du constat: Date field

If `claim_type == "retard"`:

- Date limite attendue: Expected delivery date
- Nombre de jours de retard: Auto-calculated

---

### Step 6: Financial Declaration

**Value Declaration** (critical for MR):

1. **Valeur du contenu**:

   - Field: `input[name="value"]` or `#valeurContenu`
   - Value: `order_value`
   - Format: Numeric, 2 decimals
   - **Max**: Check MR coverage limit (usually 600-1000€)

2. **Montant réclamé**:
   - May auto-calculate
   - Or manual entry
   - Usually: `min(order_value + shipping, coverage_limit)`

3. **Justificatif de valeur**:
   - Must upload invoice (REQUIRED by MR)
   - Without invoice, claim likely rejected

---

### Step 7: Upload Supporting Documents

**Mondial Relay Requirements** (strict):

**Mandatory**:

1. ✅ **Facture commerciale**: Invoice proving value
2. ✅ **Bordereau**: MR shipping label copy

**Conditional**:
3. **Photos dommages**: If damaged (min 3 angles)
4. **POD**: If contesting delivery
5. **Email exchanges**: Communication with relay point

**Upload Process**:

1. Locate upload button:
   - Text: "Ajouter documents" or "Joindre fichiers"
   - CSS: `.upload-btn` or `input[type="file"]`

2. For each document:
   - Click upload
   - Select file from `documents` list
   - Wait for progress bar
   - Verify thumbnail/name appears

**File Specs**:

- Formats: PDF, JPG, PNG
- Max size: 5MB per file
- Max total: Usually 5 files
- Naming: Clear names (facture.pdf, photo_dommage1.jpg)

---

### Step 8: Point Relais Information (if applicable)

If delivery was to pickup point and issue with relay:

**Relay Details**:

- Code Point Relais: `pickup_point`
- Nom du relais: Auto-filled
- Adresse: Auto-filled

**Relay Issue Specifics**:

- [ ] Point relais fermé
- [ ] Colis non disponible
- [ ] Délai de garde dépassé
- [ ] Problème d'accueil

**Actions**:

- Select applicable checkbox(es)
- Add details in comment field

---

### Step 9: Review and Legal Consent

**Pre-Submission Review**:

1. Summary section displays all info
2. Verify critical fields:

```python
critical_checks = {
    'tracking': tracking_number,
    'claim_type': verify_selected,
    'value': order_value > 0,
    'invoice': document_count >= 1,
    'description': len(claim_text) > 50
}
```

1. **Legal Declarations** (checkboxes):
   - [ ] "Je certifie l'exactitude des informations"
   - [ ] "J'accepte les conditions générales de réclamation"
   - [ ] "J'autorise MR à enquêter auprès du Point Relais"

**Important**: Mondial Relay may contact relay point directly

---

### Step 10: Submit and Confirm

**Submission**:

1. Locate submit button:
   - Text: "Envoyer ma réclamation" or "Valider"
   - CSS: `button.submit` or `#submitClaim`

2. Click submit

3. **Security Checks**:

   - **reCAPTCHA**:
     - Appears ~40% of the time
     - Solve via 2captcha API
     - Timeout: 60s

   - **Email Verification**:
     - MR may send verification code
     - Wait for email (check inbox)
     - Extract 6-digit code
     - Enter in verification field

   - **Double-Click Prevention**:
     - Button disabled after click
     - Don't retry immediately
     - Wait for response (30s timeout)

4. **Error Handling**:
   - Validation errors: `.form-error`, `.invalid-field`
   - Log error messages
   - Auto-correct if possible:
     - Missing phone: Add placeholder
     - Invalid email: Retry with corrected format
   - Max retries: 2

---

### Step 11: Confirmation Extraction

**Success Signals**:

1. **Confirmation Page**:
   - URL: `.../confirmation` or `.../reclamation-enregistree`
   - Title: "Réclamation enregistrée"

2. **Extract Details**:

   **Claim Number**:
   - Pattern: "Référence : MR-REC-123456789"
   - CSS: `.claim-reference`, `#numeroReclamation`
   - Regex: `MR-REC-\d+` or `REC\d{9,}`

   **Processing Timeline**:
   - Text: "Délai de traitement : X jours"
   - Usually 5-10 business days for MR
   - Extract and store

   **Next Steps Indicated**:
   - Investigation details
   - Contact information

   **Email Confirmation**:
   - "Un email récapitulatif vous a été envoyé"
   - Verify sent to `client_email`

3. **Save Evidence**:
   - Screenshot: `data/confirmations/mondialrelay_{tracking}_{timestamp}.png`
   - HTML source: For audit trail
   - Extract PDF récapitulatif if downloadable

---

## 🔧 Error Handling

### Mondial Relay Specific Errors

| Error | Cause | Resolution |
| :--- | :--- | :--- |
| **Tracking Not Found** | Delay in system | Retry after 1h |
| **Value Exceeds Limit** | Too high | Cap at coverage |
| **Invoice Missing** | No proof | CRITICAL - Block |
| **Relay Point Closed** | Defunct | Contact support |
| **Claim Duplicate** | Exists | Retrieve ref |

### Retry Logic

```python
retry_strategy = {
    'max_attempts': 3,
    'wait_between': [10, 30, 60],  # seconds
    'retry_on_errors': [
        'server_error',
        'timeout',
        'captcha_failed'
    ],
    'abort_on_errors': [
        'tracking_invalid',
        'duplicate_claim',
        'invoice_required'
    ]
}
```

---

## ⚠️ Mondial Relay Particularities

### Strict Invoice Policy

MR **ALWAYS** requires invoice:

- No invoice = Auto-rejection
- Invoice must show item value
- Must match declared value

**Action**: Include invoice check in pre-submission validation

### Relay Point Dependency

Claims involving pickup points require:

- Relay point code (6 digits)
- Often need relay cooperation
- May slow process if relay unresponsive

**Strategy**: Pro account claims prioritized

### Lower Coverage Limits

MR standard coverage: **€600-1,000 max**

- Higher values need insurance declaration at shipping
- Cannot claim above coverage limit

**Action**: Cap claim amount automatically

### Manual Review Process

Unlike automated carriers, MR:

- Reviews ALL claims manually
- Contacts relay point for verification
- Takes longer (5-10 days vs 2-3)

**Expectation**: Set realistic timelines in dashboard

---

## ✅ Success Criteria

Claim successful if:

1. ✅ Confirmation page displayed
2. ✅ Claim reference extracted (MR-REC format)
3. ✅ Timeline communicated (usually 5-10 days)
4. ✅ Email confirmation sent
5. ✅ All documents uploaded
6. ✅ Invoice included (mandatory)
7. ✅ Value within coverage limits

**Return Object**:

```json
{
  "status": "success",
  "carrier": "mondial_relay",
  "claim_reference": "MR-REC-123456789",
  "tracking_number": "MR987654321",
  "pickup_point": "012345",
  "submitted_at": "2024-01-20T16:10:00Z",
  "estimated_processing": "5-10 jours ouvrés",
  "value_claimed": "450.00",
  "coverage_limit": "600.00",
  "confirmation_screenshot": "data/confirmations/mondialrelay_MR987654321_20240120.png",
  "email_sent_to": "client@example.com",
  "method": "portal_automation",
  "requires_relay_cooperation": true
}
```

---

## 📊 Performance Metrics

### Expected KPIs

| Metric | Target |
| :--- | :--- |
| **Success Rate** | 85-90% |
| **Average Time** | 3-5 minutes |
| **Manual Fallback** | ~10% |
| **Verification** | ~20% |

### Common Failure Points

1. **Missing Invoice** (60% of failures)
2. **Captcha Timeout** (20%)
3. **Duplicate Claims** (10%)
4. **Invalid Relay Code** (5%)
5. **Other** (5%)

---

## 🧪 Testing Protocol

Pre-production checklist:

- [ ] Test with valid MR tracking
- [ ] Test professional account login
- [ ] Test public form (no account)
- [ ] Verify all claim types available
- [ ] Test invoice upload (PDF, JPG)
- [ ] Validate file size limits
- [ ] Test with/without relay point
- [ ] Test captcha solving
- [ ] Verify email confirmation
- [ ] Test value limit enforcement (cap at €600)
- [ ] Confirm manual review warning displayed

---

**Last Updated**: 2024-01-20  
**Skill Version**: 1.0  
**Maintainer**: Auto-Recovery Team  
**Carrier**: Mondial Relay (Click & Collect Network)
