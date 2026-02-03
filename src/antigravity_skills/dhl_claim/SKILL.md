---
name: DHL Claim Submission
description: Automatically navigate DHL portal for Express and Parcel claims
---

# DHL Claim Submission Skill

## 🎯 Objective

Submit claims on DHL portal with support for both DHL Express and DHL Parcel services.

## 📋 Prerequisites

- `tracking_number`: DHL tracking (10-11 digits or AWB)
- `service_type`: "express" or "parcel"
- `claim_type`: loss/damage/delay
- `client_email`, `client_name`
- `order_value`, `currency`
- `dhl_account`: Optional but recommended
- `commercial_invoice`: Required if international

## 🔄 Workflow

### Step 1: Service Type Detection

**DHL has 2 distinct services**:

1. **DHL Express**:
   - Tracking: 10-digit AWB (Air Waybill)
   - International priority
   - Portal: <https://mydhl.express.dhl/fr/>  
   - Higher coverage limits

2. **DHL Parcel**:
   - Tracking: Varied format
   - Domestic/EU mainly
   - Portal: <https://www.dhl.fr/fr/particuliers.html>
   - Standard coverage

**Auto-detection logic**:

```python
if len(tracking) == 10 and tracking.isdigit():
    service = "express"
elif tracking.startswith("JJD"):
    service = "parcel"
else:
    # Ask user or analyze from order metadata
```

---

## 🚀 DHL Express Workflow

### Step 1 (Express): Portal Access

```text
URL: https://mydhl.express.dhl/fr/fr/assistance/reclamations.html
Login: https://mydhl.express.dhl
```

### Step 2: Authentication

**MyDHL Account**:

- Email/Username
- Password
- Optional: SMS verification

**Guest Flow**:

- Limited availability
- Requires AWB + reference

### Step 3: New Claim

Navigate: Customer Service → File a Claim

### Step 4: Shipment Details

- AWB Number: 10-digit tracking
- Ship date: Auto-filled from AWB
- Origin/Destination: Verified from system

### Step 5: Claim Type

DHL Express categories:

- `perdu` → "Shipment Lost"
- `endommagé` → "Shipment Damaged"
- `retard` → "Delivery Delay" (Time-Definite only)

### Step 6: Package Details

**For Each Package**:

- Description: Detailed contents
- Weight: kg
- Dimensions: cm (L x W x H)
- Value: Amount + Currency

**International**:

- Commercial invoice REQUIRED
- HS codes recommended
- Country of origin

### Step 7: Damage Details (if applicable)

- Nature of damage: Dropdown selection
- Extent: Partial or Total
- Photos: Min 6 required (all sides + damage close-up)
- Packaging intact? Yes/No

### Step 8: Claim Amount

- Declared value: From commercial invoice
- Currency: EUR, USD, GBP, etc.
- **Coverage limits**:
  - Standard: €25 per kg
  - Declared Value service: Up to €50,000+
- Claim amount: min(order_value, coverage)

### Step 9: Documents Upload

**Mandatory Express**:

1. Commercial invoice (REQUIRED)
2. Proof of value (receipt)
3. AWB copy
4. Photos (if damage)

**Optional**:

1. Packing list
2. Customs documents
3. Repair quote

Limits: 5MB/file, 10 files max

### Step 10: Contact & Payment

- Preferred contact: Email
- Payment method:
  - Credit to DHL account (faster)
  - Bank transfer
  - Check (slower)

### Step 11: Submit Express

- Digital signature
- Attestation of accuracy
- Submit claim

### Step 12: Confirmation Express

Extract:

- Claim reference: "DHL-EXP-########"
- Case number
- Processing time: 5-7 business days
- Case handler contact

---

## 📦 DHL Parcel Workflow

### Step 1 (Parcel): Portal Access

```text
URL: https://www.dhl.fr/fr/particuliers/assistance/reclamation.html
```

### Step 2: Claim Form

**Simpler Process**:

- No mandatory account
- Tracking + Email sufficient

### Step 3: Shipment Lookup

- Tracking number
- Email address
- Verification code (sent to email)

### Step 4: Parcel Claim Type

- Colis perdu
- Colis endommagé
- Retard livraison (limited)

### Step 5: Details

- Description: `claim_text` (1500 chars max)
- Value: `order_value`
- **Coverage**: €500 max standard

### Step 6: Documents Parcel

**Required**:

- Facture (invoice)
- Photos if damage

**Note**: Less stringent than Express

### Step 7: Submit Parcel

- Contact details
- Submit claim

### Step 8: Confirmation Parcel

Extract:

- Reference: "DHL-PAR-######"
- Response: 5-7 days
- Email confirmation

---

## 🔧 Error Handling

### Common Issues

| Error | Action |
| :--- | :--- |
| **AWB not found** | Wait 48h post-shipping |
| **Tracking invalid** | Verify format |
| **Invoice missing** | CRITICAL - Block |
| **Value exceeds limit** | Cap to coverage |
| **Photos insufficient** | Min 6 for Express, 2 for Parcel |

### Retry Logic

```python
retry_config = {
    'express': {
        'max_attempts': 3,
        'backoff': [30, 60, 120],  # seconds
        'retry_on': ['system_error', 'timeout']
    },
    'parcel': {
        'max_attempts': 2,
        'backoff': [15, 45],
        'retry_on': ['system_error']
    }
}
```

---

## ⚠️ DHL Specifics

### Express vs Parcel

| Feature | DHL Express | DHL Parcel |
| :--- | :--- | :--- |
| **Coverage** | €50k+ | €500 |
| **Processing** | 5-7 days | 5-10 days |
| **Invoice** | MANDATORY | Required |
| **Photos** | Min 6 | Min 2 |
| **International** | PRIMARY | Limited |
| **Account** | Recommended | Optional |

### International Shipping

**Customs Documents**:

- Commercial invoice (all international)
- Proforma invoice (if needed)
- Certificate of origin (some countries)

**Currency Handling**:

- Express: 130+ currencies supported
- Parcel: EUR/GBP mainly

### Service Detection Strategy

```python
def detect_dhl_service(tracking, order_data):
    # AWB format (10 digits)
    if re.match(r'^\d{10}$', tracking):
        return 'express'
    
    # Parcel patterns
    if tracking.startswith('JJD') or len(tracking) > 12:
        return 'parcel'
    
    # Fallback: Check order metadata
    if order_data.get('shipping_method'):
        if 'express' in order_data['shipping_method'].lower():
            return 'express'
    
    # Default: parcel (safer, lower requirements)
    return 'parcel'
```

---

## ✅ Success Criteria

### DHL Express

1. ✅ Claim ref format: DHL-EXP-########
2. ✅ Commercial invoice uploaded
3. ✅ Min 6 photos if damage
4. ✅ AWB verified in system
5. ✅ Case handler assigned

### DHL Parcel

1. ✅ Claim ref format: DHL-PAR-######
2. ✅ Invoice uploaded
3. ✅ Email confirmation received

**Return Object**:

```json
{
  "status": "success",
  "carrier": "dhl",
  "service_type": "express",  // or "parcel"
  "claim_reference": "DHL-EXP-12345678",
  "tracking": "9876543210",
  "claim_value": "€750.00",
  "currency": "EUR",
  "is_international": true,
  "estimated_resolution": "5-7 business days",
  "case_handler": "Maria Schmidt",
  "coverage_limit": "€50000",
  "confirmation_pdf": "path/to/dhl_claim_conf.pdf"
}
```

---

## 📊 Performance Metrics

### Expected KPIs

| Metric | Express | Parcel |
| :--- | :--- | :--- |
| **Success Rate** | 80% | 85% |
| **Avg Time** | 6-8 min | 3-4 min |
| **Manual Fallback** | 20% | 15% |
| **Invoice Requirement** | 100% | 95% |

---

**Last Updated**: 2026-01-20  
**Version**: 1.0  
**Carrier**: DHL (Express & Parcel)  
**Complexity**: HIGH (Dual service)
