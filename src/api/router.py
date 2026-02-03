
from fastapi import FastAPI, Header, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
from src.auth.api_key_manager import APIKeyManager
from src.database.database_manager import get_db_manager

app = FastAPI(title="Refundly.ai Enterprise API", version="1.0.0")
key_manager = APIKeyManager()

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
