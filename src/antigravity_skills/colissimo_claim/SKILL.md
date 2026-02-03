---
name: Colissimo Claim Submission
description: Automatically navigate Colissimo portal and submit delivery claim
---

# Colissimo Claim Submission Skill

## 🎯 Objective

Automatically submit a delivery dispute claim on the Colissimo portal (La Poste) without any manual intervention.

## 📋 Prerequisites

Required information:

- `tracking_number`: Colissimo tracking number (e.g., "6A12345678901")
- `claim_type`: Type of claim (retard/perdu/endommagé/pod_invalide)
- `claim_text`: Generated claim text
- `client_email`: Client email address
- `client_name`: Client full name
- `order_value`: Value of the shipment in EUR
- `documents`: List of supporting documents to upload

Optional:

- `client_credentials`: If client has La Poste account (email/password)

## 🔄 Workflow Steps

### Step 1: Navigate to Claims Portal

```text
URL: https://www.laposte.fr/reclamation
```

**Actions**:

1. Open browser to claims page
2. Wait for page to fully load
3. Accept cookies if popup appears

**Success Criteria**: Page title contains "Réclamation"

---

### Step 2: Choose Authentication Method

**Decision Logic**:

- IF `client_credentials` provided → Use authenticated flow
- ELSE → Use guest flow (tracking number only)

#### Option A: Authenticated Flow

1. Click "Se connecter" button
2. Fill email field: `client_credentials.email`
3. Fill password field: `client_credentials.password`
4. Click "Connexion" submit button
5. Wait for redirect to account dashboard

#### Option B: Guest Flow

1. Click "Réclamation sans compte" or "Continuer sans compte"
2. Fill tracking number: `tracking_number`
3. Click "Rechercher" or "Continuer"

**Success Criteria**: Claims form becomes visible

---

### Step 3: Select Claim Type

**Form Fields**:

1. **Numéro de suivi**: `tracking_number` (if not already filled)

   - CSS Selector: `input[name="tracking"]` or `#tracking`

2. **Type de réclamation**: Select from dropdown

   - CSS Selector: `select[name="claim_type"]` or `#claim-type`
   - Mapping:
     - `retard` → "Retard de livraison"
     - `perdu` → "Colis perdu ou non reçu"
     - `endommagé` → "Colis endommagé"
     - `pod_invalide` → "Preuve de livraison contestée"

3. **Date d'expédition**: Auto-filled from tracking (verify)
   - If empty, extract from metadata

---

### Step 4: Fill Claim Details

**Text Areas**:

1. **Description du problème**:

   - CSS Selector: `textarea[name="description"]` or `#claim-description`
   - Fill with: `claim_text` (generated claim)
   - Character limit: Usually 2000-5000 chars (truncate if needed)

2. **Montant demandé**:

   - CSS Selector: `input[name="amount"]` or `#claim-amount`
   - Fill with: `order_value`
   - Format: "150.00" (two decimals, no currency symbol)

3. **Contact Details** (if not authenticated):

   - Name: `client_name`
   - Email: `client_email`
   - Phone: Optional (use placeholder if required)

---

### Step 5: Upload Supporting Documents

**Upload Flow**:

1. Locate upload button:
   - Text: "Joindre un fichier" or "Ajouter une pièce jointe"
   - CSS: `input[type="file"]` or button with upload icon

2. For each document in `documents`:

   - Click upload button
   - Select file from path
   - Wait for upload progress bar to complete
   - Verify file appears in attached files list

**Accepted Formats**: PDF, JPG, PNG (usually max 5MB per file)

**Required Documents**:

- POD image (if disputing delivery proof)
- Invoice or proof of value
- Photos of damage (if applicable)

---

### Step 6: Review and Confirm

**Actions**:

1. Scroll to review section
2. Verify all fields are correctly filled:

```python
checks = {
    'tracking_number': verify_text_matches,
    'claim_type': verify_selected_option,
    'description': verify_text_present,
    'amount': verify_number_format,
    'documents': verify_min_1_file_attached
}
```

1. Check the confirmation checkbox:
   - Text: "Je certifie l'exactitude des informations" or similar
   - CSS: `input[type="checkbox"][name="confirm"]`

---

### Step 7: Submit Claim

**Actions**:

1. Locate submit button:
   - Text: "Envoyer la réclamation" or "Valider"
   - CSS: `button[type="submit"]` or `.submit-btn`

2. Click submit button

3. **Handle Possible Challenges**:
   - **Captcha**: If presents
     - Type: reCAPTCHA v2 or hCaptcha
     - Strategy: Use 2captcha API
     - Wait for captcha solve (max 60s)

   - **Form Validation Errors**:
     - Look for error messages (CSS: `.error`, `.invalid-feedback`)
     - Log errors
     - Retry with corrected input if possible

   - **Network Timeout**:
     - Retry up to 3 times with exponential backoff
     - If still fails, mark as "manual_intervention_required"

4. Wait for confirmation page to load (max 30s)

---

### Step 8: Extract Confirmation

**Success Indicators**:

1. **Confirmation Page**:
   - URL changes to `/confirmation` or `/success`
   - Page title contains "Confirmation" or "Merci"

2. **Extract Data**:
   - **Claim Reference Number**:
     - Look for pattern: "Votre numéro de réclamation : XXXXXXXX"
     - CSS: `.claim-reference`, `#reference-number`
     - Regex: `\d{8,12}` or `REC-\d+`

   - **Email Confirmation**:
     - Text like "Un email de confirmation a été envoyé"
     - Verify email address matches `client_email`

3. **Take Screenshot**:
   - Full page screenshot of confirmation
   - Save to: `data/confirmations/{tracking_number}_{timestamp}.png`

4. **Save HTML**:
   - Full page HTML for audit trail
   - Save to: `data/confirmations/{tracking_number}_{timestamp}.html`

---

## 🔧 Error Handling

### Error Types

| Error | Action |
| :--- | :--- |
| **Portal Unavailable** (503, 500) | Retry after 5 min, max 3 attempts |
| **Tracking Not Found** | Verify tracking number format, fail fast |
| **Captcha Timeout** | Mark for manual review |
| **Upload Failed** | Retry individual file upload |
| **Session Expired** | Re-authenticate and resume |
| **Form Validation** | Log specific field errors, attempt auto-fix |

### Fallback Strategy

If automation fails after all retries:

1. Log detailed error report
2. Save current state (screenshot, HTML, form data)
3. Create manual task ticket:

   ```json
   {
     "task_type": "manual_claim_submission",
     "carrier": "colissimo",
     "tracking": "...",
     "reason": "...",
     "saved_state": "path/to/state.json",
     "priority": "high"
   }
   ```

4. Notify human operator
5. Return status: `{"status": "pending_manual", "task_id": "..."}`

---

## ✅ Success Criteria

Claim submission is considered **successful** when ALL of the following are true:

1. ✅ Confirmation page reached
2. ✅ Claim reference number extracted
3. ✅ Email confirmation message displayed
4. ✅ Screenshot saved
5. ✅ All documents uploaded successfully
6. ✅ No error messages present

**Return Value**:

```json
{
  "status": "success",
  "claim_reference": "REC12345678",
  "tracking_number": "6A12345678901",
  "submitted_at": "2024-01-20T15:45:00Z",
  "confirmation_screenshot": "data/confirmations/6A12345678901_20240120.png",
  "email_sent_to": "client@example.com"
}
```

---

## 📊 Metrics to Track

- **Success Rate**: % of claims successfully submitted
- **Average Time**: Time from start to confirmation
- **Captcha Frequency**: How often captcha appears
- **Manual Fallback Rate**: % requiring human intervention
- **Error Distribution**: Most common failure points

---

## 🔒 Security & Compliance

1. **Credentials**: Never log passwords; store encrypted only
2. **Screenshots**: Blur sensitive personal info if shared
3. **Data Retention**: Keep confirmations for 90 days minimum
4. **RGPD**: Ensure client consent for automated submission
5. **Audit Trail**: Full logs for regulatory compliance

---

## 🧪 Testing

### Test Cases

1. ✅ **Happy Path**: Standard claim with all docs → Success
2. ✅ **No Documents**: Claim without attachments → Should fail with clear error
3. ✅ **Invalid Tracking**: Wrong tracking number → Fail fast with user-friendly message
4. ✅ **Captcha Present**: Trigger captcha → Solve and proceed
5. ✅ **Network Failure**: Simulate timeout → Retry logic works
6. ✅ **Form Validation Error**: Missing required field → Auto-correction or clear error

### Manual Testing Checklist

Before deploying to production:

- [ ] Test with real Colissimo tracking number
- [ ] Verify email confirmation actually sent
- [ ] Test authenticated vs guest flow
- [ ] Validate all document types upload correctly
- [ ] Check character limits for text fields
- [ ] Confirm captcha solving works
- [ ] Test on different browsers (Chrome, Firefox)
- [ ] Verify mobile responsiveness of portal

---

**Last Updated**: 2024-01-20
**Skill Version**: 1.0
**Maintainer**: Auto-Recovery Team
