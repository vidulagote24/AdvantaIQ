import uuid
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException, status
from datetime import datetime, timezone

from ...models.schemas import (
    HealthResponse,
    WorklistResponse,
    AdvisorInsight,
    ClientProfile,
    AdvisorNoteCreate,
    AdvisorNoteResponse,
    WorkflowStatusUpdateRequest,
    ClientWorkflowStateResponse,
    WorkflowStatus
)
from ...services.data_loader import get_worklist_response, load_clients
from ...data.repositories import client_repository

router = APIRouter()

def _get_workflow_connection():
    conn = client_repository._get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS client_workflows (
            client_id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            deferred_until TEXT,
            defer_reason TEXT,
            resolved_at TEXT,
            resolution_note TEXT,
            updated_at TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn

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

# -------------------------------------------------------------
# Advisor CRM Workflow & Notes Endpoints
# Implements the collaboration contract from docs/BACKEND_WORKFLOW_CONTRACTS.md
# -------------------------------------------------------------

@router.get('/clients/{client_id}/workflow', response_model=ClientWorkflowStateResponse, tags=['Advisor Workflow'])
def get_client_workflow(client_id: str):
    """Retrieve the current workflow status, deferral/resolution details, and notes history for a client."""
    now_iso = datetime.now(timezone.utc).isoformat()
    with _get_workflow_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM client_workflows WHERE client_id = ?", (client_id,))
        row = cursor.fetchone()

        # Fetch notes for client
        cursor.execute("""
            SELECT note_id as id, client_id as clientId, content as text, created_at as createdAt, author
            FROM advisor_notes
            WHERE client_id = ?
            ORDER BY created_at DESC
        """, (client_id,))
        notes = [AdvisorNoteResponse(**dict(n)) for n in cursor.fetchall()]

        if not row:
            return ClientWorkflowStateResponse(
                clientId=client_id,
                status="open",
                notes=notes,
                updatedAt=now_iso
            )

        return ClientWorkflowStateResponse(
            clientId=row["client_id"],
            status=row["status"],
            deferredUntil=row["deferred_until"],
            deferReason=row["defer_reason"],
            resolvedAt=row["resolved_at"],
            resolutionNote=row["resolution_note"],
            notes=notes,
            updatedAt=row["updated_at"]
        )

@router.patch('/clients/{client_id}/workflow/status', response_model=ClientWorkflowStateResponse, tags=['Advisor Workflow'])
def update_client_workflow_status(client_id: str, payload: WorkflowStatusUpdateRequest):
    """Update a client's workflow state (open, deferred, resolved) with audit trail."""
    now_iso = datetime.now(timezone.utc).isoformat()

    # Validation rules specified in docs/BACKEND_WORKFLOW_CONTRACTS.md
    if payload.status == "deferred":
        if not payload.deferReason or not payload.deferReason.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Deferral reason is mandatory when deferring a client review."
            )
    elif payload.status == "resolved":
        if not payload.resolutionNote or not payload.resolutionNote.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Resolution note is mandatory when marking a client review as resolved."
            )

    deferred_until = payload.deferredUntil if payload.status == "deferred" else None
    defer_reason = payload.deferReason if payload.status == "deferred" else None
    resolved_at = now_iso if payload.status == "resolved" else None
    resolution_note = payload.resolutionNote if payload.status == "resolved" else None

    with _get_workflow_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO client_workflows (
                client_id, status, deferred_until, defer_reason, resolved_at, resolution_note, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (client_id, payload.status, deferred_until, defer_reason, resolved_at, resolution_note, now_iso))

        # Audit log
        cursor.execute("""
            INSERT INTO audit_log (log_id, action, entity_type, entity_id, details)
            VALUES (?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            "UPDATE_WORKFLOW_STATUS",
            "CLIENT",
            client_id,
            f"Status changed to {payload.status}"
        ))

        conn.commit()

    return get_client_workflow(client_id)

@router.post('/clients/{client_id}/notes', response_model=AdvisorNoteResponse, status_code=status.HTTP_201_CREATED, tags=['Advisor Workflow'])
def add_v1_client_note(client_id: str, payload: AdvisorNoteCreate):
    """Append a new advisor note to the client's permanent record."""
    note_id = f"note_{int(datetime.now(timezone.utc).timestamp())}_{uuid.uuid4().hex[:5]}"
    now_iso = datetime.now(timezone.utc).isoformat()

    with _get_workflow_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO advisor_notes (note_id, client_id, author, content, category, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (note_id, client_id, payload.author, payload.text, "ADVISOR_MEETING_NOTE", now_iso))

        cursor.execute("""
            INSERT INTO audit_log (log_id, action, entity_type, entity_id, details)
            VALUES (?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            "ADD_ADVISOR_NOTE",
            "CLIENT",
            client_id,
            f"Note added by {payload.author}"
        ))

        conn.commit()

    return AdvisorNoteResponse(
        id=note_id,
        clientId=client_id,
        text=payload.text,
        createdAt=now_iso,
        author=payload.author
    )
