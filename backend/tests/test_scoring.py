import pytest
from backend.app.models.schemas import ClientProfile
from backend.app.services.scoring import calculate_urgency_score
from backend.app.services.data_loader import load_clients, build_advisor_insights

def test_load_synthetic_clients():
    clients = load_clients()
    assert len(clients) == 6
    for c in clients:
        assert isinstance(c, ClientProfile)
        assert c.id.startswith('cli_')
        assert c.totalAum > 0

def test_category_maxima_sum_to_100():
    """Verify that score driver category maxima strictly sum to 100."""
    clients = load_clients()
    for c in clients:
        score, level, drivers, evidence, cat, summary, action = calculate_urgency_score(c)
        assert len(drivers) == 5
        max_sum = sum(d.maxPoints for d in drivers)
        assert max_sum == 100, f"Driver maxima sum must be 100, got {max_sum}"

def test_deterministic_scoring_all_clients():
    """Verify deterministic scores and urgency levels for all synthetic clients."""
    clients = {c.id: c for c in load_clients()}
    
    # Eleanor Vance (cli_001): Severe drift (30) + Underfunded goal (22) + Overdue review (20) + Cash drag (8) = 80
    eleanor = clients['cli_001']
    score, level, drivers, evidence, cat, summary, action = calculate_urgency_score(eleanor)
    assert score == 80
    assert level == 'critical'
    assert cat == 'Allocation Drift'
    assert len(evidence) >= 2
    
    # Sofia Rodriguez (cli_003): Drift (30) + Due review (10) + Cash drag (10) + Stale data (10) = 60
    sofia = clients['cli_003']
    score, level, drivers, evidence, cat, summary, action = calculate_urgency_score(sofia)
    assert score == 60
    assert level == 'high'
    assert cat == 'Allocation Drift'

    # Marcus Chen (cli_002): Drift (15) + Goal deadline (30) = 45
    marcus = clients['cli_002']
    score, level, drivers, evidence, cat, summary, action = calculate_urgency_score(marcus)
    assert score == 45
    assert level == 'medium'
    assert cat == 'Goal Milestones'

    # Robert Kowalski (cli_006): Drift (15) + Overdue review (10) = 25
    robert = clients['cli_006']
    score, level, drivers, evidence, cat, summary, action = calculate_urgency_score(robert)
    assert score == 25
    assert level == 'low'
    assert cat == 'Allocation Drift'

    # David & Sarah Miller (cli_004): Drift (15) = 15
    miller = clients['cli_004']
    score, level, drivers, evidence, cat, summary, action = calculate_urgency_score(miller)
    assert score == 15
    assert level == 'low'

    # Amina Patel (cli_005): Fully aligned = 0
    amina = clients['cli_005']
    score, level, drivers, evidence, cat, summary, action = calculate_urgency_score(amina)
    assert score == 0
    assert level == 'low'

def test_score_boundaries_and_driver_consistency():
    clients = load_clients()
    for c in clients:
        score, level, drivers, evidence, cat, summary, action = calculate_urgency_score(c)
        assert 0 <= score <= 100
        assert level in ['critical', 'high', 'medium', 'low']
        total_driver_pts = sum(d.pointsAwarded for d in drivers)
        assert score == total_driver_pts, f"Total score {score} must equal driver sum {total_driver_pts}"

def test_worklist_descending_sort_order():
    insights = build_advisor_insights()
    scores = [i.urgencyScore for i in insights]
    assert scores == sorted(scores, reverse=True)
    assert scores == [80, 60, 45, 25, 15, 0]
