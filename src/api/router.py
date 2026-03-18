from fastapi import FastAPI, Header, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Any
from pydantic import BaseModel
from src.auth.api_key_manager import APIKeyManager
from src.database.database_manager import get_db_manager
from src.scrapers.ocr_processor import OCRProcessor
from src.email_service.email_sender import EmailSender, _get_smtp_settings
import logging

app = FastAPI(title="Refundly.ai Enterprise API", version="1.0.0")

# Allow requests from React dev server and possible production domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

key_manager = APIKeyManager()
logger = logging.getLogger(__name__)

class OrderSync(BaseModel):
    order_id: str
    carrier: str
    tracking_number: str
    amount: float
    currency: str = "EUR"

async def get_client_id(x_api_key: str = Header(...)):
    client_id = key_manager.verify_key(x_api_key)
    if not client_id:
        raise HTTPException(status_code=401, detail="Invalid or inactive API Key")
    return client_id

@app.get("/")
async def root():
    return {"message": "Welcome to Refundly.ai Enterprise API. Use X-API-Key header to authenticate."}

@app.post("/orders/sync")
async def sync_order(order: OrderSync, client_id: int = Depends(get_client_id)):
    """Synchronise une commande depuis un ERP externe."""
    # Simulation de stockage
    return {"status": "success", "order_id": order.order_id, "message": "Order scheduled for analysis"}

@app.get("/claims/{reference}")
async def get_claim_status(reference: str, client_id: int = Depends(get_client_id)):
    """Récupère l'état d'avancement d'un litige."""
    db = get_db_manager()
    claim = db.get_claim(claim_reference=reference)
    
    if not claim or claim['client_id'] != client_id:
        raise HTTPException(status_code=404, detail="Claim not found")
        
    return {
        "reference": claim['claim_reference'],
        "status": claim['status'],
        "recovered_amount": claim.get('accepted_amount', 0),
        "updated_at": claim['updated_at']
    }

# --- Onboarding Endpoints for React Frontend ---

@app.post("/api/onboarding/upload")
async def onboarding_upload_docs(file: UploadFile = File(...)):
    """Simulates OCR analysis via the existing OCRProcessor."""
    try:
        content = await file.read()
        ocr = OCRProcessor()
        
        # Determine the file extension
        filename = file.filename or "unknown.jpg"
        
        # We need a proper file-like object or bytes, OCRProcessor handles bytes if we write it temporarily or pass it directly.
        # Actually, extract_all_from_file handles standard file objects.
        # Let's save it to a temporary file for safety with OCR libraries that require paths
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            ext_text, _ = ocr.extract_all_from_file(tmp_path, filename)
            analysis = ocr.analyze_rejection_text(ext_text)
            
            # Simple heuristic for carrier from OCR string
            text_lower = ext_text.lower()
            carrier = "Inconnu"
            if "dpd" in text_lower: carrier = "DPD"
            elif "ups" in text_lower or "1z" in text_lower: carrier = "UPS"
            elif "colissimo" in text_lower or "la poste" in text_lower: carrier = "Colissimo"
            elif "chronopost" in text_lower: carrier = "Chronopost"
            
            return {
                "fileName": filename,
                "carrier": carrier,
                "reason": analysis.get("label_fr", "Automatique"),
                "advice": analysis.get("advice_fr", "Le document sera traité automatiquement.")
            }
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
                
    except Exception as e:
        logger.error(f"Error during OCR upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class OnboardingCompletePayload(BaseModel):
    name: str
    company: str
    email: str = "contact@example.com" # Added email to connect
    phone: Optional[str] = None
    platform: str
    storeName: str
    storeUrl: str
    apiKey: str
    iban: str
    bic: Optional[str] = None
    holder: str

@app.post("/api/onboarding/complete")
async def complete_onboarding(data: OnboardingCompletePayload):
    """Registers the finalized client data and sends Welcome email via Python EmailSender."""
    try:
        # Simulate registration via database save logic
        # Typically we would register the store and keys in the DB here...
        
        # Send welcome email using Python EmailSender logic
        cfg = _get_smtp_settings()
        sender = EmailSender(**cfg)
        
        client_name = data.name or data.company
        target_email = data.email 
        
        # If user submits the test form without modifying email, we provide a placeholder or skip
        if target_email:
            sender.send_welcome_email(
                to_email=target_email,
                client_name=client_name,
                dashboard_url="https://app.refundly.ai/dashboard"
            )
        
        return {"status": "success", "message": "Onboarding completed and email sent"}
    except Exception as e:
        logger.error(f"Error completing onboarding: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Dashboard & Auth Endpoints for React Frontend ---

class LoginPayload(BaseModel):
    email: str
    password: Optional[str] = None # Simplified auth for MVP

@app.post("/api/login")
async def login(data: LoginPayload):
    """Simple login endpoint using email for MVP."""
    db = get_db_manager()
    client = db.get_client(email=data.email)
    
    if not client:
        raise HTTPException(status_code=401, detail="Identifiants invalides ou utilisateur introuvable")
        
    return {
        "status": "success",
        "token": f"fake-jwt-token-{client['id']}",
        "user": {
            "id": client['id'],
            "name": client['full_name'],
            "email": client['email'],
            "company": client['company_name']
        }
    }

@app.get("/api/dashboard/metrics")
async def get_dashboard_metrics(email: str):
    """Fetch real dashboard metrics from the database."""
    db = get_db_manager()
    client = db.get_client(email=email)
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
        
    stats = db.get_business_analytics(client['id'])
    global_stats = stats.get('global', {})
    
    return {
        "recovered_amount": global_stats.get('total_volume_recovered', 0) or 0,
        "pending_claims": global_stats.get('total_claims', 0) - global_stats.get('accepted_count', 0) - global_stats.get('rejected_count', 0),
        "total_claims": global_stats.get('total_claims', 0)
    }

@app.get("/api/claims")
async def get_all_claims(email: str):
    """Fetch all claims for a client."""
    db = get_db_manager()
    client = db.get_client(email=email)
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
        
    claims = db.get_client_claims(client_id=client['id'])
    
    # Format claims for the frontend list
    formatted = []
    for c in claims:
        formatted.append({
            "id": c['id'],
            "reference": c['claim_reference'],
            "date": c['created_at'].split(" ")[0] if isinstance(c['created_at'], str) else c['created_at'].strftime("%Y-%m-%d"),
            "carrier": c['carrier'],
            "status": c['status'],
            "amount": c['amount_requested']
        })
        
    return formatted
