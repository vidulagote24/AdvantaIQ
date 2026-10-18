"""Insight API Endpoints.

Handles insight queue retrieval, filtering, and advisor workflow actions (reviewed, deferred, dismissed, escalated, resolved).
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, status
from app.schemas import (
    InsightSchema,
    InsightStatusUpdateSchema,
    InsightStatusEnum
)
from app.data.repositories import client_repository

router = APIRouter(prefix="/insights", tags=["Insights"])

@router.get("", response_model=List[InsightSchema], summary="Get ranked insight queue")
def list_insights(
    sort: str = Query("priority", description="Sort order: 'priority' or 'created_at'"),
    severity: Optional[str] = Query(None, description="Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)"),
    type: Optional[str] = Query(None, description="Filter by type (GOAL_AT_RISK, ALLOCATION_DRIFT, etc.)"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (active, reviewed, etc.)")
):
    """Returns the prioritized insight queue across all clients.
    
    Each insight includes deterministic score components, underlying evidence items,
    data freshness indicators, and recommended review steps.
    """
    return client_repository.get_all_insights(
        sort=sort,
        severity=severity,
        type=type,
        status=status_filter
    )

@router.post("/{insight_id}/status", summary="Update insight workflow status")
def update_insight_status(insight_id: str, payload: InsightStatusUpdateSchema):
    """Transitions an insight's status (reviewed, deferred, dismissed, escalated, resolved).
    
    Maintains an audit trail of the action timestamp and reason.
    """
    # Verify insight exists
    all_insights = client_repository.get_all_insights()
    matching = [ins for ins in all_insights if ins.insight_id == insight_id]
    if not matching:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Insight with ID '{insight_id}' does not exist."
        )
        
    success = client_repository.update_insight_status(
        insight_id=insight_id,
        status=payload.status,
        reason=payload.reason
    )
    
    return {
        "insight_id": insight_id,
        "new_status": payload.status.value,
        "reason": payload.reason,
        "message": f"Insight status successfully updated to '{payload.status.value}'."
    }
