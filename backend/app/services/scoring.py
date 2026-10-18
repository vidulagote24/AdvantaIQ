from datetime import datetime, timezone
from typing import Tuple, List
from ..models.schemas import (
    ClientProfile,
    ScoreDriver,
    EvidenceMetric,
    AdvisorInsight,
    UrgencyLevel
)

# 100-Point Deterministic Multi-Signal Scoring Engine
# Maxima across the 5 categories sum to exactly 100:
# 1. Allocation Drift:      30 points
# 2. Goal Urgency & Funding: 30 points
# 3. Fiduciary Review:       20 points
# 4. Cash Drag / Liquidity:  10 points
# 5. Custodian Data Quality: 10 points
# Total Theoretical Max:    100 points

REFERENCE_DATE = datetime(2026, 10, 18, 0, 0, 0, tzinfo=timezone.utc)

def calculate_urgency_score(client: ClientProfile) -> Tuple[int, UrgencyLevel, List[ScoreDriver], List[EvidenceMetric], str, str, str]:
    """
    Calculates deterministic, auditable multi-signal urgency score (0-100) and drivers.
    Categories strictly sum to 100 max points:
    - Allocation Drift (Max 30)
    - Goal Urgency & Funding (Max 30)
    - Overdue Fiduciary Review (Max 20)
    - Cash Drag / Idle Liquidity (Max 10)
    - Data Quality & Custodian Freshness (Max 10)
    """
    drivers: List[ScoreDriver] = []
    evidence: List[EvidenceMetric] = []

    # 1. Allocation Drift (Max 30)
    p = client.portfolio
    drift_eq = abs(p.currentEquitiesPct - p.targetEquitiesPct)
    drift_fi = abs(p.currentFixedIncomePct - p.targetFixedIncomePct)
    max_drift = max(drift_eq, drift_fi)

    if max_drift >= 12.0:
        drift_pts = 30
        drift_reason = f"Severe allocation drift of {max_drift:.1f}% exceeds risk tolerance parameters"
    elif max_drift >= 8.0:
        drift_pts = 22
        drift_reason = f"Significant allocation drift of {max_drift:.1f}% requires rebalancing"
    elif max_drift >= 5.0:
        drift_pts = 15
        drift_reason = f"Moderate allocation drift of {max_drift:.1f}% beyond standard 5% tolerance"
    else:
        drift_pts = 0
        drift_reason = f"Portfolio allocation within acceptable tolerance ({max_drift:.1f}% max drift)"

    drivers.append(ScoreDriver(
        category="Allocation Drift",
        pointsAwarded=drift_pts,
        maxPoints=30,
        rationale=drift_reason
    ))

    if max_drift >= 5.0:
        evidence.append(EvidenceMetric(
            metricName="Asset Allocation Drift",
            observedValue=f"Equities: {p.currentEquitiesPct:.1f}% (Target {p.targetEquitiesPct:.1f}%), Drift: {p.currentEquitiesPct - p.targetEquitiesPct:+.1f}%",
            threshold="±5.0% tolerance band",
            triggerReason=drift_reason
        ))

    # 2. Goal Urgency & Funding (Max 30)
    g = client.primaryGoal
    if g.fundingStatus == "critical":
        if g.daysToDeadline <= 90:
            goal_pts = 30
            goal_reason = f"Critical goal '{g.title}' is underfunded with only {g.daysToDeadline} days remaining"
        else:
            goal_pts = 24
            goal_reason = f"Critical funding gap detected for '{g.title}'"
    elif g.fundingStatus == "underfunded":
        if g.daysToDeadline <= 180:
            goal_pts = 22
            goal_reason = f"Goal '{g.title}' underfunded with upcoming milestone in {g.daysToDeadline} days"
        else:
            goal_pts = 14
            goal_reason = f"Goal '{g.title}' behind target savings schedule"
    else:
        goal_pts = 0
        goal_reason = f"Goal '{g.title}' is on track ({g.fundingStatus})"

    drivers.append(ScoreDriver(
        category="Goal Milestones",
        pointsAwarded=goal_pts,
        maxPoints=30,
        rationale=goal_reason
    ))

    if goal_pts > 0:
        funding_pct = (g.currentAmount / g.targetAmount * 100) if g.targetAmount > 0 else 0
        evidence.append(EvidenceMetric(
            metricName="Goal Funding Status",
            observedValue=f"${g.currentAmount:,.0f} of ${g.targetAmount:,.0f} ({funding_pct:.0f}%), Deadline: {g.targetDate}",
            threshold="100% on-track target funding",
            triggerReason=goal_reason
        ))

    # 3. Overdue Fiduciary Review (Max 20)
    last_contact = datetime.fromisoformat(client.lastContactDate.replace("Z", "+00:00"))
    days_since_review = (REFERENCE_DATE.date() - last_contact.date()).days
    days_overdue = days_since_review - client.reviewCadenceDays

    if days_overdue > 180:
        review_pts = 20
        review_reason = f"Mandatory fiduciary review critically overdue by {days_overdue} days (Cadence: {client.reviewCadenceDays}d)"
    elif days_overdue > 60:
        review_pts = 15
        review_reason = f"Fiduciary review overdue by {days_overdue} days"
    elif days_overdue > 0:
        review_pts = 10
        review_reason = f"Client review overdue by {days_overdue} days past cadence"
    elif days_overdue == 0:
        review_pts = 10
        review_reason = f"Review schedule due today (Cadence: {client.reviewCadenceDays}d)"
    elif days_overdue >= -15:
        review_pts = 4
        review_reason = f"Scheduled review window approaching in {abs(days_overdue)} days"
    else:
        review_pts = 0
        review_reason = f"Review status current (last conducted {days_since_review} days ago)"

    drivers.append(ScoreDriver(
        category="Fiduciary Review",
        pointsAwarded=review_pts,
        maxPoints=20,
        rationale=review_reason
    ))

    if review_pts >= 10:
        evidence.append(EvidenceMetric(
            metricName="Advisor Review Cadence",
            observedValue=f"{days_since_review} days since last meeting (Cadence: {client.reviewCadenceDays} days)",
            threshold=f"{client.reviewCadenceDays} days maximum review interval",
            triggerReason=review_reason
        ))

    # 4. Cash Drag / Idle Liquidity (Max 10)
    cash_pct = p.currentCashPct
    target_cash = p.targetCashPct
    if cash_pct >= 20.0 and client.cashBalance > 100000:
        cash_pts = 10
        cash_reason = f"Excessive uninvested cash: {cash_pct:.1f}% (${client.cashBalance:,.0f}) creating significant drag"
    elif client.cashBalance >= 250000:
        cash_pts = 8
        cash_reason = f"Substantial uninvested cash reserves: ${client.cashBalance:,.0f} ({cash_pct:.1f}%) requires deployment strategy"
    elif (cash_pct - target_cash) >= 5.0 and client.cashBalance > 50000:
        cash_pts = 5
        cash_reason = f"Cash allocation exceeds target by {cash_pct - target_cash:.1f}% (${client.cashBalance:,.0f} unallocated)"
    else:
        cash_pts = 0
        cash_reason = f"Cash balance (${client.cashBalance:,.0f}, {cash_pct:.1f}%) within operational policy"

    drivers.append(ScoreDriver(
        category="Cash Drag",
        pointsAwarded=cash_pts,
        maxPoints=10,
        rationale=cash_reason
    ))

    if cash_pts > 0:
        evidence.append(EvidenceMetric(
            metricName="Uninvested Cash Drag",
            observedValue=f"${client.cashBalance:,.0f} ({cash_pct:.1f}% of AUM)",
            threshold=f"Target: {target_cash:.1f}%",
            triggerReason=cash_reason
        ))

    # 5. Data Quality & Sync Freshness (Max 10)
    dq = client.dataQuality
    if dq.feedStatus != "active" or dq.daysSinceSync > 14:
        data_pts = 10
        data_reason = f"Data feed {dq.feedStatus}; custodian sync delayed by {dq.daysSinceSync} days"
    elif dq.daysSinceSync > 5 or dq.hasMissingCostBasis:
        data_pts = 5
        data_reason = f"Data sync delayed ({dq.daysSinceSync}d) or incomplete cost basis"
    else:
        data_pts = 0
        data_reason = "Custodian feed healthy and synchronised"

    drivers.append(ScoreDriver(
        category="Data Freshness",
        pointsAwarded=data_pts,
        maxPoints=10,
        rationale=data_reason
    ))

    if data_pts > 0:
        evidence.append(EvidenceMetric(
            metricName="Custodian Data Freshness",
            observedValue=f"{dq.daysSinceSync} days since sync (Status: {dq.feedStatus})",
            threshold="Sync within 2 days",
            triggerReason=data_reason
        ))

    # Calculate Total (Category Maxima sum: 30 + 30 + 20 + 10 + 10 = 100)
    total_score = min(100, max(0, drift_pts + goal_pts + review_pts + cash_pts + data_pts))

    if total_score >= 80:
        level: UrgencyLevel = "critical"
    elif total_score >= 60:
        level = "high"
    elif total_score >= 35:
        level = "medium"
    else:
        level = "low"

    # Determine Primary Category & Summary
    highest_driver = max(drivers, key=lambda d: d.pointsAwarded)
    primary_category = highest_driver.category

    if primary_category == "Allocation Drift":
        summary = f"Allocation drift of {max_drift:.1f}% detected; portfolio rebalancing required."
        action = "Review portfolio drift analysis and prepare tax-loss harvested rebalance proposal."
    elif primary_category == "Goal Milestones":
        summary = f"Goal '{g.title}' is {g.fundingStatus} with {g.daysToDeadline} days remaining."
        action = "Conduct goal feasibility simulation and discuss contribution adjustment."
    elif primary_category == "Fiduciary Review":
        summary = f"Annual fiduciary review is overdue by {days_overdue} days."
        action = "Initiate advisor outreach and generate pre-meeting client briefing memo."
    elif primary_category == "Cash Drag":
        summary = f"Elevated cash allocation of {cash_pct:.1f}% (${client.cashBalance:,.0f}) creating drag."
        action = "Propose dollar-cost averaging plan or yield-enhancement deployment for excess liquidity."
    else:
        summary = f"Portfolio review indicates stable alignment; data sync freshness: {dq.daysSinceSync}d."
        action = "Maintain standard monitoring and verify next scheduled contact."

    return total_score, level, drivers, evidence, primary_category, summary, action