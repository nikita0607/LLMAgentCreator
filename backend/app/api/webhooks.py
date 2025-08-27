from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.webhook import call_webhook

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

class WebhookRequest(BaseModel):
    url: str
    payload: dict

@router.post("/call")
def call_hook(req: WebhookRequest):
    try:
        response = call_webhook(req.url, req.payload)
        return {"status": "ok", "response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))