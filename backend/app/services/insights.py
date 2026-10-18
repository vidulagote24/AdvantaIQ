"""Evidence-Backed Insight Generation Service.

Translates deterministic analytics and prioritization signals into traceable,
evidence-grounded insight cards.
Adheres strictly to the validated InsightSchema with traceable EvidenceItems.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from app.schemas import (
    InsightSchema,
    InsightTypeEnum,
    SeverityEnum,
    ConfidenceEnum,
    EvidenceItem,
    ScoreComponents
)

def generate_client_insights(
    client_data: Dict[str, Any],
    analytics_results: Dict[str, Any],
    prioritization_result: Dict[str, Any]
) -> List[InsightSchema]:
    """Generates traceable, evidence-grounded insight cards for a client.
    
    Generates cards for:
    1. GOAL_AT_RISK (when trajectory shows shortfall or goal expired)
    2. ALLOCATION_DRIFT (when aggregate drift exceeds threshold and target exists)
    3. PERSISTENT_UNDERPERFORMANCE (when benchmark gap is persistently negative)
    4. REVIEW_OVERDUE (when days since last review exceed policy threshold)
    5. DATA_VERIFICATION_REQUIRED (when data quality issues, stale snapshots, or unverified records exist)
    """
    insights: List[InsightSchema] = []
    client_id = client_data.get("client_id", "")
    client_name = client_data.get("display_name", "")
    as_of = client_data.get("data_as_of", datetime.now().strftime("%Y-%m-%d"))
    score = prioritization_result.get("overall_score", 0.0)
    score_components = prioritization_result.get("score_components")
    confidence_level = prioritization_result.get("confidence_level", ConfidenceEnum.HIGH)
    confidence_reason = prioritization_result.get("confidence_reason", "Verified evidence")
    
    goal_traj = analytics_results.get("goal_trajectory", {})
    drift = analytics_results.get("allocation_drift", {})
    perf_gap = analytics_results.get("performance_gap", {})
    persistence = analytics_results.get("persistence", {})
    data_quality = analytics_results.get("data_quality", {})
    
    # 1. DATA VERIFICATION REQUIRED
    if data_quality.get("requires_verification"):
        warnings = data_quality.get("warnings", [])
        evidence_items = [
            EvidenceItem(
                metric_name="Data Quality Findings",
                observed_value="; ".join(warnings),
                baseline_value="Complete, reconciled, fresh snapshot (<90d)",
                unit="status",
                source_field="portfolio.valuation_date, holdings",
                source_date=client_data.get("portfolio", {}).get("valuation_date"),
                confidence=confidence_level.value,
                calculation_explanation="Automated data audit detected anomalies or stale records exceeding system thresholds."
            )
        ]
        
        insights.append(
            InsightSchema(
                insight_id=f"INSIGHT-{client_id}-DATA",
                client_id=client_id,
                client_name=client_name,
                type=InsightTypeEnum.DATA_VERIFICATION_REQUIRED,
                headline="Portfolio Data Verification Required",
                what_changed=f"Automated integrity checks identified data verification requirements: {'; '.join(warnings[:2])}.",
                why_it_matters="Advisory decisions cannot be reliably grounded without verified, reconciled portfolio records.",
                severity=SeverityEnum.CRITICAL if confidence_level == ConfidenceEnum.LOW else SeverityEnum.HIGH,
                score=score,
                score_components=score_components,
                evidence=evidence_items,
                metric_values={"warnings_count": len(warnings), "warnings": warnings},
                confidence=confidence_level,
                confidence_reason=confidence_reason,
                data_as_of=as_of,
                suggested_review="Verify client records with the custodian or custodian data feed before conducting advisory discussions.",
                created_at=datetime.now(timezone.utc).isoformat()
            )
        )
        
    # 2. GOAL AT RISK
    if goal_traj.get("trajectory_status") in ("CRITICAL_SHORTFALL", "BEHIND", "EXPIRED"):
        shortfall_pct = goal_traj.get("shortfall_pct", 0.0)
        shortfall_amt = goal_traj.get("shortfall_amount", 0.0)
        modeled_val = goal_traj.get("modeled_target_value", 0.0)
        cur_val = client_data.get("portfolio", {}).get("total_value", 0.0)
        goal_name = client_data.get("goal", {}).get("goal_name", "Primary Goal")
        goal_date = client_data.get("goal", {}).get("goal_date", "")
        
        sev = (
            SeverityEnum.CRITICAL
            if goal_traj.get("trajectory_status") in ("CRITICAL_SHORTFALL", "EXPIRED")
            else SeverityEnum.HIGH
        )
        
        evidence_items = [
            EvidenceItem(
                metric_name="Modeled Goal Target vs Current Value",
                observed_value=cur_val,
                baseline_value=modeled_val,
                unit="USD",
                source_field="portfolio.total_value vs modeled_target_path",
                source_date=as_of,
                confidence=confidence_level.value,
                calculation_explanation=goal_traj.get("assumptions_description", "")
            ),
            EvidenceItem(
                metric_name="Goal Shortfall Percentage",
                observed_value=shortfall_pct,
                baseline_value=0.0,
                unit="%",
                source_field="shortfall_pct",
                source_date=as_of,
                confidence=confidence_level.value,
                calculation_explanation=f"Calculated as (modeled_target - current_value) / modeled_target * 100."
            )
        ]
        
        insights.append(
            InsightSchema(
                insight_id=f"INSIGHT-{client_id}-GOAL",
                client_id=client_id,
                client_name=client_name,
                type=InsightTypeEnum.GOAL_AT_RISK,
                headline=f"Goal Trajectory Shortfall: {goal_name}",
                what_changed=f"Portfolio value (${cur_val:,.0f}) is behind the modeled path (${modeled_val:,.0f}) by ${shortfall_amt:,.0f} ({shortfall_pct:.1f}%).",
                why_it_matters=f"Current capital accumulation trajectory indicates potential difficulty meeting the {goal_name} target date ({goal_date}) under current contribution assumptions.",
                severity=sev,
                score=score,
                score_components=score_components,
                evidence=evidence_items,
                metric_values={
                    "shortfall_amount": shortfall_amt,
                    "shortfall_pct": shortfall_pct,
                    "modeled_target_value": modeled_val,
                    "current_value": cur_val,
                    "goal_date": goal_date
                },
                confidence=confidence_level,
                confidence_reason=confidence_reason,
                data_as_of=as_of,
                suggested_review="Review contribution rates, target retirement/milestone date, and modeled return assumptions with the client.",
                created_at=datetime.now(timezone.utc).isoformat()
            )
        )
        
    # 3. ALLOCATION DRIFT
    if drift.get("exceeds_threshold"):
        agg_drift = drift.get("aggregate_drift_pct", 0.0)
        max_drift = drift.get("max_category_drift_pct", 0.0)
        max_cat = drift.get("max_drift_category", "Asset Class")
        
        evidence_items = [
            EvidenceItem(
                metric_name="Aggregate Portfolio Drift",
                observed_value=agg_drift,
                baseline_value=0.0,
                unit="%",
                source_field="portfolio.holdings vs target_allocation",
                source_date=as_of,
                confidence=confidence_level.value,
                calculation_explanation=drift.get("explanation", "")
            )
        ]
        
        # Add key category drift evidence
        for cat, d in drift.get("category_drifts", {}).items():
            if abs(d.get("drift_pp", 0.0)) >= 3.0:
                evidence_items.append(
                    EvidenceItem(
                        metric_name=f"{cat} Allocation Variance",
                        observed_value=d.get("actual_pct"),
                        baseline_value=d.get("target_pct"),
                        unit="%",
                        source_field=f"holdings.{cat}",
                        source_date=as_of,
                        confidence=confidence_level.value,
                        calculation_explanation=f"Actual weight {d.get('actual_pct')}% vs target {d.get('target_pct')}% (variance: {d.get('drift_pp'):+.1f} pp)."
                    )
                )
                
        insights.append(
            InsightSchema(
                insight_id=f"INSIGHT-{client_id}-DRIFT",
                client_id=client_id,
                client_name=client_name,
                type=InsightTypeEnum.ALLOCATION_DRIFT,
                headline=f"Portfolio Allocation Drift ({agg_drift:.1f}%)",
                what_changed=f"Holdings have drifted {agg_drift:.1f}% from the documented target model, led by {max_cat} ({max_drift:.1f} pp variance).",
                why_it_matters="Portfolio risk and expected return characteristics may no longer reflect the client's agreed risk profile and investment mandate.",
                severity=SeverityEnum.HIGH if agg_drift >= 10.0 else SeverityEnum.MEDIUM,
                score=score,
                score_components=score_components,
                evidence=evidence_items,
                metric_values={
                    "aggregate_drift_pct": agg_drift,
                    "max_category_drift_pct": max_drift,
                    "max_drift_category": max_cat
                },
                confidence=confidence_level,
                confidence_reason=confidence_reason,
                data_as_of=as_of,
                suggested_review="Inspect the documented target model, evaluate recent market movements, and discuss rebalancing with the client.",
                created_at=datetime.now(timezone.utc).isoformat()
            )
        )
        
    # 4. PERSISTENT UNDERPERFORMANCE
    if persistence.get("is_persistent"):
        gap_pp = perf_gap.get("performance_gap_pp", 0.0)
        bench_id = perf_gap.get("benchmark_id", "Benchmark")
        neg_count = persistence.get("negative_gap_count", 0)
        tot_periods = persistence.get("total_aligned_periods", 0)
        
        evidence_items = [
            EvidenceItem(
                metric_name="Latest Period Performance Gap",
                observed_value=perf_gap.get("client_return_pct"),
                baseline_value=perf_gap.get("benchmark_return_pct"),
                unit="%",
                period_start=perf_gap.get("period_start"),
                period_end=perf_gap.get("period_end"),
                source_field="historical_performance[latest]",
                source_date=as_of,
                confidence=confidence_level.value,
                calculation_explanation=perf_gap.get("explanation", "")
            ),
            EvidenceItem(
                metric_name="Deviation Persistence Ratio",
                observed_value=f"{neg_count}/{tot_periods}",
                baseline_value="0/N",
                unit="ratio",
                source_field="historical_performance",
                source_date=as_of,
                confidence=confidence_level.value,
                calculation_explanation=persistence.get("explanation", "")
            )
        ]
        
        insights.append(
            InsightSchema(
                insight_id=f"INSIGHT-{client_id}-PERF",
                client_id=client_id,
                client_name=client_name,
                type=InsightTypeEnum.PERSISTENT_UNDERPERFORMANCE,
                headline=f"Persistent Benchmark Underperformance vs {bench_id}",
                what_changed=f"Portfolio lagged benchmark by {gap_pp:.2f} pp in the latest period and underperformed in {neg_count} of {tot_periods} aligned historical periods.",
                why_it_matters="Multi-period deviation suggests systematic drag or asset selection variances rather than short-term market noise.",
                severity=SeverityEnum.HIGH if abs(gap_pp) >= 4.0 else SeverityEnum.MEDIUM,
                score=score,
                score_components=score_components,
                evidence=evidence_items,
                metric_values={
                    "performance_gap_pp": gap_pp,
                    "client_return_pct": perf_gap.get("client_return_pct"),
                    "benchmark_return_pct": perf_gap.get("benchmark_return_pct"),
                    "negative_gap_periods": neg_count,
                    "total_aligned_periods": tot_periods
                },
                confidence=confidence_level,
                confidence_reason=confidence_reason,
                data_as_of=as_of,
                suggested_review="Review asset selection and expense ratios with the client to evaluate if benchmark alignment remains suitable.",
                created_at=datetime.now(timezone.utc).isoformat()
            )
        )
        
    # 5. REVIEW OVERDUE
    last_review_str = client_data.get("last_review_date", "")
    try:
        last_dt = datetime.strptime(last_review_str, "%Y-%m-%d").date()
        as_of_dt = datetime.strptime(as_of, "%Y-%m-%d").date()
        days_since = (as_of_dt - last_dt).days
    except (ValueError, TypeError):
        days_since = 999
        
    if days_since > 180:
        evidence_items = [
            EvidenceItem(
                metric_name="Days Since Last Formal Review",
                observed_value=days_since,
                baseline_value=180,
                unit="days",
                source_field="client.last_review_date",
                source_date=last_review_str,
                confidence="HIGH",
                calculation_explanation=f"Calculated as elapsed days between last review ({last_review_str}) and as-of date ({as_of})."
            )
        ]
        
        insights.append(
            InsightSchema(
                insight_id=f"INSIGHT-{client_id}-REVIEW",
                client_id=client_id,
                client_name=client_name,
                type=InsightTypeEnum.REVIEW_OVERDUE,
                headline=f"Periodic Financial Review Overdue ({days_since} Days)",
                what_changed=f"{days_since} days have elapsed since the last documented client review on {last_review_str} (standard cadence: 180 days).",
                why_it_matters="Periodic reviews ensure investment objectives, risk tolerance, and life circumstances remain aligned with the mandate.",
                severity=SeverityEnum.HIGH if days_since >= 365 else SeverityEnum.MEDIUM,
                score=score,
                score_components=score_components,
                evidence=evidence_items,
                metric_values={"days_since_review": days_since, "last_review_date": last_review_str},
                confidence=ConfidenceEnum.HIGH,
                confidence_reason="Verified review log timestamp",
                data_as_of=as_of,
                suggested_review="Contact the client to schedule a routine financial review and reconfirm profile and goals.",
                created_at=datetime.now(timezone.utc).isoformat()
            )
        )
        
    return insights
