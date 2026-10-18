"""Planted Test Scenarios for Deterministic Evaluation.

Documents the 12 explicitly required test scenarios:
1. CLIENT-001: Negative-return client who outperforms benchmark and remains on track.
2. CLIENT-002: Positive-return client whose goal trajectory is deteriorating.
3. CLIENT-003: Behind modeled goal path + allocation drift + overdue review.
4. CLIENT-004: Repeated underperformance over aligned periods (persistent).
5. CLIENT-005: Isolated negative period (previous periods strong).
6. CLIENT-006: Target allocation is missing (insufficient evidence for drift).
7. CLIENT-007: Missing or ambiguous advisor advice.
8. CLIENT-008: Stale portfolio data (>90 days old).
9. CLIENT-009: Missing benchmark data (performance gap cannot be computed).
10. CLIENT-010: Inconsistent / conflicting records (holdings sum != total value).
11. CLIENT-011: Insufficient evidence to support a reliable alert (uninitialized).
12. CLIENT-012 to CLIENT-020: Normal, non-actionable financial conditions.
"""

from typing import Dict, Any, List

PLANTED_SCENARIOS: Dict[str, Dict[str, Any]] = {
    "CLIENT-001": {
        "scenario_number": 1,
        "name": "Negative Return But On Track",
        "description": "Client has negative return (-4.2%) but outperforms benchmark (-6.5%) by +2.3 pp and goal is on track.",
        "ground_truth_urgent_review": False,  # Should NOT be urgent despite negative return!
        "expected_performance_gap_pp": 2.3,
        "expected_trajectory_status": "ON_TRACK",
        "expected_drift_exceeded": False,
        "expected_severity": "LOW"
    },
    "CLIENT-002": {
        "scenario_number": 2,
        "name": "Positive Return But Deteriorating Goal",
        "description": "Client has positive return (+5.1%), but goal trajectory has severe shortfall (-22.5%) vs modeled path.",
        "ground_truth_urgent_review": True,  # Critical to catch; return-only ranking completely misses this!
        "expected_performance_gap_pp": -1.2,
        "expected_trajectory_status": "CRITICAL_SHORTFALL",
        "expected_drift_exceeded": False,
        "expected_severity": "HIGH"
    },
    "CLIENT-003": {
        "scenario_number": 3,
        "name": "Goal Shortfall + Allocation Drift + Overdue Review",
        "description": "Client is behind goal path, has 14% aggregate allocation drift, and review is 410 days overdue.",
        "ground_truth_urgent_review": True,  # Highest urgency case
        "expected_performance_gap_pp": -3.5,
        "expected_trajectory_status": "CRITICAL_SHORTFALL",
        "expected_drift_exceeded": True,
        "expected_severity": "CRITICAL"
    },
    "CLIENT-004": {
        "scenario_number": 4,
        "name": "Persistent Benchmark Underperformance",
        "description": "Client underperformed benchmark across all 4 historical periods (1M, 3M, 6M, 1Y).",
        "ground_truth_urgent_review": True,
        "expected_performance_gap_pp": -4.2,
        "expected_persistence": True,
        "expected_severity": "HIGH"
    },
    "CLIENT-005": {
        "scenario_number": 5,
        "name": "Isolated Negative Period",
        "description": "Client had a negative 1M dip (-2.1 pp) but 3M, 6M, and 1Y periods all outperformed benchmark.",
        "ground_truth_urgent_review": False,  # Market noise; not persistent
        "expected_performance_gap_pp": -2.1,
        "expected_persistence": False,
        "expected_severity": "LOW"
    },
    "CLIENT-006": {
        "scenario_number": 6,
        "name": "Missing Target Allocation",
        "description": "Portfolio has holdings but target allocation is missing. Drift evaluation returns insufficient evidence.",
        "ground_truth_urgent_review": False,  # Verification required, but not urgent portfolio risk
        "expected_target_missing": True,
        "expected_severity": "MEDIUM"
    },
    "CLIENT-007": {
        "scenario_number": 7,
        "name": "Missing / Ambiguous Advisor Advice",
        "description": "No prior advice records exist. Advice follow-through reports insufficient evidence.",
        "ground_truth_urgent_review": False,
        "expected_advice_missing": True,
        "expected_severity": "LOW"
    },
    "CLIENT-008": {
        "scenario_number": 8,
        "name": "Stale Portfolio Snapshot",
        "description": "Valuation date is 140 days old (>90 days). Triggers data quality verification warning.",
        "ground_truth_urgent_review": True,  # Requires data refresh before any action
        "expected_is_stale": True,
        "expected_confidence": "LOW",
        "expected_severity": "HIGH"
    },
    "CLIENT-009": {
        "scenario_number": 9,
        "name": "Missing Benchmark Data",
        "description": "Benchmark return data is absent for client risk profile. Performance gap reports insufficient evidence.",
        "ground_truth_urgent_review": False,
        "expected_benchmark_missing": True,
        "expected_confidence": "MEDIUM"
    },
    "CLIENT-010": {
        "scenario_number": 10,
        "name": "Inconsistent Conflicting Records",
        "description": "Holdings sum to $420,000 but reported total value is $500,000 (16% accounting mismatch).",
        "ground_truth_urgent_review": True,  # Accounting conflict must be verified immediately
        "expected_has_conflicts": True,
        "expected_confidence": "LOW",
        "expected_severity": "HIGH"
    },
    "CLIENT-011": {
        "scenario_number": 11,
        "name": "Insufficient Evidence Alert",
        "description": "Uninitialized new account with empty holdings and missing assumptions.",
        "ground_truth_urgent_review": False,
        "expected_empty_portfolio": True,
        "expected_confidence": "LOW"
    },
    "CLIENT-012": {
        "scenario_number": 12,
        "name": "Normal On-Track Client A",
        "description": "Balanced portfolio, goal on track, reviewed 45 days ago, outperforming benchmark.",
        "ground_truth_urgent_review": False,
        "expected_severity": "LOW"
    }
}
