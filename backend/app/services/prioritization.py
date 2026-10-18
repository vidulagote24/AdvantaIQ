"""Explainable Priority Scoring Service.

Implements the normalized 0-100 priority scoring engine with initial heuristic weights:
- Goal urgency: 25%
- Deviation magnitude & persistence: 25%
- Risk/allocation mismatch: 20%
- Time since last review: 15%
- Evidence quality / verification urgency: 15%

All component scores are fully visible, explainable, and derived from verified evidence.
Deterministic tie-breaking ensures strict reproducibility.
"""

from datetime import datetime, date
from typing import Dict, List, Any, Tuple
from app.config import settings
from app.schemas import ScoreComponents, SeverityEnum, ConfidenceEnum

def calculate_goal_urgency_score(goal_trajectory: Dict[str, Any]) -> Tuple[float, List[str]]:
    """Normalizes goal trajectory metrics to a 0-100 score."""
    signals: List[str] = []
    status = goal_trajectory.get("trajectory_status", "UNKNOWN")
    shortfall_pct = goal_trajectory.get("shortfall_pct") or 0.0
    shortfall_amt = goal_trajectory.get("shortfall_amount") or 0.0
    
    if status == "EXPIRED":
        score = 95.0
        signals.append(f"Goal target date has passed with shortfall of ${shortfall_amt:,.0f}")
    elif status == "CRITICAL_SHORTFALL":
        score = min(100.0, 80.0 + min(20.0, shortfall_pct))
        signals.append(f"Critical goal shortfall of {shortfall_pct:.1f}% (${shortfall_amt:,.0f}) vs modeled path")
    elif status == "BEHIND":
        score = min(74.0, 45.0 + (shortfall_pct / 20.0) * 29.0)
        signals.append(f"Goal trajectory is behind modeled path by {shortfall_pct:.1f}%")
    elif status == "ON_TRACK":
        score = 10.0
    else:  # UNKNOWN or INVALID
        score = 50.0
        signals.append("Goal trajectory cannot be computed due to missing or invalid goal parameters")
        
    return round(score, 2), signals

def calculate_deviation_persistence_score(
    performance_gap: Dict[str, Any],
    persistence: Dict[str, Any]
) -> Tuple[float, List[str]]:
    """Calculates 0-100 score based on benchmark gap and historical persistence.
    
    CRITICAL RULE:
    If client outperformed benchmark (gap > 0), score is low even if absolute return was negative!
    Persistent underperformance over multiple periods increases score significantly.
    """
    signals: List[str] = []
    
    gap_status = performance_gap.get("status")
    if gap_status in ("INSUFFICIENT_EVIDENCE", "MISALIGNED_PERIODS"):
        signals.append("Benchmark comparison unavailable; verification needed")
        return 40.0, signals
        
    gap_pp = performance_gap.get("performance_gap_pp", 0.0)
    outperformed = performance_gap.get("outperformed", False)
    is_persistent = persistence.get("is_persistent", False)
    neg_count = persistence.get("negative_gap_count", 0)
    total_periods = persistence.get("total_aligned_periods", 1)
    
    if outperformed or gap_pp >= 0:
        # Outperforming benchmark
        base_score = 5.0
        signals.append(f"Client outperformed benchmark by +{gap_pp:.2f} pp")
        return round(base_score, 2), signals
        
    # Underperforming benchmark (gap_pp < 0)
    underperf_magnitude = abs(gap_pp)
    base_score = min(75.0, 20.0 + (underperf_magnitude / 5.0) * 35.0)
    
    if is_persistent:
        # Persistent across historical periods
        persistence_boost = 25.0
        score = min(100.0, base_score + persistence_boost)
        signals.append(
            f"Persistent benchmark underperformance ({gap_pp:.2f} pp gap, negative in {neg_count}/{total_periods} periods)"
        )
    else:
        # Isolated deviation
        score = min(45.0, base_score)
        signals.append(f"Isolated benchmark deviation ({gap_pp:.2f} pp gap; previous periods in line)")
        
    return round(score, 2), signals

def calculate_allocation_mismatch_score(drift_eval: Dict[str, Any]) -> Tuple[float, List[str]]:
    """Calculates 0-100 score for asset allocation drift against target."""
    signals: List[str] = []
    
    if drift_eval.get("target_missing"):
        signals.append("Target asset allocation is missing; cannot evaluate portfolio alignment")
        return 45.0, signals
        
    if drift_eval.get("status") == "EMPTY_PORTFOLIO":
        signals.append("Portfolio is empty or uninitialized")
        return 60.0, signals
        
    agg_drift = drift_eval.get("aggregate_drift_pct", 0.0)
    max_drift = drift_eval.get("max_category_drift_pct", 0.0)
    max_cat = drift_eval.get("max_drift_category", "")
    
    if agg_drift < 2.0:
        score = 10.0
    elif agg_drift < 5.0:
        score = 25.0 + (agg_drift / 5.0) * 15.0
    elif agg_drift < 10.0:
        score = 45.0 + ((agg_drift - 5.0) / 5.0) * 30.0
        signals.append(f"Moderate portfolio drift of {agg_drift:.1f}% (max: {max_cat} {max_drift:.1f} pp)")
    else:
        score = min(100.0, 75.0 + ((agg_drift - 10.0) / 5.0) * 25.0)
        signals.append(f"Significant portfolio drift of {agg_drift:.1f}% (max: {max_cat} {max_drift:.1f} pp)")
        
    return round(score, 2), signals

def calculate_review_recency_score(last_review_date_str: str, as_of_date_str: str) -> Tuple[float, List[str]]:
    """Calculates 0-100 score based on days elapsed since the client's last financial review."""
    signals: List[str] = []
    try:
        last_dt = datetime.strptime(last_review_date_str, "%Y-%m-%d").date()
        as_of_dt = datetime.strptime(as_of_date_str, "%Y-%m-%d").date()
        days_since = (as_of_dt - last_dt).days
    except (ValueError, TypeError):
        signals.append("Review date invalid or missing")
        return 75.0, signals
        
    policy_days = settings.REVIEW_OVERDUE_THRESHOLD_DAYS  # 180 days
    
    if days_since <= 90:
        score = 10.0
    elif days_since <= policy_days:
        score = 25.0 + ((days_since - 90) / 90.0) * 20.0
    elif days_since <= 365:
        score = 55.0 + ((days_since - policy_days) / 185.0) * 30.0
        signals.append(f"Review overdue: {days_since} days since last review (policy: {policy_days} days)")
    else:
        score = min(100.0, 85.0 + ((days_since - 365) / 180.0) * 15.0)
        signals.append(f"Severely overdue for review: {days_since} days elapsed (> 1 year)")
        
    return round(score, 2), signals

def calculate_evidence_quality_score(data_quality: Dict[str, Any]) -> Tuple[float, List[str]]:
    """Calculates 0-100 urgency score for data quality / verification necessity."""
    signals: List[str] = []
    confidence = data_quality.get("confidence", "HIGH")
    warnings = data_quality.get("warnings", [])
    
    if confidence == "LOW":
        score = 85.0
        signals.append(f"Data verification urgently required: {'; '.join(warnings[:2])}")
    elif confidence == "MEDIUM":
        score = 50.0
        signals.append(f"Minor data quality warnings noted: {'; '.join(warnings[:1])}")
    else:
        score = 10.0
        
    return round(score, 2), signals

def compute_priority_score(
    goal_trajectory: Dict[str, Any],
    performance_gap: Dict[str, Any],
    persistence: Dict[str, Any],
    drift_eval: Dict[str, Any],
    last_review_date_str: str,
    as_of_date_str: str,
    data_quality: Dict[str, Any]
) -> Dict[str, Any]:
    """Combines all 5 normalized component scores using documented heuristic weights."""
    s_goal, sig_goal = calculate_goal_urgency_score(goal_trajectory)
    s_perf, sig_perf = calculate_deviation_persistence_score(performance_gap, persistence)
    s_drift, sig_drift = calculate_allocation_mismatch_score(drift_eval)
    s_review, sig_review = calculate_review_recency_score(last_review_date_str, as_of_date_str)
    s_quality, sig_quality = calculate_evidence_quality_score(data_quality)
    
    weights = {
        "goal_urgency": settings.WEIGHT_GOAL_URGENCY,
        "deviation_persistence": settings.WEIGHT_DEVIATION_PERSISTENCE,
        "allocation_mismatch": settings.WEIGHT_ALLOCATION_MISMATCH,
        "review_recency": settings.WEIGHT_REVIEW_RECENCY,
        "evidence_quality": settings.WEIGHT_EVIDENCE_QUALITY,
    }
    
    overall = (
        s_goal * weights["goal_urgency"]
        + s_perf * weights["deviation_persistence"]
        + s_drift * weights["allocation_mismatch"]
        + s_review * weights["review_recency"]
        + s_quality * weights["evidence_quality"]
    )
    overall_score = round(overall, 2)
    
    # Severity classification:
    # CRITICAL: >= 65.0 (multi-trigger risks, severe compounding shortfalls)
    # HIGH: >= 40.0 (substantial single-driver urgencies like severe goal lag or stale data)
    # MEDIUM: >= 25.0 (approaching review limits, minor drift)
    # LOW: < 25.0 (healthy, on-track portfolios)
    if overall_score >= 65.0:
        severity = SeverityEnum.CRITICAL
    elif overall_score >= 40.0:
        severity = SeverityEnum.HIGH
    elif overall_score >= 25.0:
        severity = SeverityEnum.MEDIUM
    else:
        severity = SeverityEnum.LOW
        
    confidence_level = data_quality.get("confidence", "HIGH")
    if confidence_level == "LOW":
        conf_enum = ConfidenceEnum.LOW
    elif confidence_level == "MEDIUM":
        conf_enum = ConfidenceEnum.MEDIUM
    else:
        conf_enum = ConfidenceEnum.HIGH
        
    all_signals = sig_goal + sig_perf + sig_drift + sig_review + sig_quality
    if not all_signals:
        all_signals = ["Portfolio and goal are tracking within normal parameters."]
        
    if conf_enum == ConfidenceEnum.LOW:
        suggested_review = "Verify portfolio data integrity, reconcile holdings, and update missing records before client outreach."
    elif s_goal >= 70.0 and s_drift >= 60.0:
        suggested_review = "Schedule comprehensive portfolio and goal review to discuss rebalancing and contribution pacing."
    elif s_goal >= 70.0:
        suggested_review = "Review goal trajectory assumptions, projected shortfall, and timeline flexibility with the client."
    elif s_drift >= 60.0:
        suggested_review = "Inspect documented target allocation and evaluate rebalancing opportunities."
    elif s_perf >= 70.0:
        suggested_review = "Analyze benchmark deviation persistence and discuss asset class suitability."
    elif s_review >= 70.0:
        suggested_review = "Schedule periodic annual review as timeline exceeds recommended horizon."
    else:
        suggested_review = "Maintain current monitoring cadence; no immediate advisor intervention required."
        
    score_components = ScoreComponents(
        goal_urgency=s_goal,
        deviation_persistence=s_perf,
        allocation_mismatch=s_drift,
        review_recency=s_review,
        evidence_quality=s_quality
    )
    
    return {
        "overall_score": overall_score,
        "score_components": score_components,
        "weights": weights,
        "severity": severity,
        "confidence_level": conf_enum,
        "confidence_reason": "; ".join(data_quality.get("confidence_reasons", ["Verified portfolio data"])),
        "contributing_signals": all_signals,
        "data_quality_warnings": data_quality.get("warnings", []),
        "suggested_review": suggested_review
    }
