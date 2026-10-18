"""Advisor Brief Generation Service.

Produces an evidence-backed, factual advisor brief designed as a decision-support draft.
Features:
- Clear draft notice & human-in-the-loop watermark
- Synthesizes verified portfolio, goal, and benchmark facts
- Highlights data warnings and confidence limitations explicitly
- Formulates neutral, structured client review questions
"""

from typing import Dict, Any, List
from datetime import datetime
from app.schemas import AdvisorBriefSchema, EvidenceItem

def generate_advisor_brief(
    client_data: Dict[str, Any],
    analytics_results: Dict[str, Any],
    prioritization_result: Dict[str, Any],
    insights: List[Any]
) -> AdvisorBriefSchema:
    """Generates an evidence-backed advisor brief draft for client review meetings."""
    client_id = client_data.get("client_id", "")
    client_name = client_data.get("display_name", "")
    as_of = client_data.get("data_as_of", datetime.now().strftime("%Y-%m-%d"))
    
    goal_traj = analytics_results.get("goal_trajectory", {})
    drift = analytics_results.get("allocation_drift", {})
    perf_gap = analytics_results.get("performance_gap", {})
    data_quality = analytics_results.get("data_quality", {})
    advice_eval = analytics_results.get("advice_follow_through", {})
    
    score = prioritization_result.get("overall_score", 0.0)
    severity = prioritization_result.get("severity")
    confidence = prioritization_result.get("confidence_level")
    signals = prioritization_result.get("contributing_signals", [])
    
    # 1. Executive Summary
    summary_parts = [
        f"Client {client_name} ({client_id}) has an overall priority score of {score:.1f}/100 ({severity.value if hasattr(severity, 'value') else severity})."
    ]
    if signals:
        summary_parts.append(f"Key drivers: {'; '.join(signals[:3])}.")
    if data_quality.get("warnings"):
        summary_parts.append(f"Data Notice: {'; '.join(data_quality.get('warnings')[:2])}.")
    executive_summary = " ".join(summary_parts)
    
    # 2. Goal Summary
    goal = client_data.get("goal", {})
    goal_summary = {
        "goal_name": goal.get("goal_name", "Primary Goal"),
        "goal_amount": goal.get("goal_amount", 0.0),
        "goal_date": goal.get("goal_date", ""),
        "current_value": client_data.get("portfolio", {}).get("total_value", 0.0),
        "progress_pct": goal_traj.get("progress_pct", 0.0),
        "modeled_target_value": goal_traj.get("modeled_target_value"),
        "shortfall_amount": goal_traj.get("shortfall_amount", 0.0),
        "shortfall_pct": goal_traj.get("shortfall_pct", 0.0),
        "trajectory_status": goal_traj.get("trajectory_status", "UNKNOWN"),
        "assumptions": goal_traj.get("assumptions_description", "Standard compound trajectory")
    }
    
    # 3. Performance Summary
    perf_summary = {
        "status": perf_gap.get("status", "VALID"),
        "client_return_pct": perf_gap.get("client_return_pct"),
        "benchmark_id": perf_gap.get("benchmark_id"),
        "benchmark_return_pct": perf_gap.get("benchmark_return_pct"),
        "performance_gap_pp": perf_gap.get("performance_gap_pp"),
        "period_start": perf_gap.get("period_start"),
        "period_end": perf_gap.get("period_end"),
        "explanation": perf_gap.get("explanation", "Performance data current.")
    }
    
    # 4. Allocation Summary
    target_alloc = client_data.get("portfolio", {}).get("target_allocation")
    alloc_summary = {
        "has_target_allocation": target_alloc is not None and len(target_alloc) > 0,
        "aggregate_drift_pct": drift.get("aggregate_drift_pct", 0.0),
        "max_category_drift_pct": drift.get("max_category_drift_pct", 0.0),
        "max_drift_category": drift.get("max_drift_category"),
        "exceeds_threshold": drift.get("exceeds_threshold", False),
        "category_breakdown": drift.get("category_drifts", {}),
        "explanation": drift.get("explanation", "Target allocation aligned.")
    }
    
    # 5. Advice History & Follow-Through
    advice_records = client_data.get("advice_history", [])
    advice_summary = {
        "total_records": len(advice_records),
        "latest_advice_date": advice_records[0].get("recording_date") if advice_records else None,
        "latest_advice_text": advice_records[0].get("advice_text") if advice_records else None,
        "follow_through_status": advice_eval.get("status", "INSUFFICIENT_EVIDENCE"),
        "evaluation_notes": advice_eval.get("explanation", "No recorded advice found.")
    }
    
    # 6. Data Freshness & Confidence
    data_freshness = {
        "valuation_date": client_data.get("portfolio", {}).get("valuation_date"),
        "data_as_of": as_of,
        "confidence_level": confidence.value if hasattr(confidence, "value") else confidence,
        "confidence_reason": prioritization_result.get("confidence_reason", "Verified data"),
        "warnings": data_quality.get("warnings", []),
        "requires_verification": data_quality.get("requires_verification", False)
    }
    
    # 7. Formulate Review Questions for Advisor
    review_questions: List[str] = []
    if data_quality.get("requires_verification"):
        review_questions.append("Have recent deposits, transfers, or custodian feed delays occurred that explain data discrepancies?")
    if goal_traj.get("trajectory_status") in ("CRITICAL_SHORTFALL", "BEHIND"):
        review_questions.append(f"Given the modeled ${goal_traj.get('shortfall_amount', 0):,.0f} goal shortfall, can the client increase monthly contributions or extend the horizon?")
    if drift.get("exceeds_threshold"):
        review_questions.append(f"Does the current {drift.get('aggregate_drift_pct', 0):.1f}% allocation drift reflect deliberate tactical positioning or unattended market drift?")
    if perf_gap.get("performance_gap_pp") is not None and perf_gap.get("performance_gap_pp") < -1.0:
        review_questions.append("Does the client understand recent benchmark deviation factors and do their risk expectations remain aligned?")
    if not review_questions:
        review_questions.append("Are there any life events, liquidity needs, or changes in investment objectives since the last review?")
    review_questions.append("Would the client benefit from reconfirming their target asset allocation and risk profile?")
    
    # Collect all evidence items from insights
    all_evidence: List[EvidenceItem] = []
    for ins in insights:
        if hasattr(ins, "evidence") and ins.evidence:
            all_evidence.extend(ins.evidence)
            
    return AdvisorBriefSchema(
        client_id=client_id,
        client_name=client_name,
        brief_date=as_of,
        draft_notice="DRAFT FOR ADVISOR REVIEW — Decision support only. Not an autonomous recommendation.",
        executive_summary=executive_summary,
        goal_summary=goal_summary,
        performance_summary=perf_summary,
        allocation_summary=alloc_summary,
        advice_follow_through=advice_summary,
        data_freshness_and_confidence=data_freshness,
        suggested_review_questions=review_questions,
        evidence=all_evidence
    )
