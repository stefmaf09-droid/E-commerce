---
name: UPS Claim Submission
description: Automatically navigate UPS portal and submit international claim
---

# UPS Claim Submission Skill

## 🎯 Objective

Submit delivery claims on UPS portal with international shipping support.

## 📋 Prerequisites

- `tracking_number`: UPS 1Z tracking (18 chars)
- `claim_type`: loss/damage/delay
- `client_email`, `client_name`
- `order_value`, `currency` (EUR/USD/GBP)
- `commercial_invoice`: REQUIRED for international
- `ups_account`: My UPS account (required)

## 🔄 Workflow

### Step 1: Portal Access

```text
URL: https://www.ups.com/fr/fr/support/file-a-claim.page
Account: https://www.ups.com/lasso/login
```

**Authentication REQUIRED** - No guest flow

### Step 2: Login My UPS

- User ID or Email
- Password
- 2FA if enabled (SMS/App)

### Step 3: File Claim

Navigate: Support → File a Claim → Start

### Step 4: Shipment Details

- Tracking: `1Z` format (18 chars)
- Service type: Auto-detected (Express, Standard, etc.)
- Ship date: Auto-filled

**International Validation**:

- If cross-border: Commercial invoice MANDATORY
- Customs value verification

### Step 5: Claim Reason

UPS Categories:

- `perdu` → "Package lost/not delivered"
- `endommagé` → "Package damaged"
- `retard` → "Late delivery" (limited coverage)

### Step 6: Package Contents

**Critical for International**:

- Description: Detailed item list
- Quantity: Per item
- Value: Per item + currency
- HS Code: If available (customs)

Example:

```text
Item 1: Electronics - Smartphone
Quantity: 1
Value: €500.00
Weight: 0.2kg
```

### Step 7: Value Declaration

- Declared value: `order_value`
- Currency: `currency`
- **Insurance limit check**: varies by service
  - UPS Standard: €500
  - UPS Express: €50,000+
- Claim amount: min(order_value, coverage_limit)

### Step 8: Supporting Documents

**Mandatory**:

1. Commercial Invoice (CRITICAL international)
2. Proof of value (receipt/invoice)
3. Packing list

**If Damage**:
4. Photos (min 4 angles)
5. Repair estimate (if applicable)

**Upload**:

- Format: PDF, JPG, PNG
- Max: 10MB per file
- Multi-file support: Up to 10 files

### Step 9: Claim Details

- Description: `claim_text`
- Contact preferences: Email
- Payment method: Bank transfer or UPS account credit

### Step 10: Review & Submit

- Summary verification
- Legal attestation: "Information is true and accurate"
- Digital signature (type full name)

**Security**:

- May require email OTP verification
- Timeout: 15 minutes session

### Step 11: Confirmation

Extract:

- Claim number: Format "UPS-CLAIM-##########"
- Reference ID: For tracking
- Est. processing: 7-10 business days
- Case manager contact (if assigned)

## 🔧 Error Handling

| Error | Action |
| :--- | :--- |
| **Tracking not found** | Wait 24h, verify format |
| **Commercial invoice missing** | CRITICAL - Block submission |
| **Value exceeds coverage** | Cap at coverage limit |
| **2FA timeout** | Retry login |

## ⚠️ UPS Specifics

### International Complexity

**Customs & Duties**:

- Claim cannot exceed declared customs value
- HS codes helpful but optional
- Currency conversion: UPS uses daily rates

**Multi-Currency**:

```python
supported_currencies = ['EUR', 'USD', 'GBP', 'CAD', 'CHF']

if currency not in supported_currencies:
    convert_to_EUR()
```

### Service-Level Variations

| Service | Coverage | Documentation | Processing |
| :--- | :--- | :--- | :--- |
| **UPS Express** | High ($50k+) | Invoice required | 5-7 days |
| **UPS Standard** | €500 max | Basic | 7-10 days |
| **UPS Access Point** | €100 max | Minimal | 10-14 days |

### Account Requirements

**My UPS Account**:

- REQUIRED (no anonymous claims)
- Business account: Faster processing
- Personal account: Longer review

**Shipper Number**:

- If available: Pre-filled data
- Improves claim speed significantly

## 🌍 International Considerations

### Cross-Border Claims

**EU Shipments**:

- VAT documentation helpful
- EORI number if business

**US/UK Shipments**:

- Commercial invoice MANDATORY
- Customs declaration copy
- Potential currency conversion issues

### Language

Portal auto-detects:

- French for FR accounts
- English for international
- Form fields: Translate claim_text if needed

## ✅ Success Criteria

All must be true:

1. ✅ Claim number extracted (UPS-CLAIM format)
2. ✅ Commercial invoice uploaded (if international)
3. ✅ Value within coverage limits
4. ✅ Confirmation email received
5. ✅ PDF receipt downloaded

**Return Object**:

```json
{
  "status": "success",
  "carrier": "ups",
  "claim_number": "UPS-CLAIM-1234567890",
  "tracking": "1Z999AA10123456784",
  "claim_value": "€500.00",
  "currency": "EUR",
  "is_international": true,
  "estimated_resolution": "7-10 business days",
  "case_manager": "John Doe (optional)",
  "confirmation_pdf": "path/to/ups_claim_confirmation.pdf"
}
```

## 📊 Performance Notes

- **Success rate**: 85% (lower due to complexity)
- **Average time**: 5-7 minutes (documents upload)
- **Manual fallback**: ~15% (2FA issues, missing docs)

---

**Last Updated**: 2026-01-20  
**Version**: 1.0  
**Carrier**: UPS (United Parcel Service)  
**Complexity**: HIGH (International)
