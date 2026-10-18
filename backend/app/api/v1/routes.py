from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException
from datetime import datetime, timezone

from ...models.schemas import HealthResponse, WorklistResponse, AdvisorInsight, ClientProfile
from ...services.data_loader import get_worklist_response, load_clients

router = APIRouter()

@router.get('/health', response_model=HealthResponse, tags=['System'])
def health_check():
    return HealthResponse(
        status='healthy',
        version='1.0.0-milestone1',
        environment='hackathon-local',
        timestamp=datetime.now(timezone.utc).isoformat()
    )

@router.get('/advisors/worklist', response_model=WorklistResponse, tags=['Advisor Worklist'])
def get_advisor_worklist(
    urgency: Optional[str] = Query(default='all', description='Filter by urgency: all, critical, high, medium, low')
):
    return get_worklist_response(urgency_filter=urgency)

@router.get('/clients', response_model=List[ClientProfile], tags=['Clients'])
def list_clients():
    return load_clients()

@router.get('/clients/{client_id}', response_model=ClientProfile, tags=['Clients'])
def get_client(client_id: str):
    clients = load_clients()
    for c in clients:
        if c.id == client_id:
            return c
    raise HTTPException(status_code=404, detail=f'Client {client_id} not found')
