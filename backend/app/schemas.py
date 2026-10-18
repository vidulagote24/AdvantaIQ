from __future__ import annotations
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field

class SeverityEnum(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

class ConfidenceEnum(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class InsightStatusEnum(str, Enum):
    ACTIVE = "active"
    REVIEWED = "reviewed"
    DEFERRED = "deferred"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"
    RESOLVED = "resolved"

class InsightTypeEnum(str, Enum):
    GOAL_AT_RISK = "GOAL_AT_RISK"
    ALLOCATION_DRIFT = "ALLOCATION_DRIFT"
    PERSISTENT_UNDERPERFORMANCE = "PERSISTENT_UNDERPERFORMANCE"
    REVIEW_OVERDUE = "REVIEW_OVERDUE"
    DATA_VERIFICATION_REQUIRED = "DATA_VERIFICATION_REQUIRED"

class ScoreComponents(BaseModel):
    goal_urgency: float = Field(..., ge=0.0, le=100.0, description="Normalized score 0-100 for goal shortfall/urgency")
    deviation_persistence: float = Field(..., ge=0.0, le=100.0, description="Normalized score 0-100 for benchmark gap & persistence")
    allocation_mismatch: float = Field(..., ge=0.0, le=100.0, description="Normalized score 0-100 for portfolio drift vs target")
    review_recency: float = Field(..., ge=0.0, le=100.0, description="Normalized score 0-100 for time since last review")
    evidence_quality: float = Field(..., ge=0.0, le=100.0, description="Normalized score 0-100 for data completeness & freshness")

class EvidenceItem(BaseModel):
    metric_name: str
    observed_value: Optional[Any] = None
    baseline_value: Optional[Any] = None
    unit: str = ""
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    source_field: str
    source_date: Optional[str] = None
    confidence: str = "HIGH"
    calculation_explanation: str

class HoldingSchema(BaseModel):
    asset_id: str
    asset_name: str
    category: str  # Equity, Fixed Income, Cash, Alternative, Real Estate
    market_value: float
    allocation_pct: float
    risk_tags: List[str] = Field(default_factory=list)

class PortfolioSnapshotSchema(BaseModel):
    valuation_date: str
    total_value: float
    cash_balance: float
    holdings: List[HoldingSchema]
    target_allocation: Optional[Dict[str, float]] = None
    is_stale: bool = False
    data_warnings: List[str] = Field(default_factory=list)

class PerformancePeriodSchema(BaseModel):
    period_label: str  # e.g., 1M, 3M, 6M, 1Y
    period_start: str
    period_end: str
    client_return_pct: float
    benchmark_id: Optional[str] = None
    benchmark_name: Optional[str] = None
    benchmark_return_pct: Optional[float] = None
    performance_gap_pp: Optional[float] = None
    aligned: bool = True

class AdviceRecordSchema(BaseModel):
    advice_id: str
    recording_date: str
    advice_text: str
    expected_outcome: Optional[str] = None
    review_horizon_days: int = 180
    target_allocation: Optional[Dict[str, float]] = None
    status: str = "recorded"
    follow_through_notes: Optional[str] = None

class GoalSchema(BaseModel):
    goal_name: str
    goal_amount: float
    goal_date: str
    current_value: float
    progress_pct: float
    modeled_target_value: Optional[float] = None
    trajectory_status: str  # ON_TRACK, BEHIND, CRITICAL_SHORTFALL, UNKNOWN, EXPIRED
    shortfall_amount: Optional[float] = None
    shortfall_pct: Optional[float] = None
    monthly_contribution_assumed: float = 0.0
    assumed_return_rate_pct: float = 6.0
    assumptions_description: str

class AdvisorNoteCreateSchema(BaseModel):
    author: str = "Financial Advisor"
    content: str
    category: str = "PORTFOLIO_REVIEW"

class AdvisorNoteSchema(BaseModel):
    note_id: str
    client_id: str
    author: str
    content: str
    category: str
    created_at: str

class InsightStatusUpdateSchema(BaseModel):
    status: InsightStatusEnum
    reason: Optional[str] = None

class InsightSchema(BaseModel):
    insight_id: str
    client_id: str
    client_name: str
    type: InsightTypeEnum
    headline: str
    what_changed: str
    why_it_matters: str
    severity: SeverityEnum
    score: float
    score_components: ScoreComponents
    evidence: List[EvidenceItem]
    metric_values: Dict[str, Any]
    confidence: ConfidenceEnum
    confidence_reason: str
    data_as_of: str
    suggested_review: str
    status: InsightStatusEnum = InsightStatusEnum.ACTIVE
    created_at: str

class ClientSummarySchema(BaseModel):
    client_id: str
    display_name: str
    risk_profile: str
    total_portfolio_value: float
    goal_name: str
    goal_progress_pct: float
    priority_score: float
    severity: SeverityEnum
    confidence_level: ConfidenceEnum
    last_review_date: str
    days_since_review: int
    data_as_of: str
    active_insight_count: int
    primary_concern: str
    planted_scenario_id: Optional[str] = None

class ClientListResponse(BaseModel):
    clients: List[ClientSummarySchema]
    total_count: int
    data_as_of: str

class ClientDetailSchema(BaseModel):
    client_id: str
    display_name: str
    risk_profile: str
    data_as_of: str
    last_review_date: str
    days_since_review: int
    portfolio: PortfolioSnapshotSchema
    goal: GoalSchema
    historical_performance: List[PerformancePeriodSchema]
    advice_history: List[AdviceRecordSchema]
    notes: List[AdvisorNoteSchema]
    insights: List[InsightSchema]
    priority_score: float
    score_components: ScoreComponents
    severity: SeverityEnum
    confidence_level: ConfidenceEnum
    confidence_reason: str
    data_warnings: List[str]
    suggested_review: str
    planted_scenario_id: Optional[str] = None

class AdvisorBriefSchema(BaseModel):
    client_id: str
    client_name: str
    brief_date: str
    draft_notice: str = "DRAFT FOR ADVISOR REVIEW — Decision support only. Not an autonomous recommendation."
    executive_summary: str
    goal_summary: Dict[str, Any]
    performance_summary: Dict[str, Any]
    allocation_summary: Dict[str, Any]
    advice_follow_through: Dict[str, Any]
    data_freshness_and_confidence: Dict[str, Any]
    suggested_review_questions: List[str]
    evidence: List[EvidenceItem]

class BaselineMetricComparison(BaseModel):
    metric_name: str
    proposed_engine_value: float
    return_only_baseline_value: float
    delta_percentage_points: float
    explanation: str

class EvaluationSummarySchema(BaseModel):
    total_clients_evaluated: int
    total_ground_truth_relevant: int
    proposed_engine: Dict[str, float]
    return_only_baseline: Dict[str, float]
    comparisons: List[BaselineMetricComparison]
    planted_scenarios_evaluated: List[Dict[str, Any]]
    methodology_notes: str
    limitations: List[str]
