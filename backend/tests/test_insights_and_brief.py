"""Unit Tests for Insights and Advisor Brief Generation.

Verifies:
- Traceability of insight statements to EvidenceItems
- Validated InsightSchema adherence
- Neutral, non-prescriptive review suggestions (no trade orders)
- Advisor brief synthesis and draft watermark
"""

import pytest
from datetime import datetime
from app.services.insights import generate_client_insights
from app.services.advisor_brief import generate_advisor_brief
from app.schemas import InsightTypeEnum, SeverityEnum, ConfidenceEnum

@pytest.fixture
def sample_client_data():
    return {
        "client_id": "CLIENT-003",
        "display_name": "Charles Kensington",
        "risk_profile": "MODERATE",
        "data_as_of": "2026-03-31",
        "last_review_date": "2025-02-14",
        "portfolio": {
            "valuation_date": "2026-03-31",
            "total_value": 700000.0,
            "cash_balance": 70000.0,
            "target_allocation": {"Equity": 50.0, "Fixed Income": 40.0, "Cash": 10.0},
            "holdings": [
                {"category": "Equity", "market_value": 476000.0, "allocation_pct": 68.0},
                {"category": "Fixed Income", "market_value": 154000.0, "allocation_pct": 22.0},
                {"category": "Cash", "market_value": 70000.0, "allocation_pct": 10.0}
            ]
        },
        "goal": {
            "goal_name": "Retirement Security Fund",
            "goal_amount": 1400000.0,
            "goal_date": "2032-12-31"
        },
        "historical_performance": [
            {
                "period_label": "1Y",
                "client_return_pct": 1.2,
                "benchmark_id": "BMK-MODERATE",
                "benchmark_return_pct": 4.7,
                "performance_gap_pp": -3.5,
                "aligned": True
            }
        ],
        "advice_history": []
    }

@pytest.fixture
def sample_analytics_and_prior():
    analytics = {
        "goal_trajectory": {
            "status": "VALID",
            "trajectory_status": "CRITICAL_SHORTFALL",
            "progress_pct": 50.0,
            "modeled_target_value": 850000.0,
            "shortfall_amount": 150000.0,
            "shortfall_pct": 17.65,
            "assumptions_description": "Modeled compound path"
        },
        "allocation_drift": {
            "status": "VALID",
            "target_missing": False,
            "aggregate_drift_pct": 18.0,
            "max_category_drift_pct": 18.0,
            "max_drift_category": "Equity",
            "exceeds_threshold": True,
            "category_drifts": {
                "Equity": {"target_pct": 50.0, "actual_pct": 68.0, "drift_pp": 18.0},
                "Fixed Income": {"target_pct": 40.0, "actual_pct": 22.0, "drift_pp": -18.0}
            },
            "explanation": "Aggregate drift 18.0%"
        },
        "performance_gap": {
            "status": "VALID",
            "performance_gap_pp": -3.5,
            "client_return_pct": 1.2,
            "benchmark_return_pct": 4.7,
            "benchmark_id": "BMK-MODERATE",
            "explanation": "Client lagged benchmark by 3.5 pp"
        },
        "persistence": {
            "status": "VALID",
            "is_persistent": True,
            "negative_gap_count": 2,
            "total_aligned_periods": 2,
            "explanation": "Repeated underperformance"
        },
        "data_quality": {
            "confidence": "HIGH",
            "warnings": [],
            "confidence_reasons": ["Verified records"],
            "requires_verification": False
        },
        "advice_follow_through": {
            "status": "INSUFFICIENT_EVIDENCE",
            "explanation": "No prior advice"
        }
    }
    
    from app.schemas import ScoreComponents
    prioritization = {
        "overall_score": 76.5,
        "score_components": ScoreComponents(
            goal_urgency=85.0,
            deviation_persistence=75.0,
            allocation_mismatch=80.0,
            review_recency=88.0,
            evidence_quality=10.0
        ),
        "severity": SeverityEnum.CRITICAL,
        "confidence_level": ConfidenceEnum.HIGH,
        "confidence_reason": "Verified records",
        "contributing_signals": ["Severe goal shortfall", "Allocation drift", "Review overdue"],
        "suggested_review": "Schedule comprehensive portfolio and goal review"
    }
    
    return analytics, prioritization

def test_generate_client_insights(sample_client_data, sample_analytics_and_prior):
    analytics, prior = sample_analytics_and_prior
    insights = generate_client_insights(sample_client_data, analytics, prior)
    
    assert len(insights) >= 3
    types = [ins.type for ins in insights]
    assert InsightTypeEnum.GOAL_AT_RISK in types
    assert InsightTypeEnum.ALLOCATION_DRIFT in types
    assert InsightTypeEnum.REVIEW_OVERDUE in types
    
    for ins in insights:
        # Check required fields
        assert ins.insight_id.startswith("INSIGHT-")
        assert ins.headline
        assert ins.what_changed
        assert ins.why_it_matters
        assert len(ins.evidence) > 0
        # Check that suggested review is non-prescriptive
        assert "buy" not in ins.suggested_review.lower()
        assert "sell" not in ins.suggested_review.lower()

def test_advisor_brief_generation(sample_client_data, sample_analytics_and_prior):
    analytics, prior = sample_analytics_and_prior
    insights = generate_client_insights(sample_client_data, analytics, prior)
    brief = generate_advisor_brief(sample_client_data, analytics, prior, insights)
    
    assert brief.client_id == "CLIENT-003"
    assert "DRAFT" in brief.draft_notice
    assert brief.executive_summary
    assert len(brief.suggested_review_questions) >= 3
    assert len(brief.evidence) > 0
