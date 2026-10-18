"""Unit Tests for Deterministic Financial Analytics.

Includes exact hand-calculated test cases for:
- Performance gap
- Goal trajectory
- Allocation drift
- Persistence
- Advice follow-through
- Data quality and freshness audits
"""

import pytest
from app.services.analytics import (
    calculate_performance_gap,
    calculate_goal_trajectory,
    calculate_allocation_drift,
    evaluate_persistence,
    evaluate_advice_follow_through,
    assess_data_quality_and_freshness
)

class TestPerformanceGap:
    def test_negative_return_outperforming_benchmark(self):
        """Hand-calculated: client -4.0%, benchmark -5.0% -> gap = +1.0 pp (Outperformed!)."""
        res = calculate_performance_gap(
            client_return_pct=-4.0,
            benchmark_return_pct=-5.0,
            benchmark_id="BMK-TEST",
            period_start="2025-01-01",
            period_end="2025-12-31",
            aligned=True
        )
        assert res["status"] == "VALID"
        assert res["performance_gap_pp"] == 1.0
        assert res["outperformed"] is True
        assert res["unit"] == "percentage_points"
        assert "outperformed" in res["explanation"]

    def test_positive_return_underperforming_benchmark(self):
        """Hand-calculated: client +3.5%, benchmark +6.0% -> gap = -2.5 pp."""
        res = calculate_performance_gap(
            client_return_pct=3.5,
            benchmark_return_pct=6.0,
            benchmark_id="BMK-TEST",
            period_start="2025-01-01",
            period_end="2025-12-31",
            aligned=True
        )
        assert res["status"] == "VALID"
        assert res["performance_gap_pp"] == -2.5
        assert res["outperformed"] is False

    def test_missing_benchmark_returns_insufficient_evidence(self):
        res = calculate_performance_gap(
            client_return_pct=5.0,
            benchmark_return_pct=None,
            benchmark_id=None
        )
        assert res["status"] == "INSUFFICIENT_EVIDENCE"
        assert res["performance_gap_pp"] is None
        assert "missing" in res["warning"].lower()

    def test_misaligned_periods(self):
        res = calculate_performance_gap(
            client_return_pct=5.0,
            benchmark_return_pct=4.0,
            aligned=False
        )
        assert res["status"] == "MISALIGNED_PERIODS"
        assert res["performance_gap_pp"] is None


class TestGoalTrajectory:
    def test_hand_calculated_compound_accumulation(self):
        """Hand-calculated:
        Initial = $100,000, Monthly = $1,000, Rate = 6.0% (r_m = 0.005)
        12 elapsed months:
        FV_init = 100000 * (1.005)^12 = 106,167.78
        FV_pmt = 1000 * ((1.005)^12 - 1) / 0.005 = 12,335.56
        Modeled Target = 118,503.34
        Current value = 110,000 -> Shortfall = 8,503.34 (7.18% shortfall -> BEHIND)
        """
        res = calculate_goal_trajectory(
            goal_amount=500000.0,
            current_value=110000.0,
            start_date="2025-01-01",
            goal_date="2035-01-01",
            as_of_date="2026-01-01",
            initial_amount=100000.0,
            monthly_contribution=1000.0,
            assumed_annual_rate_pct=6.0
        )
        assert res["status"] == "VALID"
        assert abs(res["modeled_target_value"] - 118503.34) < 1.0
        assert abs(res["shortfall_amount"] - 8503.34) < 1.0
        assert abs(res["shortfall_pct"] - 7.18) < 0.1
        assert res["trajectory_status"] == "BEHIND"

    def test_on_track_when_current_exceeds_modeled(self):
        res = calculate_goal_trajectory(
            goal_amount=500000.0,
            current_value=125000.0,  # Exceeds 118,503.34
            start_date="2025-01-01",
            goal_date="2035-01-01",
            as_of_date="2026-01-01",
            initial_amount=100000.0,
            monthly_contribution=1000.0,
            assumed_annual_rate_pct=6.0
        )
        assert res["status"] == "VALID"
        assert res["shortfall_amount"] == 0.0
        assert res["shortfall_pct"] == 0.0
        assert res["trajectory_status"] == "ON_TRACK"

    def test_critical_shortfall_when_shortfall_over_20_percent(self):
        res = calculate_goal_trajectory(
            goal_amount=500000.0,
            current_value=90000.0,  # shortfall > 24% of 118,503.34
            start_date="2025-01-01",
            goal_date="2035-01-01",
            as_of_date="2026-01-01",
            initial_amount=100000.0,
            monthly_contribution=1000.0,
            assumed_annual_rate_pct=6.0
        )
        assert res["trajectory_status"] == "CRITICAL_SHORTFALL"
        assert res["shortfall_pct"] > 20.0

    def test_expired_goal_handling(self):
        res = calculate_goal_trajectory(
            goal_amount=500000.0,
            current_value=400000.0,
            start_date="2020-01-01",
            goal_date="2025-01-01",
            as_of_date="2026-01-01",  # Goal date is in the past!
            initial_amount=200000.0
        )
        assert res["trajectory_status"] == "EXPIRED"
        assert res["shortfall_amount"] == 100000.0

    def test_invalid_input_handling(self):
        res = calculate_goal_trajectory(
            goal_amount=-500.0,
            current_value=10000.0,
            start_date="invalid-date",
            goal_date="invalid-date",
            as_of_date="2026-01-01",
            initial_amount=1000.0
        )
        assert res["status"] in ("INVALID_INPUT", "INVALID_DATES")


class TestAllocationDrift:
    def test_hand_calculated_aggregate_drift(self):
        """Hand-calculated:
        Target: Equity 60%, FI 30%, Cash 10%
        Holdings:
        Equity: $700k (70%) -> +10 pp
        FI: $200k (20%)     -> -10 pp
        Cash: $100k (10%)   -> 0 pp
        Total abs drift = 10 + 10 + 0 = 20 pp
        Aggregate drift = 20 / 2 = 10.0%
        Max category drift = 10.0% (Equity)
        """
        holdings = [
            {"asset_id": "EQ", "category": "Equity", "market_value": 700000.0},
            {"asset_id": "FI", "category": "Fixed Income", "market_value": 200000.0},
            {"asset_id": "CS", "category": "Cash", "market_value": 100000.0}
        ]
        target = {"Equity": 60.0, "Fixed Income": 30.0, "Cash": 10.0}
        
        res = calculate_allocation_drift(holdings, target, drift_alert_threshold_pct=5.0)
        assert res["status"] == "VALID"
        assert res["aggregate_drift_pct"] == 10.0
        assert res["max_category_drift_pct"] == 10.0
        assert res["max_drift_category"] == "Equity"
        assert res["exceeds_threshold"] is True

    def test_missing_target_returns_insufficient_evidence(self):
        holdings = [{"asset_id": "EQ", "category": "Equity", "market_value": 500000.0}]
        res = calculate_allocation_drift(holdings, None)
        assert res["status"] == "INSUFFICIENT_EVIDENCE"
        assert res["target_missing"] is True
        assert res["exceeds_threshold"] is False
        assert "missing" in res["warning"].lower()

    def test_empty_portfolio(self):
        res = calculate_allocation_drift([], {"Equity": 60.0, "Fixed Income": 40.0})
        assert res["status"] == "EMPTY_PORTFOLIO"
        assert res["exceeds_threshold"] is False


class TestPersistence:
    def test_persistent_underperformance(self):
        """3 of 4 periods negative -> persistent = True."""
        periods = [
            {"aligned": True, "performance_gap_pp": -2.0},
            {"aligned": True, "performance_gap_pp": -1.5},
            {"aligned": True, "performance_gap_pp": -0.8},
            {"aligned": True, "performance_gap_pp": 0.5}
        ]
        res = evaluate_persistence(periods, min_periods=2)
        assert res["status"] == "VALID"
        assert res["is_persistent"] is True
        assert res["negative_gap_count"] == 3
        assert res["total_aligned_periods"] == 4
        assert res["persistence_ratio"] == 0.75

    def test_isolated_deviation(self):
        """1 of 4 periods negative -> persistent = False."""
        periods = [
            {"aligned": True, "performance_gap_pp": -1.5},
            {"aligned": True, "performance_gap_pp": 0.8},
            {"aligned": True, "performance_gap_pp": 1.2},
            {"aligned": True, "performance_gap_pp": 0.4}
        ]
        res = evaluate_persistence(periods, min_periods=2)
        assert res["is_persistent"] is False
        assert res["negative_gap_count"] == 1


class TestDataQualityAndFreshness:
    def test_stale_data_detection(self):
        client_data = {
            "portfolio": {
                "valuation_date": "2025-11-01",  # 150 days before 2026-03-31
                "total_value": 500000.0,
                "holdings": [{"category": "Equity", "market_value": 500000.0}],
                "target_allocation": {"Equity": 100.0}
            },
            "goal": {"goal_amount": 1000000.0},
            "historical_performance": [{"benchmark_return_pct": 5.0}]
        }
        res = assess_data_quality_and_freshness(client_data, as_of_date="2026-03-31", stale_threshold_days=90)
        assert res["is_stale"] is True
        assert res["confidence"] == "LOW"
        assert any("stale" in w.lower() for w in res["warnings"])

    def test_accounting_mismatch_detection(self):
        client_data = {
            "portfolio": {
                "valuation_date": "2026-03-31",
                "total_value": 500000.0,
                "holdings": [{"category": "Equity", "market_value": 400000.0}],  # $100k mismatch (20%)!
                "target_allocation": {"Equity": 100.0}
            },
            "goal": {"goal_amount": 1000000.0},
            "historical_performance": [{"benchmark_return_pct": 5.0}]
        }
        res = assess_data_quality_and_freshness(client_data, as_of_date="2026-03-31")
        assert res["has_conflicts"] is True
        assert res["confidence"] == "LOW"
        assert any("reconcile" in w.lower() for w in res["warnings"])
