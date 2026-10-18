from typing import List, Optional, Literal
from pydantic import BaseModel, Field

UrgencyLevel = Literal['critical', 'high', 'medium', 'low']
WorkflowStatus = Literal['open', 'deferred', 'resolved']

class EvidenceMetric(BaseModel):
    metricName: str
    observedValue: str
    threshold: str
    triggerReason: str

class ScoreDriver(BaseModel):
    category: str
    pointsAwarded: int
    maxPoints: int
    rationale: str

class PortfolioSummary(BaseModel):
    asOfDate: str
    targetEquitiesPct: float
    currentEquitiesPct: float
    targetFixedIncomePct: float
    currentFixedIncomePct: float
    targetCashPct: float
    currentCashPct: float
    driftAlertTriggered: bool

class GoalSummary(BaseModel):
    id: str
    title: str
    targetAmount: float
    currentAmount: float
    targetDate: str
    fundingStatus: str
    daysToDeadline: int

class DataQualitySummary(BaseModel):
    feedStatus: str
    daysSinceSync: int
    hasMissingCostBasis: bool

class ClientProfile(BaseModel):
    id: str
    fullName: str
    email: str
    phone: str
    age: int
    riskTolerance: str
    totalAum: float
    cashBalance: float
    advisorAssignedId: str
    lastContactDate: str
    reviewCadenceDays: int
    tags: List[str] = []
    portfolio: PortfolioSummary
    primaryGoal: GoalSummary
    dataQuality: DataQualitySummary

class AdvisorInsight(BaseModel):
    id: str
    clientId: str
    clientName: str
    totalAum: float
    cashBalance: float
    riskTolerance: str
    urgencyScore: int = Field(ge=0, le=100)
    urgencyLevel: UrgencyLevel
    primaryCategory: str
    summary: str
    detectedAt: str
    daysSinceLastReview: int
    isReviewOverdue: bool
    dataFreshnessDays: int
    scoreDrivers: List[ScoreDriver]
    evidence: List[EvidenceMetric]
    suggestedAction: str

class WorklistResponse(BaseModel):
    totalCount: int
    criticalCount: int
    highCount: int
    mediumCount: int
    lowCount: int
    items: List[AdvisorInsight]

class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    timestamp: str

# ---------------------------------------------
# Advisor CRM Workflow & Notes Schemas
# (Specified in docs/BACKEND_WORKFLOW_CONTRACTS.md)
# ---------------------------------------------

class AdvisorNoteCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="Advisor note or meeting minutes")
    author: str = Field(default="Wealth Advisor", description="Advisor name or role")

class AdvisorNoteResponse(BaseModel):
    id: str
    clientId: str
    text: str
    createdAt: str
    author: str

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
    updatedAt: str
