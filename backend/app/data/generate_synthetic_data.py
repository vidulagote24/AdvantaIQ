"""Synthetic Dataset Generator.

Generates ~200 reproducible fictional clients using deterministic random seed 42.
Plants the 12 specified test scenarios with fixed client IDs (CLIENT-001 to CLIENT-012)
and generates realistic distributions for all remaining clients.
"""

import random
from datetime import datetime, date, timedelta, timezone
from typing import Dict, List, Any, Optional

FIRST_NAMES = [
    "Alexander", "Beatrix", "Charles", "Diana", "Edward", "Fiona", "George", "Helena",
    "Ian", "Julia", "Kenneth", "Lillian", "Marcus", "Nora", "Oliver", "Penelope",
    "Quentin", "Rosalind", "Sebastian", "Theresa", "Ulrich", "Valerie", "Winston", "Xenia",
    "Arthur", "Clara", "David", "Eleanor", "Felix", "Grace", "Henry", "Isabel",
    "Jasper", "Kavita", "Liam", "Maya", "Nathan", "Olivia", "Philip", "Rachel"
]

LAST_NAMES = [
    "Vance", "Sterling", "Montgomery", "Sinclair", "Hawthorne", "Kensington", "Blackwood",
    "Harrington", "Pemberton", "Fairfax", "Cromwell", "Waverly", "Prescott", "Aldridge",
    "Winslow", "Bradford", "Carrington", "Somerset", "Langley", "Beaumont", "Chen",
    "Patel", "Gupta", "Tanaka", "Larsson", "Dubois", "Moretti", "Castillo", "Kim", "O'Connor"
]

GOAL_TEMPLATES = [
    ("Retirement Security Fund", 1200000, 2038),
    ("Family Legacy Trust", 2500000, 2045),
    ("Next-Gen Education Endowment", 350000, 2032),
    ("Primary Residence Acquisition", 650000, 2028),
    ("Philanthropic Foundation Launch", 1800000, 2040),
    ("Early Financial Independence", 1500000, 2035),
    ("Private Enterprise Succession Fund", 3000000, 2042),
    ("Vacation Estate Milestone", 850000, 2030)
]

RISK_PROFILES = {
    "CONSERVATIVE": {
        "target_allocation": {"Equity": 30.0, "Fixed Income": 55.0, "Cash": 15.0},
        "benchmark_id": "BMK-CONSERVATIVE",
        "benchmark_name": "Conservative 30/70 Composite",
        "expected_return": 4.5
    },
    "MODERATE": {
        "target_allocation": {"Equity": 50.0, "Fixed Income": 40.0, "Cash": 10.0},
        "benchmark_id": "BMK-MODERATE",
        "benchmark_name": "Moderate 50/50 Balanced Index",
        "expected_return": 6.0
    },
    "GROWTH": {
        "target_allocation": {"Equity": 70.0, "Fixed Income": 22.0, "Cash": 8.0},
        "benchmark_id": "BMK-GROWTH",
        "benchmark_name": "Growth 70/30 Blend Index",
        "expected_return": 7.5
    },
    "AGGRESSIVE": {
        "target_allocation": {"Equity": 85.0, "Fixed Income": 10.0, "Cash": 5.0},
        "benchmark_id": "BMK-AGGRESSIVE",
        "benchmark_name": "Global Equity 85/15 Index",
        "expected_return": 9.0
    }
}

ASSET_CATALOG = {
    "Equity": [
        ("EQ-01", "Global Large-Cap Equity Fund", ["EQUITY", "CORE_INDEX"]),
        ("EQ-02", "US Broad Market Index ETF", ["EQUITY", "DOMESTIC"]),
        ("EQ-03", "International Developed Markets ETF", ["EQUITY", "INTERNATIONAL"]),
        ("EQ-04", "Emerging Markets Growth Fund", ["EQUITY", "HIGH_VOLATILITY"]),
        ("EQ-05", "Dividend Aristocrats Equity Fund", ["EQUITY", "INCOME"]),
    ],
    "Fixed Income": [
        ("FI-01", "Core US Aggregate Bond Fund", ["FIXED_INCOME", "INVESTMENT_GRADE"]),
        ("FI-02", "Treasury Inflation-Protected (TIPS) ETF", ["FIXED_INCOME", "GOVERNMENT"]),
        ("FI-03", "Short-Duration Corporate Bond ETF", ["FIXED_INCOME", "SHORT_DURATION"]),
        ("FI-04", "High Yield Opportunity Fund", ["FIXED_INCOME", "CREDIT_SPREAD"]),
        ("FI-05", "Municipal Tax-Exempt Bond Fund", ["FIXED_INCOME", "TAX_ADVANTAGED"]),
    ],
    "Cash": [
        ("CS-01", "Treasury Money Market Fund", ["CASH_EQUIVALENT", "LOW_RISK"]),
        ("CS-02", "High-Yield Custodial Cash Deposit", ["CASH_EQUIVALENT", "LIQUID"]),
    ],
    "Alternative": [
        ("AL-01", "Real Estate Infrastructure REIT Fund", ["REAL_ESTATE", "ALTERNATIVE"]),
        ("AL-02", "Diversified Commodities Strategy Fund", ["COMMODITIES", "INFLATION_HEDGE"]),
    ]
}

def generate_holdings_for_allocation(
    total_value: float,
    allocation: Dict[str, float],
    rng: random.Random
) -> List[Dict[str, Any]]:
    """Creates individual holdings matching a given category allocation."""
    holdings: List[Dict[str, Any]] = []
    
    for category, target_pct in allocation.items():
        if target_pct <= 0:
            continue
        cat_val = total_value * (target_pct / 100.0)
        assets = ASSET_CATALOG.get(category, ASSET_CATALOG["Equity"])
        # Split across 1 to 2 assets in this category
        num_assets = min(len(assets), 2 if target_pct > 20 else 1)
        sub_assets = rng.sample(assets, num_assets)
        
        remaining_val = cat_val
        for i, (asset_id, asset_name, tags) in enumerate(sub_assets):
            if i == num_assets - 1:
                val = remaining_val
            else:
                share = rng.uniform(0.4, 0.6)
                val = round(cat_val * share, 2)
                remaining_val -= val
                
            val = round(val, 2)
            pct = round((val / total_value) * 100.0, 2) if total_value > 0 else 0.0
            holdings.append({
                "asset_id": asset_id,
                "asset_name": asset_name,
                "category": category,
                "market_value": val,
                "allocation_pct": pct,
                "risk_tags": tags
            })
            
    # Adjust last holding for exact rounding match
    current_sum = sum(h["market_value"] for h in holdings)
    if holdings and abs(current_sum - total_value) > 0.01:
        diff = round(total_value - current_sum, 2)
        holdings[-1]["market_value"] = round(holdings[-1]["market_value"] + diff, 2)
        holdings[-1]["allocation_pct"] = round((holdings[-1]["market_value"] / total_value) * 100.0, 2)
        
    return holdings

def generate_synthetic_dataset(num_clients: int = 200, seed: int = 42) -> Dict[str, Any]:
    """Generates the full synthetic dataset with planted scenarios."""
    rng = random.Random(seed)
    as_of_date = "2026-03-31"  # Standard demonstration baseline date
    
    clients: List[Dict[str, Any]] = []
    
    # ----------------------------------------------------
    # Planted Scenario 1: CLIENT-001
    # Negative return (-4.2%) but outperforms benchmark (-6.5%) by +2.3 pp; goal on track
    # ----------------------------------------------------
    clients.append({
        "client_id": "CLIENT-001",
        "display_name": "Arthur Vance",
        "risk_profile": "MODERATE",
        "data_as_of": as_of_date,
        "last_review_date": "2026-01-15",
        "planted_scenario_id": "SCENARIO-01",
        "portfolio": {
            "valuation_date": "2026-03-31",
            "total_value": 780000.0,
            "cash_balance": 78000.0,
            "target_allocation": {"Equity": 50.0, "Fixed Income": 40.0, "Cash": 10.0},
            "holdings": generate_holdings_for_allocation(
                780000.0, {"Equity": 50.0, "Fixed Income": 40.0, "Cash": 10.0}, rng
            ),
            "is_stale": False,
            "data_warnings": []
        },
        "goal": {
            "goal_name": "Retirement Security Fund",
            "goal_amount": 1200000.0,
            "start_date": "2021-01-01",
            "goal_date": "2035-12-31",
            "initial_amount": 500000.0,
            "monthly_contribution": 1000.0,  # Modeled target at 63 months is ~$758k < $780k -> ON_TRACK
            "assumed_annual_rate_pct": 6.0
        },
        "historical_performance": [
            {
                "period_label": "1Y",
                "period_start": "2025-04-01",
                "period_end": "2026-03-31",
                "client_return_pct": -4.2,
                "benchmark_id": "BMK-MODERATE",
                "benchmark_name": "Moderate 50/50 Balanced Index",
                "benchmark_return_pct": -6.5,
                "performance_gap_pp": 2.3,
                "aligned": True
            },
            {
                "period_label": "6M",
                "period_start": "2025-10-01",
                "period_end": "2026-03-31",
                "client_return_pct": -1.8,
                "benchmark_id": "BMK-MODERATE",
                "benchmark_name": "Moderate 50/50 Balanced Index",
                "benchmark_return_pct": -3.0,
                "performance_gap_pp": 1.2,
                "aligned": True
            },
            {
                "period_label": "3M",
                "period_start": "2026-01-01",
                "period_end": "2026-03-31",
                "client_return_pct": 0.5,
                "benchmark_id": "BMK-MODERATE",
                "benchmark_name": "Moderate 50/50 Balanced Index",
                "benchmark_return_pct": -0.2,
                "performance_gap_pp": 0.7,
                "aligned": True
            }
        ],
        "advice_history": [
            {
                "advice_id": "ADV-001",
                "recording_date": "2026-01-15",
                "advice_text": "Maintain defensive positioning in Fixed Income; preserve 10% cash buffer.",
                "expected_outcome": "Capital preservation during anticipated market correction.",
                "review_horizon_days": 180,
                "target_allocation": {"Equity": 50.0, "Fixed Income": 40.0, "Cash": 10.0},
                "status": "implemented"
            }
        ]
    })
    
    # ----------------------------------------------------
    # Planted Scenario 2: CLIENT-002
    # Positive return (+5.1%), but goal trajectory has severe shortfall (-43.4%) vs modeled path
    # ----------------------------------------------------
    clients.append({
        "client_id": "CLIENT-002",
        "display_name": "Beatrix Montgomery",
        "risk_profile": "GROWTH",
        "data_as_of": as_of_date,
        "last_review_date": "2025-07-10",  # Overdue review (264 days)
        "planted_scenario_id": "SCENARIO-02",
        "portfolio": {
            "valuation_date": "2026-03-31",
            "total_value": 410000.0,
            "cash_balance": 32800.0,
            "target_allocation": {"Equity": 70.0, "Fixed Income": 22.0, "Cash": 8.0},
            "holdings": generate_holdings_for_allocation(
                410000.0, {"Equity": 70.0, "Fixed Income": 22.0, "Cash": 8.0}, rng
            ),
            "is_stale": False,
            "data_warnings": []
        },
        "goal": {
            "goal_name": "Early Financial Independence",
            "goal_amount": 1500000.0,
            "start_date": "2020-01-01",
            "goal_date": "2030-12-31",
            "initial_amount": 250000.0,
            "monthly_contribution": 3500.0,
            "assumed_annual_rate_pct": 7.5
        },
        "historical_performance": [
            {
                "period_label": "1Y",
                "period_start": "2025-04-01",
                "period_end": "2026-03-31",
                "client_return_pct": 5.1,
                "benchmark_id": "BMK-GROWTH",
                "benchmark_name": "Growth 70/30 Blend Index",
                "benchmark_return_pct": 6.3,
                "performance_gap_pp": -1.2,
                "aligned": True
            },
            {
                "period_label": "6M",
                "period_start": "2025-10-01",
                "period_end": "2026-03-31",
                "client_return_pct": 3.0,
                "benchmark_id": "BMK-GROWTH",
                "benchmark_name": "Growth 70/30 Blend Index",
                "benchmark_return_pct": 3.5,
                "performance_gap_pp": -0.5,
                "aligned": True
            }
        ],
        "advice_history": [
            {
                "advice_id": "ADV-002",
                "recording_date": "2025-07-10",
                "advice_text": "Increase monthly deposits to $3,500 to maintain required accumulation trajectory.",
                "expected_outcome": "Close modeled shortfall before 2030 target date.",
                "review_horizon_days": 180,
                "target_allocation": {"Equity": 70.0, "Fixed Income": 22.0, "Cash": 8.0},
                "status": "pending"
            }
        ]
    })
    
    # ----------------------------------------------------
    # Planted Scenario 3: CLIENT-003
    # Goal Shortfall + Allocation Drift (18% aggregate) + Overdue Review (410 days)
    # ----------------------------------------------------
    drift_holdings = [
        {"asset_id": "EQ-01", "asset_name": "Global Large-Cap Equity Fund", "category": "Equity", "market_value": 476000.0, "allocation_pct": 68.0, "risk_tags": ["EQUITY"]},
        {"asset_id": "FI-01", "asset_name": "Core US Aggregate Bond Fund", "category": "Fixed Income", "market_value": 154000.0, "allocation_pct": 22.0, "risk_tags": ["FIXED_INCOME"]},
        {"asset_id": "CS-01", "asset_name": "Treasury Money Market Fund", "category": "Cash", "market_value": 70000.0, "allocation_pct": 10.0, "risk_tags": ["CASH_EQUIVALENT"]}
    ]
    clients.append({
        "client_id": "CLIENT-003",
        "display_name": "Charles Kensington",
        "risk_profile": "MODERATE",
        "data_as_of": as_of_date,
        "last_review_date": "2025-02-14",  # 410 days ago!
        "planted_scenario_id": "SCENARIO-03",
        "portfolio": {
            "valuation_date": "2026-03-31",
            "total_value": 700000.0,
            "cash_balance": 70000.0,
            "target_allocation": {"Equity": 50.0, "Fixed Income": 40.0, "Cash": 10.0},
            "holdings": drift_holdings,
            "is_stale": False,
            "data_warnings": []
        },
        "goal": {
            "goal_name": "Retirement Security Fund",
            "goal_amount": 1400000.0,
            "start_date": "2020-01-01",
            "goal_date": "2032-12-31",
            "initial_amount": 450000.0,
            "monthly_contribution": 3000.0,  # Modeled target is ~$980k -> Shortfall 28.5% -> CRITICAL_SHORTFALL
            "assumed_annual_rate_pct": 6.0
        },
        "historical_performance": [
            {
                "period_label": "1Y",
                "period_start": "2025-04-01",
                "period_end": "2026-03-31",
                "client_return_pct": 1.2,
                "benchmark_id": "BMK-MODERATE",
                "benchmark_name": "Moderate 50/50 Balanced Index",
                "benchmark_return_pct": 4.7,
                "performance_gap_pp": -3.5,
                "aligned": True
            },
            {
                "period_label": "6M",
                "period_start": "2025-10-01",
                "period_end": "2026-03-31",
                "client_return_pct": 0.4,
                "benchmark_id": "BMK-MODERATE",
                "benchmark_name": "Moderate 50/50 Balanced Index",
                "benchmark_return_pct": 2.8,
                "performance_gap_pp": -2.4,
                "aligned": True
            }
        ],
        "advice_history": [
            {
                "advice_id": "ADV-003",
                "recording_date": "2025-02-14",
                "advice_text": "Rebalance portfolio back to 50% Equity, 40% Fixed Income target model.",
                "expected_outcome": "Restore moderate risk tolerance and prevent equity concentration risk.",
                "review_horizon_days": 180,
                "target_allocation": {"Equity": 50.0, "Fixed Income": 40.0, "Cash": 10.0},
                "status": "pending"
            }
        ]
    })
    
    # ----------------------------------------------------
    # Planted Scenario 4: CLIENT-004
    # Repeated underperformance over aligned periods (persistent underperformer)
    # ----------------------------------------------------
    clients.append({
        "client_id": "CLIENT-004",
        "display_name": "Diana Hawthorne",
        "risk_profile": "GROWTH",
        "data_as_of": as_of_date,
        "last_review_date": "2025-11-20",
        "planted_scenario_id": "SCENARIO-04",
        "portfolio": {
            "valuation_date": "2026-03-31",
            "total_value": 920000.0,
            "cash_balance": 73600.0,
            "target_allocation": {"Equity": 70.0, "Fixed Income": 22.0, "Cash": 8.0},
            "holdings": generate_holdings_for_allocation(
                920000.0, {"Equity": 70.0, "Fixed Income": 22.0, "Cash": 8.0}, rng
            ),
            "is_stale": False,
            "data_warnings": []
        },
        "goal": {
            "goal_name": "Family Legacy Trust",
            "goal_amount": 2000000.0,
            "start_date": "2022-01-01",
            "goal_date": "2040-12-31",
            "initial_amount": 750000.0,
            "monthly_contribution": 1500.0,
            "assumed_annual_rate_pct": 7.5
        },
        "historical_performance": [
            {
                "period_label": "1Y",
                "period_start": "2025-04-01",
                "period_end": "2026-03-31",
                "client_return_pct": 2.1,
                "benchmark_id": "BMK-GROWTH",
                "benchmark_name": "Growth 70/30 Blend Index",
                "benchmark_return_pct": 6.3,
                "performance_gap_pp": -4.2,
                "aligned": True
            },
            {
                "period_label": "6M",
                "period_start": "2025-10-01",
                "period_end": "2026-03-31",
                "client_return_pct": 0.8,
                "benchmark_id": "BMK-GROWTH",
                "benchmark_name": "Growth 70/30 Blend Index",
                "benchmark_return_pct": 3.5,
                "performance_gap_pp": -2.7,
                "aligned": True
            },
            {
                "period_label": "3M",
                "period_start": "2026-01-01",
                "period_end": "2026-03-31",
                "client_return_pct": -0.5,
                "benchmark_id": "BMK-GROWTH",
                "benchmark_name": "Growth 70/30 Blend Index",
                "benchmark_return_pct": 1.2,
                "performance_gap_pp": -1.7,
                "aligned": True
            },
            {
                "period_label": "1M",
                "period_start": "2026-03-01",
                "period_end": "2026-03-31",
                "client_return_pct": -0.8,
                "benchmark_id": "BMK-GROWTH",
                "benchmark_name": "Growth 70/30 Blend Index",
                "benchmark_return_pct": 0.4,
                "performance_gap_pp": -1.2,
                "aligned": True
            }
        ],
        "advice_history": []
    })
    
    # ----------------------------------------------------
    # Planted Scenario 5: CLIENT-005
    # Isolated negative period (temporary 1M dip of -2.1 pp; previous periods strong)
    # ----------------------------------------------------
    clients.append({
        "client_id": "CLIENT-005",
        "display_name": "Edward Blackwood",
        "risk_profile": "GROWTH",
        "data_as_of": as_of_date,
        "last_review_date": "2026-01-20",
        "planted_scenario_id": "SCENARIO-05",
        "portfolio": {
            "valuation_date": "2026-03-31",
            "total_value": 650000.0,
            "cash_balance": 52000.0,
            "target_allocation": {"Equity": 70.0, "Fixed Income": 22.0, "Cash": 8.0},
            "holdings": generate_holdings_for_allocation(
                650000.0, {"Equity": 70.0, "Fixed Income": 22.0, "Cash": 8.0}, rng
            ),
            "is_stale": False,
            "data_warnings": []
        },
        "goal": {
            "goal_name": "Retirement Security Fund",
            "goal_amount": 1100000.0,
            "start_date": "2021-01-01",
            "goal_date": "2036-12-31",
            "initial_amount": 400000.0,
            "monthly_contribution": 1800.0,
            "assumed_annual_rate_pct": 7.5
        },
        "historical_performance": [
            {
                "period_label": "1M",
                "period_start": "2026-03-01",
                "period_end": "2026-03-31",
                "client_return_pct": -1.7,
                "benchmark_id": "BMK-GROWTH",
                "benchmark_name": "Growth 70/30 Blend Index",
                "benchmark_return_pct": 0.4,
                "performance_gap_pp": -2.1,
                "aligned": True
            },
            {
                "period_label": "1Y",
                "period_start": "2025-04-01",
                "period_end": "2026-03-31",
                "client_return_pct": 7.8,
                "benchmark_id": "BMK-GROWTH",
                "benchmark_name": "Growth 70/30 Blend Index",
                "benchmark_return_pct": 6.3,
                "performance_gap_pp": 1.5,
                "aligned": True
            },
            {
                "period_label": "6M",
                "period_start": "2025-10-01",
                "period_end": "2026-03-31",
                "client_return_pct": 4.1,
                "benchmark_id": "BMK-GROWTH",
                "benchmark_name": "Growth 70/30 Blend Index",
                "benchmark_return_pct": 3.5,
                "performance_gap_pp": 0.6,
                "aligned": True
            }
        ],
        "advice_history": []
    })
    
    # ----------------------------------------------------
    # Planted Scenario 6: CLIENT-006
    # Target allocation is missing
    # ----------------------------------------------------
    clients.append({
        "client_id": "CLIENT-006",
        "display_name": "Fiona Harrington",
        "risk_profile": "MODERATE",
        "data_as_of": as_of_date,
        "last_review_date": "2025-12-05",
        "planted_scenario_id": "SCENARIO-06",
        "portfolio": {
            "valuation_date": "2026-03-31",
            "total_value": 520000.0,
            "cash_balance": 40000.0,
            "target_allocation": None,  # MISSING TARGET ALLOCATION
            "holdings": [
                {"asset_id": "EQ-01", "asset_name": "Global Large-Cap Equity Fund", "category": "Equity", "market_value": 260000.0, "allocation_pct": 50.0, "risk_tags": ["EQUITY"]},
                {"asset_id": "FI-01", "asset_name": "Core US Aggregate Bond Fund", "category": "Fixed Income", "market_value": 220000.0, "allocation_pct": 42.31, "risk_tags": ["FIXED_INCOME"]},
                {"asset_id": "CS-01", "asset_name": "Treasury Money Market Fund", "category": "Cash", "market_value": 40000.0, "allocation_pct": 7.69, "risk_tags": ["CASH_EQUIVALENT"]}
            ],
            "is_stale": False,
            "data_warnings": ["Target allocation missing"]
        },
        "goal": {
            "goal_name": "Primary Residence Acquisition",
            "goal_amount": 650000.0,
            "start_date": "2023-01-01",
            "goal_date": "2028-12-31",
            "initial_amount": 300000.0,
            "monthly_contribution": 2000.0,
            "assumed_annual_rate_pct": 6.0
        },
        "historical_performance": [
            {
                "period_label": "1Y",
                "period_start": "2025-04-01",
                "period_end": "2026-03-31",
                "client_return_pct": 4.9,
                "benchmark_id": "BMK-MODERATE",
                "benchmark_name": "Moderate 50/50 Balanced Index",
                "benchmark_return_pct": 4.7,
                "performance_gap_pp": 0.2,
                "aligned": True
            }
        ],
        "advice_history": []
    })
    
    # ----------------------------------------------------
    # Planted Scenario 7: CLIENT-007
    # Missing / ambiguous advisor advice
    # ----------------------------------------------------
    clients.append({
        "client_id": "CLIENT-007",
        "display_name": "George Pemberton",
        "risk_profile": "CONSERVATIVE",
        "data_as_of": as_of_date,
        "last_review_date": "2026-02-10",
        "planted_scenario_id": "SCENARIO-07",
        "portfolio": {
            "valuation_date": "2026-03-31",
            "total_value": 890000.0,
            "cash_balance": 133500.0,
            "target_allocation": {"Equity": 30.0, "Fixed Income": 55.0, "Cash": 15.0},
            "holdings": generate_holdings_for_allocation(
                890000.0, {"Equity": 30.0, "Fixed Income": 55.0, "Cash": 15.0}, rng
            ),
            "is_stale": False,
            "data_warnings": []
        },
        "goal": {
            "goal_name": "Retirement Security Fund",
            "goal_amount": 1000000.0,
            "start_date": "2022-01-01",
            "goal_date": "2030-12-31",
            "initial_amount": 700000.0,
            "monthly_contribution": 1000.0,
            "assumed_annual_rate_pct": 4.5
        },
        "historical_performance": [
            {
                "period_label": "1Y",
                "period_start": "2025-04-01",
                "period_end": "2026-03-31",
                "client_return_pct": 3.8,
                "benchmark_id": "BMK-CONSERVATIVE",
                "benchmark_name": "Conservative 30/70 Composite",
                "benchmark_return_pct": 3.6,
                "performance_gap_pp": 0.2,
                "aligned": True
            }
        ],
        "advice_history": []  # Empty advice history
    })
    
    # ----------------------------------------------------
    # Planted Scenario 8: CLIENT-008
    # Stale portfolio data (>90 days old)
    # ----------------------------------------------------
    clients.append({
        "client_id": "CLIENT-008",
        "display_name": "Helena Fairfax",
        "risk_profile": "MODERATE",
        "data_as_of": as_of_date,
        "last_review_date": "2025-09-01",
        "planted_scenario_id": "SCENARIO-08",
        "portfolio": {
            "valuation_date": "2025-11-10",  # 141 days before 2026-03-31! STALE!
            "total_value": 640000.0,
            "cash_balance": 64000.0,
            "target_allocation": {"Equity": 50.0, "Fixed Income": 40.0, "Cash": 10.0},
            "holdings": generate_holdings_for_allocation(
                640000.0, {"Equity": 50.0, "Fixed Income": 40.0, "Cash": 10.0}, rng
            ),
            "is_stale": True,
            "data_warnings": ["Portfolio snapshot is stale (141 days old)"]
        },
        "goal": {
            "goal_name": "Retirement Security Fund",
            "goal_amount": 950000.0,
            "start_date": "2021-01-01",
            "goal_date": "2033-12-31",
            "initial_amount": 450000.0,
            "monthly_contribution": 1500.0,
            "assumed_annual_rate_pct": 6.0
        },
        "historical_performance": [
            {
                "period_label": "1Y",
                "period_start": "2024-11-01",
                "period_end": "2025-11-10",
                "client_return_pct": 4.2,
                "benchmark_id": "BMK-MODERATE",
                "benchmark_name": "Moderate 50/50 Balanced Index",
                "benchmark_return_pct": 4.5,
                "performance_gap_pp": -0.3,
                "aligned": True
            }
        ],
        "advice_history": []
    })
    
    # ----------------------------------------------------
    # Planted Scenario 9: CLIENT-009
    # Missing benchmark data
    # ----------------------------------------------------
    clients.append({
        "client_id": "CLIENT-009",
        "display_name": "Ian Cromwell",
        "risk_profile": "AGGRESSIVE",
        "data_as_of": as_of_date,
        "last_review_date": "2026-01-10",
        "planted_scenario_id": "SCENARIO-09",
        "portfolio": {
            "valuation_date": "2026-03-31",
            "total_value": 1150000.0,
            "cash_balance": 57500.0,
            "target_allocation": {"Equity": 85.0, "Fixed Income": 10.0, "Cash": 5.0},
            "holdings": generate_holdings_for_allocation(
                1150000.0, {"Equity": 85.0, "Fixed Income": 10.0, "Cash": 5.0}, rng
            ),
            "is_stale": False,
            "data_warnings": ["Benchmark comparison missing"]
        },
        "goal": {
            "goal_name": "Private Enterprise Succession Fund",
            "goal_amount": 3000000.0,
            "start_date": "2022-01-01",
            "goal_date": "2042-12-31",
            "initial_amount": 800000.0,
            "monthly_contribution": 3000.0,
            "assumed_annual_rate_pct": 9.0
        },
        "historical_performance": [
            {
                "period_label": "1Y",
                "period_start": "2025-04-01",
                "period_end": "2026-03-31",
                "client_return_pct": 8.5,
                "benchmark_id": None,  # MISSING BENCHMARK
                "benchmark_name": None,
                "benchmark_return_pct": None,
                "performance_gap_pp": None,
                "aligned": False
            }
        ],
        "advice_history": []
    })
    
    # ----------------------------------------------------
    # Planted Scenario 10: CLIENT-010
    # Inconsistent or conflicting records (holdings sum $420k != total value $500k)
    # ----------------------------------------------------
    mismatched_holdings = [
        {"asset_id": "EQ-01", "asset_name": "Global Large-Cap Equity Fund", "category": "Equity", "market_value": 250000.0, "allocation_pct": 50.0, "risk_tags": ["EQUITY"]},
        {"asset_id": "FI-01", "asset_name": "Core US Aggregate Bond Fund", "category": "Fixed Income", "market_value": 140000.0, "allocation_pct": 28.0, "risk_tags": ["FIXED_INCOME"]},
        {"asset_id": "CS-01", "asset_name": "Treasury Money Market Fund", "category": "Cash", "market_value": 30000.0, "allocation_pct": 6.0, "risk_tags": ["CASH_EQUIVALENT"]}
    ]  # Sum = $420,000; total_value is set to $500,000 (16% difference!)
    clients.append({
        "client_id": "CLIENT-010",
        "display_name": "Julia Waverly",
        "risk_profile": "MODERATE",
        "data_as_of": as_of_date,
        "last_review_date": "2025-11-15",
        "planted_scenario_id": "SCENARIO-10",
        "portfolio": {
            "valuation_date": "2026-03-31",
            "total_value": 500000.0,  # MISMATCH
            "cash_balance": 30000.0,
            "target_allocation": {"Equity": 50.0, "Fixed Income": 40.0, "Cash": 10.0},
            "holdings": mismatched_holdings,
            "is_stale": False,
            "data_warnings": ["Holdings sum ($420,000) does not reconcile with total portfolio value ($500,000)"]
        },
        "goal": {
            "goal_name": "Retirement Security Fund",
            "goal_amount": 1000000.0,
            "start_date": "2021-01-01",
            "goal_date": "2035-12-31",
            "initial_amount": 350000.0,
            "monthly_contribution": 1500.0,
            "assumed_annual_rate_pct": 6.0
        },
        "historical_performance": [
            {
                "period_label": "1Y",
                "period_start": "2025-04-01",
                "period_end": "2026-03-31",
                "client_return_pct": 4.1,
                "benchmark_id": "BMK-MODERATE",
                "benchmark_name": "Moderate 50/50 Balanced Index",
                "benchmark_return_pct": 4.7,
                "performance_gap_pp": -0.6,
                "aligned": True
            }
        ],
        "advice_history": []
    })
    
    # ----------------------------------------------------
    # Planted Scenario 11: CLIENT-011
    # Insufficient evidence to support a reliable alert (uninitialized account)
    # ----------------------------------------------------
    clients.append({
        "client_id": "CLIENT-011",
        "display_name": "Kenneth Prescott",
        "risk_profile": "MODERATE",
        "data_as_of": as_of_date,
        "last_review_date": "2026-03-25",
        "planted_scenario_id": "SCENARIO-11",
        "portfolio": {
            "valuation_date": "2026-03-31",
            "total_value": 0.0,
            "cash_balance": 0.0,
            "target_allocation": {"Equity": 50.0, "Fixed Income": 40.0, "Cash": 10.0},
            "holdings": [],  # EMPTY HOLDINGS
            "is_stale": False,
            "data_warnings": ["Portfolio holdings are empty"]
        },
        "goal": {
            "goal_name": "Retirement Security Fund",
            "goal_amount": 0.0,  # INVALID/UNINITIALIZED GOAL
            "start_date": "2026-03-01",
            "goal_date": "2040-12-31",
            "initial_amount": 0.0,
            "monthly_contribution": 0.0,
            "assumed_annual_rate_pct": 6.0
        },
        "historical_performance": [],
        "advice_history": []
    })
    
    # ----------------------------------------------------
    # Planted Scenario 12: CLIENT-012 to CLIENT-020
    # Normal, non-actionable financial conditions (on-track, balanced, reviewed recently)
    # ----------------------------------------------------
    normal_profiles = ["CONSERVATIVE", "MODERATE", "GROWTH", "AGGRESSIVE"]
    for i in range(12, 21):
        cid = f"CLIENT-{i:03d}"
        first = FIRST_NAMES[(i - 12) % len(FIRST_NAMES)]
        last = LAST_NAMES[(i - 12) % len(LAST_NAMES)]
        prof_name = normal_profiles[(i - 12) % len(normal_profiles)]
        prof_meta = RISK_PROFILES[prof_name]
        
        val = 600000.0 + (i * 25000.0)
        target = prof_meta["target_allocation"]
        holdings = generate_holdings_for_allocation(val, target, rng)
        
        # Recent review (30-60 days ago)
        review_dt = (datetime.strptime(as_of_date, "%Y-%m-%d") - timedelta(days=35 + (i % 30))).strftime("%Y-%m-%d")
        
        clients.append({
            "client_id": cid,
            "display_name": f"{first} {last}",
            "risk_profile": prof_name,
            "data_as_of": as_of_date,
            "last_review_date": review_dt,
            "planted_scenario_id": "SCENARIO-12" if i == 12 else None,
            "portfolio": {
                "valuation_date": as_of_date,
                "total_value": val,
                "cash_balance": round(val * (target.get("Cash", 10.0) / 100.0), 2),
                "target_allocation": target,
                "holdings": holdings,
                "is_stale": False,
                "data_warnings": []
            },
            "goal": {
                "goal_name": "Retirement Security Fund",
                "goal_amount": val * 1.6,
                "start_date": "2020-01-01",
                "goal_date": "2038-12-31",
                "initial_amount": val * 0.55,
                "monthly_contribution": 1500.0,
                "assumed_annual_rate_pct": prof_meta["expected_return"]
            },
            "historical_performance": [
                {
                    "period_label": "1Y",
                    "period_start": "2025-04-01",
                    "period_end": "2026-03-31",
                    "client_return_pct": round(prof_meta["expected_return"] + rng.uniform(0.2, 1.2), 2),
                    "benchmark_id": prof_meta["benchmark_id"],
                    "benchmark_name": prof_meta["benchmark_name"],
                    "benchmark_return_pct": round(prof_meta["expected_return"], 2),
                    "performance_gap_pp": round(rng.uniform(0.2, 1.2), 2),
                    "aligned": True
                }
            ],
            "advice_history": [
                {
                    "advice_id": f"ADV-{i:03d}",
                    "recording_date": review_dt,
                    "advice_text": "Portfolio aligned with mandate; continue monthly contributions.",
                    "expected_outcome": "Steady capital accumulation on target trajectory.",
                    "review_horizon_days": 180,
                    "target_allocation": target,
                    "status": "implemented"
                }
            ]
        })
        
    # ----------------------------------------------------
    # Generate remaining clients up to num_clients (200 total)
    # ----------------------------------------------------
    current_count = len(clients)
    for idx in range(current_count + 1, num_clients + 1):
        cid = f"CLIENT-{idx:03d}"
        first = FIRST_NAMES[idx % len(FIRST_NAMES)]
        last = LAST_NAMES[idx % len(LAST_NAMES)]
        prof_name = rng.choice(list(RISK_PROFILES.keys()))
        prof_meta = RISK_PROFILES[prof_name]
        
        goal_tmpl, goal_amt, goal_yr = rng.choice(GOAL_TEMPLATES)
        
        # Portfolio value between $150k and $3.5M
        tot_val = round(rng.uniform(200000.0, 2500000.0), -3)
        target = prof_meta["target_allocation"].copy()
        
        # Add slight natural drift for realistic variation (e.g. +/- 2-6%)
        drift_equity = rng.uniform(-4.0, 4.0)
        actual_alloc = {
            "Equity": round(target["Equity"] + drift_equity, 2),
            "Fixed Income": round(target["Fixed Income"] - (drift_equity * 0.8), 2),
            "Cash": round(target["Cash"] - (drift_equity * 0.2), 2)
        }
        holdings = generate_holdings_for_allocation(tot_val, actual_alloc, rng)
        
        # Review date between 20 and 280 days ago
        days_ago = rng.randint(20, 280)
        rev_dt = (datetime.strptime(as_of_date, "%Y-%m-%d") - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        
        # Benchmark and returns
        bmk_ret = round(prof_meta["expected_return"] + rng.uniform(-2.0, 2.0), 2)
        gap = round(rng.uniform(-2.5, 2.5), 2)
        client_ret = round(bmk_ret + gap, 2)
        
        start_year = rng.randint(2018, 2022)
        init_amt = round(tot_val * rng.uniform(0.4, 0.7), -3)
        monthly_pmt = round(rng.uniform(500.0, 3000.0), -2)
        
        clients.append({
            "client_id": cid,
            "display_name": f"{first} {last}",
            "risk_profile": prof_name,
            "data_as_of": as_of_date,
            "last_review_date": rev_dt,
            "planted_scenario_id": None,
            "portfolio": {
                "valuation_date": as_of_date,
                "total_value": tot_val,
                "cash_balance": round(tot_val * (actual_alloc.get("Cash", 10.0) / 100.0), 2),
                "target_allocation": target,
                "holdings": holdings,
                "is_stale": False,
                "data_warnings": []
            },
            "goal": {
                "goal_name": goal_tmpl,
                "goal_amount": float(goal_amt),
                "start_date": f"{start_year}-01-01",
                "goal_date": f"{goal_yr}-12-31",
                "initial_amount": float(init_amt),
                "monthly_contribution": float(monthly_pmt),
                "assumed_annual_rate_pct": prof_meta["expected_return"]
            },
            "historical_performance": [
                {
                    "period_label": "1Y",
                    "period_start": "2025-04-01",
                    "period_end": "2026-03-31",
                    "client_return_pct": client_ret,
                    "benchmark_id": prof_meta["benchmark_id"],
                    "benchmark_name": prof_meta["benchmark_name"],
                    "benchmark_return_pct": bmk_ret,
                    "performance_gap_pp": gap,
                    "aligned": True
                }
            ],
            "advice_history": [
                {
                    "advice_id": f"ADV-{idx:03d}",
                    "recording_date": rev_dt,
                    "advice_text": "Review asset allocation and rebalance when cash exceeds threshold.",
                    "expected_outcome": "Maintain targeted risk/return profile.",
                    "review_horizon_days": 180,
                    "target_allocation": target,
                    "status": "implemented"
                }
            ]
        })
        
    return {
        "metadata": {
            "dataset_name": "Advisor Dynamic Summary Synthetic Dataset",
            "seed": seed,
            "client_count": len(clients),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "as_of_date": as_of_date,
            "planted_scenarios_count": 12
        },
        "clients": clients
    }
