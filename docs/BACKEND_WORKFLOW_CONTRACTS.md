# AdvantaIQ Backend Collaboration Contract: Advisor Workflow & Notes

**Document Status:** Proposed API Contracts for Member 1  
**Author:** Member 2 (Frontend Lead)  
**Date:** 2026-10-18  
**Target Backend Module:** `backend/app/routers/` & `backend/app/models/`  
**Current Implementation Status in Frontend:** Full UI workflow implemented with honest local demo fallback (`localStorage` key: `advantaiq_advisor_workflow_states`). Clearly marked in the UI as *"Session Local Storage (Demo)"*.

---

## 1. Executive Summary & Objective

In Member 2's final frontend implementation, AdvantaIQ provides advisors with:
1. **Client Review Modal with 3 Tabs:** Evidence & Diagnosis, Deterministic Review Brief, Advisor Actions & Notes.
2. **Advisor Notes:** Recording time-stamped meeting notes and rationale.
3. **Deferral Workflow:** Postponing action until a target date with an explicit reason (e.g., CPA tax-loss harvesting consultation).
4. **Insight Resolution:** Marking an item resolved with a required audit resolution summary.
5. **Deterministic Review Brief:** Generating grounded meeting briefing memos without LLM dependency.
6. **Workflow Filtering:** Filterable by `Open Action`, `Deferred`, `Resolved`, and `All Statuses`.

Currently, the backend only provides read-only endpoints:
- `GET /api/v1/health`
- `GET /api/v1/advisors/worklist`
- `GET /api/v1/clients`
- `GET /api/v1/clients/{id}`

To achieve full end-to-end multi-user persistence across machines without relying on browser `localStorage`, Member 1 should implement the three REST endpoints detailed below.

---

## 2. Shared Data Models (Pydantic / TypeScript Aligned)

### 2.1 Workflow Status Enum
```python
from enum import Enum

class WorkflowStatus(str, Enum):
    OPEN = "open"
    DEFERRED = "deferred"
    RESOLVED = "resolved"
```

### 2.2 Advisor Note Model
```python
from pydantic import BaseModel, Field
from datetime import datetime

class AdvisorNoteCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="Advisor note or meeting minutes")
    author: str = Field(default="Wealth Advisor", description="Advisor name or role")

class AdvisorNoteResponse(BaseModel):
    id: str = Field(..., description="Unique note identifier (e.g. note_1730000000_abc12)")
    clientId: str
    text: str
    createdAt: str  # ISO 8601 string
    author: str
```

### 2.3 Client Workflow State Model
```python
from typing import Optional, List
from pydantic import BaseModel, Field

class WorkflowStatusUpdateRequest(BaseModel):
    status: WorkflowStatus
    deferredUntil: Optional[str] = Field(None, description="ISO Date string (YYYY-MM-DD) if status is deferred")
    deferReason: Optional[str] = Field(None, description="Mandatory rationale if deferred")
    resolutionNote: Optional[str] = Field(None, description="Mandatory audit explanation if resolved")

class ClientWorkflowStateResponse(BaseModel):
    clientId: str
    status: WorkflowStatus
    deferredUntil: Optional[str] = None
    deferReason: Optional[str] = None
    resolvedAt: Optional[str] = None
    resolutionNote: Optional[str] = None
    notes: List[AdvisorNoteResponse] = []
    updatedAt: str  # ISO 8601 string
```

---

## 3. Proposed Backend REST Endpoints

### Endpoint 1: Get Client Workflow State & Notes
- **Method:** `GET`
- **Route:** `/api/v1/clients/{client_id}/workflow`
- **Description:** Retrieve the current workflow status, deferral/resolution details, and notes history for a given client.
- **Path Parameters:**
  - `client_id` (string, required): e.g., `cli_001`
- **Response 200 OK:**
```json
{
  "clientId": "cli_001",
  "status": "deferred",
  "deferredUntil": "2026-11-15",
  "deferReason": "Waiting for client CPA tax-loss harvesting review on capital gains budget",
  "resolvedAt": null,
  "resolutionNote": null,
  "notes": [
    {
      "id": "note_1792318000_x91kf",
      "clientId": "cli_001",
      "text": "Called Eleanor Vance regarding 14.2% equity drift. Rebalancing proposed for next Monday.",
      "createdAt": "2026-10-18T12:00:00Z",
      "author": "Lead Wealth Advisor"
    }
  ],
  "updatedAt": "2026-10-18T12:05:00Z"
}
```
- **Response 404 Not Found:**
```json
{
  "detail": "Client with ID cli_999 not found"
}
```

---

### Endpoint 2: Update Workflow Status (Open / Defer / Resolve)
- **Method:** `PATCH`
- **Route:** `/api/v1/clients/{client_id}/workflow/status`
- **Description:** Update a client's workflow state. Guarantees that the underlying portfolio urgency score, data freshness, and score drivers are **not modified** by advisor workflow transitions.
- **Request Body (JSON):**
```json
{
  "status": "deferred",
  "deferredUntil": "2026-11-15",
  "deferReason": "Waiting for CPA review on tax implications."
}
```
*Or for Resolution:*
```json
{
  "status": "resolved",
  "resolutionNote": "Executed 10% equity trim to short duration Treasuries. Rebalanced."
}
```
- **Validation Rules:**
  1. If `status == "deferred"`, `deferredUntil` must be a valid future ISO date, and `deferReason` must not be blank.
  2. If `status == "resolved"`, `resolutionNote` must not be blank.
  3. If `status == "open"`, `deferredUntil`, `deferReason`, `resolvedAt`, and `resolutionNote` should be cleared.
  4. Notes history must be preserved across all state transitions.
- **Response 200 OK:** Returns updated `ClientWorkflowStateResponse`.

---

### Endpoint 3: Create Advisor Note
- **Method:** `POST`
- **Route:** `/api/v1/clients/{client_id}/notes`
- **Description:** Append a new advisor note to the client's permanent record.
- **Request Body (JSON):**
```json
{
  "text": "Discussed Aspen vacation home closing timeline. Advised increasing liquidity by $50k.",
  "author": "Primary Advisor"
}
```
- **Response 201 Created:** Returns `AdvisorNoteResponse`.

---

## 4. Worklist Enrichment (Optional Performance Optimization)

In `GET /api/v1/advisors/worklist`, Member 1 may optionally enrich each item in the worklist with an embedded `workflowStatus` object:
```json
{
  "id": "ins_cli_001",
  "clientId": "cli_001",
  "clientName": "Eleanor Vance",
  "urgencyScore": 80,
  "urgencyLevel": "critical",
  "workflow": {
    "status": "open",
    "deferredUntil": null,
    "noteCount": 1
  }
}
```
The frontend already handles this smoothly whether provided directly or fetched on demand.

---

## 5. Safety, Compliance & Architecture Commitments

1. **Deterministic Briefs (No Third-Party AI API):** Review briefs are generated deterministically in `workflowService.ts` from verified client telemetry (asset drift, overdue days, cash drag). No financial or PII data is transmitted to an LLM or third-party service.
2. **Score Invariance:** Urgency score, score drivers, and client risk rankings are derived strictly from objective portfolio data and are invariant to whether an insight is Open, Deferred, or Resolved.
3. **Execution Safety:** Workflow notes and status changes do not execute trades, move funds, or alter custodial positions.
4. **Honest Labeling:** The frontend clearly informs the advisor:
   > *"Session Local Storage (Demo) — Notes and status updates are saved in your local browser storage for this hackathon evaluation."*
