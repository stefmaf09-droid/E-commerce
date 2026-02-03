---
name: Chronopost Claim Submission
description: Automatically navigate Chronopost portal and submit delivery claim
---

# Chronopost Claim Submission Skill

## 🎯 Objective

Automatically submit delivery dispute claims on the Chronopost professional portal without manual intervention.

## 📋 Prerequisites

Required information:

- `tracking_number`: Chronopost tracking number (e.g., "EC123456789FR")
- `claim_type`: Type of claim (retard/perdu/endommagé/pod_invalide)
- `claim_text`: Generated claim description
- `client_email`: Client email
- `client_name`: Client full name
- `order_value`: Shipment value in EUR
- `documents`: Supporting documents list

Optional:

- `chronopost_account`: Professional account credentials if available

## 🔄 Workflow Steps

### Step 1: Navigate to Professional Portal

```text
URL: https://www.chronopost.fr/fr/compte-pro
Alternative: https://www.chronopost.fr/fr/reclamations
```

**Actions**:

1. Open Chronopost professional portal
2. Wait for page load
3. Accept cookies/RGPD if prompted

**Success Criteria**: Portal page visible with login or claim option

---

### Step 2: Authentication

#### Option A: Professional Account Login

1. Click "Connexion Espace Pro"
2. Fill fields:
   - Login/Email: `chronopost_account.email`
   - Password: `chronopost_account.password`
3. Click "Se connecter"
4. Wait for dashboard redirect
5. Navigate to "Mes réclamations" or "Ouvrir une réclamation"

#### Option B: Guest Claim (Limited)

1. Click "Réclamation sans compte"
2. Fill tracking number: `tracking_number`
3. Fill email: `client_email`
4. Click "Rechercher mon envoi"

**Success Criteria**: Claim form accessible

---

### Step 3: Fill Tracking Information

**Form Fields**:

1. **Numéro d'envoi Chronopost**:
   - CSS: `input[name="tracking"]` or `#trackingNumber`
   - Value: `tracking_number`
   - Format: ECxxxxxxxxFR (13 chars)

2. **Date d'expédition**:
   - Auto-filled from tracking (verify)
   - Manual if needed: Extract from order metadata

3. **Type de service**:
   - Dropdown: Chronopost Express, Chronopost Relais, etc.
   - Auto-detect from tracking prefix if possible

---

### Step 4: Select Claim Type

**Claim Type Mapping**:

- `retard` → "Retard de livraison"
- `perdu` → "Colis perdu ou égaré"
- `endommagé` → "Marchandise endommagée"
- `pod_invalide` → "Contestation de livraison / POD"

**Actions**:

1. Locate dropdown: `select[name="claim_type"]` or `#typeReclamation`
2. Select appropriate option based on `claim_type`
3. Wait for additional fields to appear (dynamic form)

---

### Step 5: Provide Claim Details

**Sender Information** (if not auto-filled):

- Name: `client_name`
- Email: `client_email`
- Phone: Optional (use placeholder if required)
- Company: Extract from client profile if available

**Recipient Information**:

- Usually auto-filled from tracking
- Verify accuracy

**Claim Description**:

- CSS: `textarea[name="description"]` or `#claimDescription`
- Value: `claim_text`
- Max length: ~3000 characters
- Truncate if needed, keep legally important parts

**Financial Information**:

- **Valeur déclarée**: `order_value`
- **Montant réclamé**: Auto-calculated or manual
- **Frais de port**: Usually auto-filled from tracking

---

### Step 6: Upload Supporting Documents

**Upload Interface**:

1. Locate upload zone:
   - Button text: "Joindre des fichiers" or "Ajouter pièce jointe"
   - CSS: `input[type="file"]` or `.upload-zone`

2. **Required Documents** (Chronopost specific):
   - **Facture commerciale**: Invoice/proof of value (REQUIRED)
   - **POD contestée**: If disputing delivery proof
   - **Photos dommages**: If damaged claim
   - **Bordereau d'expédition**: Shipping label copy

3. Upload process:
   - For each document in `documents`:
     - Click upload button
     - Select file
     - Wait for upload bar completion
     - Verify file name appears in list

**File Requirements**:

- Formats: PDF, JPG, PNG
- Max size: 10MB per file
- Max files: Usually 5-10 files

---

### Step 7: Additional Information (Damage Specific)

If `claim_type == "endommagé"`:

**Damage Details**:

- Nature du dommage: Dropdown (cassé, mouillé, ouvert, etc.)
- Description détaillée: `damage_description`
- Constat fait par: Sélection (destinataire, transporteur, etc.)

**Packaging Condition**:

- État du colis: Checkbox options
  - [ ] Emballage déchiré
  - [ ] Carton écrasé
  - [ ] Colis ouvert
  - [ ] Scotch d'origine coupé

---

### Step 8: Review and Legal Confirmation

**Review Section**:

1. Scroll to summary/review area
2. Verify all information:

```python
validation_checks = {
    'tracking': verify_matches(tracking_number),
    'claim_type': verify_selected,
    'description': verify_not_empty,
    'documents': verify_min_count(1),
    'value': verify_numeric(order_value)
}
```

1. **Legal Checkboxes** (usually required):
   - [ ] "Je certifie l'exactitude des informations"
   - [ ] "J'ai lu et accepte les conditions de réclamation"
   - [ ] "J'autorise Chronopost à enquêter"

**Actions**:

- Check all required checkboxes
- CSS: `input[type="checkbox"][required]`

---

### Step 9: Submit Claim

**Submission Process**:

1. Locate submit button:
   - Text: "Valider ma réclamation" or "Envoyer"
   - CSS: `button[type="submit"]` or `.btn-submit`

2. Click submit

3. **Handle Security Measures**:
   - **Captcha** (if present):
     - Type: Usually reCAPTCHA v2
     - Solve via 2captcha API
     - Timeout: 60 seconds max

   - **Email Verification**:
     - Some claims require email confirmation
     - Check for message like "Un code a été envoyé à votre email"
     - Wait for email, extract code
     - Fill verification field

   - **SMS Verification** (rare):
     - If phone number required
     - May need manual intervention

4. **Error Handling**:
   - Form validation errors: `.error-message`, `.field-error`
   - Log specific errors
   - Retry with corrections if auto-fixable
   - Max 3 retries

5. Wait for confirmation (max 30s)

---

### Step 10: Extract Confirmation Details

**Success Indicators**:

1. **URL Change**:
   - Redirects to `/confirmation` or `/reclamation/success`

2. **Confirmation Message**:
   - Look for: "Votre réclamation a été enregistrée"
   - Confirmation banner visible

3. **Extract Key Data**:

   **Claim Reference**:
   - Pattern: "Numéro de dossier : CHR123456789"
   - CSS: `.claim-ref`, `#dossierNumber`
   - Regex: `CHR\d{9,}` or `\d{10,}`

   **Estimated Response Time**:
   - Text like "Réponse sous 5 jours ouvrés"
   - Extract and store

   **Email Confirmation**:
   - Message: "Un email récapitulatif a été envoyé"
   - Verify destination: `client_email`

4. **Capture Evidence**:
   - Full page screenshot
   - Save to: `data/confirmations/chronopost_{tracking}_{timestamp}.png`
   - Save HTML source for audit
   - Extract confirmation PDF if available

---

## 🔧 Error Handling

### Common Errors

| Error | Cause | Action |
| :--- | :--- | :--- |
| **Tracking Invalid** | Wrong format or not in system | Verify format ECxxxxxxxxFR, fail fast |
| **Document Upload Failed** | Size/format issue | Compress image, retry, skip non-critical |
| **Account Locked** | Too many attempts | Wait 15min, retry, or use guest |
| **Portal Under Maintenance** | 503/502 errors | Retry after 30min, max 3 times |
| **Claim Already Exists** | Duplicate submission | Check existing claim number, skip |
| **Missing Required Field** | Form validation | Auto-fill with placeholder/default |

### Retry Strategy

```python
retry_config = {
    'max_attempts': 3,
    'backoff': 'exponential',  # 5s, 15s, 45s
    'retry_on': [
        'network_timeout',
        'server_error_5xx',
        'captcha_timeout'
    ],
    'fail_fast_on': [
        'invalid_tracking',
        'authentication_failed',
        'account_suspended'
    ]
}
```

---

## ⚠️ Chronopost-Specific Considerations

### Professional Account Benefits

If using pro account:

- ✅ Pre-filled sender information
- ✅ Access to historical shipments
- ✅ Bulk claim submission possible
- ✅ Faster processing (SLA priority)
- ✅ Direct contact assigned agent

### Peak Hours to Avoid

Chronopost portal slower during:

- 10h-12h (morning peak)
- 14h-16h (afternoon peak)

**Strategy**: Schedule submissions for 8h-10h or 16h-18h

### Document Requirements Strictness

Chronopost is **strict** on documents:

- Invoice REQUIRED (not optional)
- Photos must show damage clearly
- POD must be high-resolution if contesting

**Fallback**: If documents insufficient, mark for manual review

---

## ✅ Success Criteria

Claim successful when **ALL** conditions met:

1. ✅ Confirmation page reached
2. ✅ Claim reference number extracted (CHR format)
3. ✅ Email confirmation displayed
4. ✅ Screenshot saved
5. ✅ All mandatory documents uploaded
6. ✅ No error messages remaining

**Return Object**:

```json
{
  "status": "success",
  "carrier": "chronopost",
  "claim_reference": "CHR1234567890",
  "tracking_number": "EC123456789FR",
  "submitted_at": "2024-01-20T16:05:00Z",
  "estimated_response": "5 jours ouvrés",
  "confirmation_screenshot": "data/confirmations/chronopost_EC123456789FR_20240120.png",
  "email_sent_to": "client@example.com",
  "method": "portal_automation"
}
```

---

## 📊 Metrics & Monitoring

### Track Performance

- **Success Rate**: Target 90%+
- **Average Time**: 2-4 minutes per claim
- **Captcha Frequency**: ~30% of submissions
- **Manual Intervention Rate**: <5%

### Error Distribution

Monitor most common failures:

1. Document upload failures (40%)
2. Captcha timeouts (25%)
3. Form validation errors (20%)
4. Session timeouts (10%)
5. Other (5%)

---

## 🧪 Testing Checklist

Before production:

- [ ] Test with real Chronopost tracking (EC format)
- [ ] Test professional account login
- [ ] Test guest flow (no account)
- [ ] Verify all claim types selectable
- [ ] Test document upload (PDF, JPG, PNG)
- [ ] Validate file size limits (10MB)
- [ ] Test captcha solving integration
- [ ] Verify email confirmation received
- [ ] Test error scenarios (invalid tracking, etc.)
- [ ] Confirm screenshot capture working

---

**Last Updated**: 2024-01-20  
**Skill Version**: 1.0  
**Maintainer**: Auto-Recovery Team  
**Carrier**: Chronopost (DPD Group)
