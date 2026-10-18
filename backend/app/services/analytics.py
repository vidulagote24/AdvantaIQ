"""Deterministic Financial Analytics Service.

All calculations are pure, deterministic, unit-testable, and traceable to verified evidence.
Adheres strictly to decision-support principles:
- Negative returns do not imply underperformance if benchmark outperformed.
- Positive returns may still fall behind goal trajectories.
- Drift is only evaluated when documented target allocations exist.
- Missing or stale data produces explicit warnings and reduces confidence.
"""

from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any
from dateutil.relativedelta import relativedelta

def calculate_performance_gap(
    client_return_pct: Optional[float],
    benchmark_return_pct: Optional[float],
    benchmark_id: Optional[str] = None,
    period_start: Optional[str] = None,
    period_end: Optional[str] = None,
    aligned: bool = True
) -> Dict[str, Any]:
    """Calculates performance gap: client_return_pct - benchmark_return_pct in percentage points.
    
    Returns structured explanation, units, and evidence fields.
    """
    if client_return_pct is None or benchmark_return_pct is None:
        return {
            "status": "INSUFFICIENT_EVIDENCE",
            "performance_gap_pp": None,
            "client_return_pct": client_return_pct,
            "benchmark_return_pct": benchmark_return_pct,
            "benchmark_id": benchmark_id,
            "period_start": period_start,
            "period_end": period_end,
            "unit": "percentage_points",
            "outperformed": False,
            "warning": "Missing return data for client or benchmark",
            "explanation": "Cannot calculate performance gap: benchmark return or client return is missing."
        }
    
    if not aligned:
        return {
            "status": "MISALIGNED_PERIODS",
            "performance_gap_pp": None,
            "client_return_pct": client_return_pct,
            "benchmark_return_pct": benchmark_return_pct,
            "benchmark_id": benchmark_id,
            "period_start": period_start,
            "period_end": period_end,
            "unit": "percentage_points",
            "outperformed": False,
            "warning": "Client period and benchmark period are not aligned",
            "explanation": "Cannot compare returns because the observation periods do not align."
        }
    
    gap_pp = round(client_return_pct - benchmark_return_pct, 4)
    outperformed = gap_pp >= 0.0
    
    if gap_pp > 0:
        rel = f"outperformed benchmark {benchmark_id or ''} by +{gap_pp:.2f} percentage points"
    elif gap_pp < 0:
        rel = f"underperformed benchmark {benchmark_id or ''} by {gap_pp:.2f} percentage points"
    else:
        rel = f"matched benchmark {benchmark_id or ''} exactly"
        
    explanation = (
        f"Client return was {client_return_pct:+.2f}% vs benchmark return of {benchmark_return_pct:+.2f}%, "
        f"yielding a performance gap of {gap_pp:+.2f} percentage points ({rel})."
    )
    
    return {
        "status": "VALID",
        "performance_gap_pp": gap_pp,
        "client_return_pct": round(client_return_pct, 4),
        "benchmark_return_pct": round(benchmark_return_pct, 4),
        "benchmark_id": benchmark_id,
        "period_start": period_start,
        "period_end": period_end,
        "unit": "percentage_points",
        "outperformed": outperformed,
        "warning": None,
        "explanation": explanation
    }

def calculate_goal_trajectory(
    goal_amount: float,
    current_value: float,
    start_date: str,
    goal_date: str,
    as_of_date: str,
    initial_amount: float,
    monthly_contribution: float = 0.0,
    assumed_annual_rate_pct: float = 6.0
) -> Dict[str, Any]:
    """Calculates goal trajectory comparing current value against a documented modeled target path.
    
    Modeled path formula:
    Standard compound accumulation with regular monthly contributions:
    V(t) = initial_amount * (1 + r_m)^m + monthly_contribution * [((1 + r_m)^m - 1) / r_m]
    where r_m = assumed_annual_rate / 12, and m = elapsed months from start_date to as_of_date.
    """
    if goal_amount <= 0 or current_value is None:
        return {
            "status": "INVALID_INPUT",
            "progress_pct": 0.0,
            "modeled_target_value": None,
            "shortfall_amount": None,
            "shortfall_pct": None,
            "trajectory_status": "UNKNOWN",
            "warning": "Goal amount must be positive and current value must be present",
            "assumptions_description": "Invalid goal parameters."
        }
        
    try:
        dt_start = datetime.strptime(start_date, "%Y-%m-%d").date()
        dt_goal = datetime.strptime(goal_date, "%Y-%m-%d").date()
        dt_as_of = datetime.strptime(as_of_date, "%Y-%m-%d").date()
    except (ValueError, TypeError) as e:
        return {
            "status": "INVALID_DATES",
            "progress_pct": round((current_value / goal_amount) * 100, 2),
            "modeled_target_value": None,
            "shortfall_amount": None,
            "shortfall_pct": None,
            "trajectory_status": "UNKNOWN",
            "warning": f"Invalid date formatting: {e}",
            "assumptions_description": "Cannot parse trajectory dates."
        }
        
    if dt_as_of >= dt_goal:
        # Goal horizon has passed
        progress_pct = round((current_value / goal_amount) * 100, 2)
        if current_value >= goal_amount:
            trajectory_status = "ON_TRACK"
            shortfall = 0.0
            shortfall_pct = 0.0
        else:
            trajectory_status = "EXPIRED"
            shortfall = round(goal_amount - current_value, 2)
            shortfall_pct = round((shortfall / goal_amount) * 100, 2)
            
        return {
            "status": "EXPIRED" if trajectory_status == "EXPIRED" else "VALID",
            "progress_pct": progress_pct,
            "modeled_target_value": goal_amount,
            "shortfall_amount": shortfall,
            "shortfall_pct": shortfall_pct,
            "trajectory_status": trajectory_status,
            "warning": "Goal target date has passed." if trajectory_status == "EXPIRED" else None,
            "assumptions_description": f"Goal target date ({goal_date}) reached. Modeled target is final goal amount."
        }
        
    # Calculate elapsed and total months
    total_months = max(1, (dt_goal.year - dt_start.year) * 12 + (dt_goal.month - dt_start.month))
    elapsed_months = max(0, (dt_as_of.year - dt_start.year) * 12 + (dt_as_of.month - dt_start.month))
    
    r_monthly = (assumed_annual_rate_pct / 100.0) / 12.0
    
    # Calculate modeled trajectory at as_of_date
    if r_monthly > 0:
        fv_initial = initial_amount * ((1 + r_monthly) ** elapsed_months)
        if monthly_contribution > 0:
            fv_contributions = monthly_contribution * (((1 + r_monthly) ** elapsed_months - 1) / r_monthly)
        else:
            fv_contributions = 0.0
    else:
        fv_initial = initial_amount
        fv_contributions = monthly_contribution * elapsed_months
        
    modeled_target = round(fv_initial + fv_contributions, 2)
    # Target shouldn't exceed goal amount before goal date
    modeled_target = min(modeled_target, goal_amount)
    
    progress_pct = round((current_value / goal_amount) * 100, 2)
    
    shortfall = round(modeled_target - current_value, 2)
    if shortfall > 0:
        shortfall_pct = round((shortfall / modeled_target) * 100, 2) if modeled_target > 0 else 0.0
    else:
        shortfall = 0.0
        shortfall_pct = 0.0
        
    if shortfall_pct >= 20.0:
        trajectory_status = "CRITICAL_SHORTFALL"
    elif shortfall_pct >= 5.0:
        trajectory_status = "BEHIND"
    else:
        trajectory_status = "ON_TRACK"
        
    assumptions_desc = (
        f"Modeled path based on initial balance of ${initial_amount:,.0f}, "
        f"monthly contribution of ${monthly_contribution:,.0f}, and "
        f"{assumed_annual_rate_pct:.1f}% assumed annual return rate over {elapsed_months} elapsed months "
        f"of {total_months} total months."
    )
    
    return {
        "status": "VALID",
        "progress_pct": progress_pct,
        "modeled_target_value": modeled_target,
        "shortfall_amount": shortfall,
        "shortfall_pct": shortfall_pct,
        "trajectory_status": trajectory_status,
        "elapsed_months": elapsed_months,
        "total_months": total_months,
        "warning": None,
        "assumptions_description": assumptions_desc
    }

def calculate_allocation_drift(
    holdings: List[Dict[str, Any]],
    target_allocation: Optional[Dict[str, float]],
    drift_alert_threshold_pct: float = 5.0
) -> Dict[str, Any]:
    """Calculates category-level drift and aggregate absolute drift vs documented target allocation.
    
    Aggregate drift = sum(abs(actual_pct - target_pct)) / 2.0
    If target_allocation is missing or empty, returns INSUFFICIENT_EVIDENCE state.
    """
    if not target_allocation or len(target_allocation) == 0:
        return {
            "status": "INSUFFICIENT_EVIDENCE",
            "target_missing": True,
            "aggregate_drift_pct": 0.0,
            "max_category_drift_pct": 0.0,
            "category_drifts": {},
            "exceeds_threshold": False,
            "warning": "Target allocation is missing or undocumented. Drift cannot be evaluated.",
            "explanation": "No documented target allocation on file for this client. Cannot evaluate allocation drift without target."
        }
        
    # Aggregate actual weights by category
    total_market_val = sum(h.get("market_value", 0.0) for h in holdings)
    if total_market_val <= 0:
        return {
            "status": "EMPTY_PORTFOLIO",
            "target_missing": False,
            "aggregate_drift_pct": 0.0,
            "max_category_drift_pct": 0.0,
            "category_drifts": {},
            "exceeds_threshold": False,
            "warning": "Portfolio holdings are empty or total value is zero",
            "explanation": "Cannot calculate allocation drift for an empty portfolio."
        }
        
    actual_category_values: Dict[str, float] = {}
    for h in holdings:
        cat = h.get("category", "Unclassified")
        actual_category_values[cat] = actual_category_values.get(cat, 0.0) + h.get("market_value", 0.0)
        
    actual_allocation: Dict[str, float] = {
        cat: round((val / total_market_val) * 100.0, 2)
        for cat, val in actual_category_values.items()
    }
    
    # Compare all categories present in either target or actual
    all_categories = set(target_allocation.keys()).union(set(actual_allocation.keys()))
    category_drifts: Dict[str, Dict[str, Any]] = {}
    total_abs_drift = 0.0
    max_cat_drift = 0.0
    max_drift_category = None
    
    for cat in sorted(all_categories):
        target_pct = round(target_allocation.get(cat, 0.0), 2)
        actual_pct = round(actual_allocation.get(cat, 0.0), 2)
        drift_pp = round(actual_pct - target_pct, 2)
        abs_drift = abs(drift_pp)
        total_abs_drift += abs_drift
        if abs_drift > max_cat_drift:
            max_cat_drift = abs_drift
            max_drift_category = cat
            
        category_drifts[cat] = {
            "target_pct": target_pct,
            "actual_pct": actual_pct,
            "drift_pp": drift_pp,
            "abs_drift": abs_drift,
            "status": "OVERWEIGHT" if drift_pp > 0 else ("UNDERWEIGHT" if drift_pp < 0 else "BALANCED")
        }
        
    aggregate_drift_pct = round(total_abs_drift / 2.0, 2)
    exceeds_threshold = (aggregate_drift_pct >= drift_alert_threshold_pct) or (max_cat_drift >= drift_alert_threshold_pct * 1.5)
    
    drift_details = [
        f"{cat}: actual {d['actual_pct']:.1f}% vs target {d['target_pct']:.1f}% ({d['drift_pp']:+.1f}%)"
        for cat, d in category_drifts.items() if abs(d['drift_pp']) >= 1.0
    ]
    explanation = (
        f"Aggregate portfolio drift is {aggregate_drift_pct:.1f}% (threshold {drift_alert_threshold_pct:.1f}%). "
        f"Max deviation in {max_drift_category} ({max_cat_drift:.1f} pp). "
        + (f"Key variances: {', '.join(drift_details)}." if drift_details else "Portfolio aligned with targets.")
    )
    
    return {
        "status": "VALID",
        "target_missing": False,
        "aggregate_drift_pct": aggregate_drift_pct,
        "max_category_drift_pct": round(max_cat_drift, 2),
        "max_drift_category": max_drift_category,
        "category_drifts": category_drifts,
        "exceeds_threshold": exceeds_threshold,
        "warning": None,
        "explanation": explanation
    }

def evaluate_persistence(
    historical_periods: List[Dict[str, Any]],
    min_periods: int = 2
) -> Dict[str, Any]:
    """Distinguishes isolated negative periods from repeated deviations across comparable historical periods."""
    if not historical_periods or len(historical_periods) == 0:
        return {
            "status": "INSUFFICIENT_EVIDENCE",
            "is_persistent": False,
            "negative_gap_count": 0,
            "total_aligned_periods": 0,
            "persistence_ratio": 0.0,
            "warning": "No historical performance periods available to evaluate persistence",
            "explanation": "Insufficient historical data to determine deviation persistence."
        }
        
    aligned_periods = [p for p in historical_periods if p.get("aligned", True) and p.get("performance_gap_pp") is not None]
    
    if len(aligned_periods) == 0:
        return {
            "status": "INSUFFICIENT_EVIDENCE",
            "is_persistent": False,
            "negative_gap_count": 0,
            "total_aligned_periods": 0,
            "persistence_ratio": 0.0,
            "warning": "No aligned benchmark comparisons found in historical periods",
            "explanation": "Historical periods are missing benchmark alignments."
        }
        
    negative_gaps = [p for p in aligned_periods if (p.get("performance_gap_pp") or 0.0) < -0.5]
    negative_count = len(negative_gaps)
    total_aligned = len(aligned_periods)
    ratio = round(negative_count / total_aligned, 2)
    
    is_persistent = (negative_count >= min_periods) and (ratio >= 0.5)
    
    explanation = (
        f"Client underperformed benchmark in {negative_count} of {total_aligned} aligned historical periods "
        f"({ratio * 100:.0f}%). "
        + ("Repeated deviations detected across multiple horizons." if is_persistent else "Isolated deviation or consistent alignment.")
    )
    
    return {
        "status": "VALID",
        "is_persistent": is_persistent,
        "negative_gap_count": negative_count,
        "total_aligned_periods": total_aligned,
        "persistence_ratio": ratio,
        "warning": None,
        "explanation": explanation
    }

def evaluate_advice_follow_through(
    advice_records: List[Dict[str, Any]],
    current_portfolio_snapshot: Dict[str, Any]
) -> Dict[str, Any]:
    """Evaluates whether recorded advisor recommendations were implemented, or if evidence is ambiguous/missing."""
    if not advice_records or len(advice_records) == 0:
        return {
            "status": "INSUFFICIENT_EVIDENCE",
            "advice_present": False,
            "followed_through": None,
            "unimplemented_count": 0,
            "warning": "No recorded advisor advice found on file",
            "explanation": "No prior advisor advice records found. Cannot evaluate advice follow-through without documented advice."
        }
        
    latest_advice = advice_records[0]
    advice_text = latest_advice.get("advice_text", "")
    target_alloc = latest_advice.get("target_allocation")
    
    # If target allocation was specified in advice, check drift against current portfolio
    if target_alloc:
        drift_eval = calculate_allocation_drift(
            current_portfolio_snapshot.get("holdings", []),
            target_alloc,
            drift_alert_threshold_pct=5.0
        )
        if drift_eval["status"] == "VALID":
            if drift_eval["exceeds_threshold"]:
                return {
                    "status": "NOT_FOLLOWED",
                    "advice_present": True,
                    "followed_through": False,
                    "unimplemented_count": 1,
                    "warning": f"Current allocation deviates from advised targets: {drift_eval['explanation']}",
                    "explanation": f"Advised target allocation ({latest_advice.get('recording_date')}) not reflected in current holdings."
                }
            else:
                return {
                    "status": "FOLLOWED",
                    "advice_present": True,
                    "followed_through": True,
                    "unimplemented_count": 0,
                    "warning": None,
                    "explanation": f"Portfolio aligns with advised target allocation from {latest_advice.get('recording_date')}."
                }
                
    # If status is explicitly noted
    status = latest_advice.get("status", "recorded").lower()
    if status == "implemented":
        return {
            "status": "FOLLOWED",
            "advice_present": True,
            "followed_through": True,
            "unimplemented_count": 0,
            "warning": None,
            "explanation": f"Advice '{advice_text}' marked as implemented."
        }
    elif status == "pending" or status == "unimplemented":
        return {
            "status": "NOT_FOLLOWED",
            "advice_present": True,
            "followed_through": False,
            "unimplemented_count": 1,
            "warning": f"Pending advice '{advice_text}' not yet executed.",
            "explanation": f"Advisor recommendation from {latest_advice.get('recording_date')} remains pending."
        }
        
    return {
        "status": "AMBIGUOUS_EVIDENCE",
        "advice_present": True,
        "followed_through": None,
        "unimplemented_count": 0,
        "warning": "Advice record does not have quantifiable execution criteria",
        "explanation": f"Recorded advice ('{advice_text}') is qualitative; execution status cannot be verified automatically."
    }

def assess_data_quality_and_freshness(
    client_data: Dict[str, Any],
    as_of_date: str,
    stale_threshold_days: int = 90,
    warning_threshold_days: int = 45
) -> Dict[str, Any]:
    """Examines snapshot freshness, missing fields, holding sum consistency, and period alignments.
    
    Produces explicit data warnings, confidence level, and verification tasks.
    """
    warnings: List[str] = []
    confidence = "HIGH"
    confidence_reasons: List[str] = []
    
    portfolio = client_data.get("portfolio") or {}
    valuation_date_str = portfolio.get("valuation_date")
    
    # 1. Valuation Freshness
    if not valuation_date_str:
        warnings.append("Portfolio valuation date is missing")
        confidence = "LOW"
        confidence_reasons.append("Missing valuation date")
    else:
        try:
            val_date = datetime.strptime(valuation_date_str, "%Y-%m-%d").date()
            as_of = datetime.strptime(as_of_date, "%Y-%m-%d").date()
            age_days = (as_of - val_date).days
            if age_days < 0:
                warnings.append(f"Valuation date ({valuation_date_str}) is in the future relative to system date ({as_of_date})")
                confidence = "LOW"
            elif age_days > stale_threshold_days:
                warnings.append(f"Portfolio snapshot is stale ({age_days} days old, exceeds {stale_threshold_days}-day limit)")
                confidence = "LOW"
                confidence_reasons.append(f"Stale valuation data ({age_days} days)")
            elif age_days > warning_threshold_days:
                warnings.append(f"Portfolio snapshot is aging ({age_days} days old)")
                if confidence == "HIGH":
                    confidence = "MEDIUM"
                confidence_reasons.append(f"Aging valuation data ({age_days} days)")
        except (ValueError, TypeError):
            warnings.append(f"Invalid valuation date format: {valuation_date_str}")
            confidence = "LOW"
            confidence_reasons.append("Unparseable valuation date")
            
    # 2. Holdings consistency check
    holdings = portfolio.get("holdings", [])
    total_val = portfolio.get("total_value", 0.0)
    if len(holdings) == 0:
        warnings.append("Holdings list is empty")
        confidence = "LOW"
        confidence_reasons.append("Empty holdings list")
    else:
        holdings_sum = sum(h.get("market_value", 0.0) for h in holdings)
        # Check if holdings_sum + cash_balance matches total_val within 1%
        cash = portfolio.get("cash_balance", 0.0)
        reconciled_val = holdings_sum # in our schema holdings includes cash asset or separate cash
        pct_diff = abs(total_val - holdings_sum) / total_val if total_val > 0 else 1.0
        if pct_diff > 0.015:
            warnings.append(f"Holdings sum (${holdings_sum:,.2f}) does not reconcile with total portfolio value (${total_val:,.2f}, diff {pct_diff*100:.1f}%)")
            confidence = "LOW"
            confidence_reasons.append("Conflicting portfolio accounting records")
            
    # 3. Target allocation presence
    target_alloc = portfolio.get("target_allocation")
    if not target_alloc:
        warnings.append("No documented target asset allocation found")
        if confidence == "HIGH":
            confidence = "MEDIUM"
        confidence_reasons.append("Missing target allocation")
        
    # 4. Benchmark presence in historical performance
    hist_perf = client_data.get("historical_performance", [])
    has_benchmark = any(p.get("benchmark_return_pct") is not None for p in hist_perf)
    if not has_benchmark and len(hist_perf) > 0:
        warnings.append("Missing benchmark comparison data for historical periods")
        if confidence == "HIGH":
            confidence = "MEDIUM"
        confidence_reasons.append("Missing benchmark data")
        
    # 5. Goal details
    goal = client_data.get("goal") or {}
    if not goal.get("goal_amount") or goal.get("goal_amount", 0) <= 0:
        warnings.append("Client goal amount is missing or invalid")
        confidence = "LOW"
        confidence_reasons.append("Incomplete goal parameters")
        
    if not confidence_reasons:
        confidence_reasons.append("Complete, fresh, and fully reconciled portfolio data")
        
    return {
        "confidence": confidence,
        "warnings": warnings,
        "confidence_reasons": confidence_reasons,
        "is_stale": any("stale" in w.lower() for w in warnings),
        "has_conflicts": any("reconcile" in w.lower() for w in warnings),
        "requires_verification": len(warnings) > 0 and confidence in ("LOW", "MEDIUM")
    }
