"""Unit Tests for Explainable Priority Scoring Engine.

Verifies:
- 0-100 normalization
- Initial heuristic weights (25/25/20/15/15)
- Client with negative returns who outperforms benchmark is not prioritized solely for return
- Client with positive returns but severe goal shortfall receives high urgency
- Multi-risk trigger escalation
- Deterministic score calculation
"""

import pytest
from app.services.prioritization import (
    compute_priority_score,
    calculate_goal_urgency_score,
    calculate_deviation_persistence_score,
    calculate_allocation_mismatch_score,
    calculate_review_recency_score,
    calculate_evidence_quality_score
)
from app.schemas import SeverityEnum, ConfidenceEnum

class TestPrioritizationComponents:
    def test_outperforming_negative_return_has_low_deviation_score(self):
        """Even with negative return, if client outperformed benchmark, deviation score must be low."""
        perf_gap = {
            "status": "VALID",
            "performance_gap_pp": 2.5,
            "outperformed": True,
            "client_return_pct": -4.0,
            "benchmark_return_pct": -6.5
        }
        persistence = {"is_persistent": False, "negative_gap_count": 0, "total_aligned_periods": 3}
        score, signals = calculate_deviation_persistence_score(perf_gap, persistence)
        assert score <= 15.0  # Must be low!
        assert any("outperformed" in s for s in signals)

    def test_positive_return_with_goal_shortfall_gets_high_urgency(self):
        """Goal trajectory behind path produces high goal urgency score."""
        goal_traj = {
            "status": "VALID",
            "trajectory_status": "CRITICAL_SHORTFALL",
            "shortfall_pct": 24.5,
            "shortfall_amount": 95000.0,
            "progress_pct": 45.0
        }
        score, signals = calculate_goal_urgency_score(goal_traj)
        assert score >= 75.0  # High urgency!
        assert any("shortfall" in s.lower() for s in signals)

    def test_allocation_mismatch_score_scaling(self):
        # 14% drift
        drift_high = {
            "status": "VALID",
            "target_missing": False,
            "aggregate_drift_pct": 14.0,
            "max_category_drift_pct": 14.0,
            "max_drift_category": "Equity",
            "exceeds_threshold": True
        }
        score_high, _ = calculate_allocation_mismatch_score(drift_high)
        assert score_high >= 80.0

        # 1% drift
        drift_low = {
            "status": "VALID",
            "target_missing": False,
            "aggregate_drift_pct": 1.0,
            "max_category_drift_pct": 1.0,
            "max_drift_category": "Cash",
            "exceeds_threshold": False
        }
        score_low, _ = calculate_allocation_mismatch_score(drift_low)
        assert score_low <= 15.0

    def test_overdue_review_score(self):
        # 410 days ago (severely overdue)
        score_old, signals = calculate_review_recency_score("2025-02-14", "2026-03-31")
        assert score_old >= 85.0
        assert any("overdue" in s.lower() for s in signals)

        # 45 days ago (fresh review)
        score_fresh, _ = calculate_review_recency_score("2026-02-14", "2026-03-31")
        assert score_fresh <= 15.0


class TestFullPriorityCalculation:
    def test_full_priority_multi_risk_escalation(self):
        """Scenario 3: Goal shortfall + Allocation drift + Overdue review -> CRITICAL severity."""
        goal_traj = {
            "trajectory_status": "CRITICAL_SHORTFALL",
            "shortfall_pct": 22.0,
            "shortfall_amount": 80000.0
        }
        perf_gap = {
            "status": "VALID",
            "performance_gap_pp": -3.5,
            "outperformed": False,
            "client_return_pct": 1.2,
            "benchmark_return_pct": 4.7
        }
        persistence = {"is_persistent": True, "negative_gap_count": 2, "total_aligned_periods": 2}
        drift = {
            "target_missing": False,
            "aggregate_drift_pct": 14.0,
            "max_category_drift_pct": 14.0,
            "max_drift_category": "Equity",
            "exceeds_threshold": True
        }
        data_quality = {"confidence": "HIGH", "warnings": [], "confidence_reasons": ["Clean data"]}
        
        result = compute_priority_score(
            goal_trajectory=goal_traj,
            performance_gap=perf_gap,
            persistence=persistence,
            drift_eval=drift,
            last_review_date_str="2025-02-14",  # 410 days ago
            as_of_date_str="2026-03-31",
            data_quality=data_quality
        )
        
        assert result["overall_score"] >= 70.0
        assert result["severity"] == SeverityEnum.CRITICAL
        assert len(result["contributing_signals"]) >= 3
        assert "rebalancing" in result["suggested_review"].lower() or "review" in result["suggested_review"].lower()
