"""Client API Endpoints.

Handles client listing, detailed client profiles, advisor briefs, and advisor notes.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, status
from app.schemas import (
    ClientListResponse,
    ClientDetailSchema,
    AdvisorBriefSchema,
    AdvisorNoteSchema,
    AdvisorNoteCreateSchema
)
from app.data.repositories import client_repository

router = APIRouter(prefix="/clients", tags=["Clients"])

@router.get("", response_model=ClientListResponse, summary="List ranked clients with review priority")
def list_clients(
    search: Optional[str] = Query(None, description="Search by client name or ID"),
    risk_profile: Optional[str] = Query(None, description="Filter by risk profile (CONSERVATIVE, MODERATE, GROWTH, AGGRESSIVE)"),
    severity: Optional[str] = Query(None, description="Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)"),
    limit: int = Query(50, ge=1, le=200, description="Page limit"),
    offset: int = Query(0, ge=0, description="Offset")
):
    """Returns clients ranked deterministically by priority score.
    
    Includes goal progress, data freshness, active insight count, and primary concern.
    """
    summaries = client_repository.get_all_clients_summary(
        search=search,
        risk_profile=risk_profile,
        severity=severity
    )
    total_count = len(summaries)
    paginated = summaries[offset:offset + limit]
    as_of = paginated[0].data_as_of if paginated else "2026-03-31"
    
    return ClientListResponse(
        clients=paginated,
        total_count=total_count,
        data_as_of=as_of
    )

@router.get("/{client_id}", response_model=ClientDetailSchema, summary="Get full client profile and analytics")
def get_client(client_id: str):
    """Returns detailed client profile, portfolio holdings, goal trajectory, historical performance,
    benchmark alignment, advice history, and verified evidence warnings.
    """
    detail = client_repository.get_client_detail(client_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client '{client_id}' not found in portfolio database."
        )
    return detail

@router.get("/{client_id}/brief", response_model=AdvisorBriefSchema, summary="Generate evidence-backed advisor brief")
def get_client_brief(client_id: str):
    """Produces a synthesized advisor brief draft for client review meetings.
    
    Includes executive summary, goal trajectory, benchmark comparison, allocation drift,
    confidence warnings, and suggested non-prescriptive review questions.
    """
    brief = client_repository.get_client_brief(client_id)
    if not brief:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client '{client_id}' not found. Cannot generate advisor brief."
        )
    return brief

@router.post("/{client_id}/notes", response_model=AdvisorNoteSchema, status_code=status.HTTP_201_CREATED, summary="Add advisor note or meeting summary")
def add_client_note(client_id: str, note_in: AdvisorNoteCreateSchema):
    """Saves an advisor-entered meeting summary or qualitative note with persistent audit trail.
    
    Does not expose unapproved raw transcripts.
    """
    raw = client_repository.get_raw_client(client_id)
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client '{client_id}' not found. Cannot attach advisor note."
        )
    return client_repository.add_client_note(
        client_id=client_id,
        author=note_in.author,
        content=note_in.content,
        category=note_in.category
    )
