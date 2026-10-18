"""Integration Tests for FastAPI Endpoints.

Tests both Member 1 Core Intelligence Endpoints:
- GET /health
- GET /api/clients
- GET /api/clients/{client_id}
- GET /api/clients/{client_id}/brief
- GET /api/insights
- POST /api/insights/{insight_id}/status
- POST /api/clients/{client_id}/notes
- GET /api/metrics/summary

And Member 2 Advisor Workflow Endpoints:
- GET /api/v1/health
- GET /api/v1/advisors/worklist
- GET /api/v1/clients
- GET /api/v1/clients/{client_id}
"""

import pytest

# ==========================================
# Member 1 Intelligence Engine Endpoints
# ==========================================

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"]["clients_loaded"] >= 200

def test_api_root(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "/docs" in data["documentation"]

def test_list_clients(client):
    response = client.get("/api/clients?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "clients" in data
    assert len(data["clients"]) == 10
    assert data["total_count"] >= 200
    
    first_score = data["clients"][0]["priority_score"]
    second_score = data["clients"][1]["priority_score"]
    assert first_score >= second_score

def test_search_and_filter_clients(client):
    response = client.get("/api/clients?search=Vance")
    assert response.status_code == 200
    data = response.json()
    assert len(data["clients"]) >= 1
    assert "Vance" in data["clients"][0]["display_name"]

def test_get_client_detail_success(client):
    response = client.get("/api/clients/CLIENT-001")
    assert response.status_code == 200
    data = response.json()
    assert data["client_id"] == "CLIENT-001"
    assert "portfolio" in data
    assert "goal" in data
    assert "historical_performance" in data
    assert "score_components" in data
    assert "priority_score" in data

def test_get_client_detail_not_found(client):
    response = client.get("/api/clients/CLIENT-UNKNOWN-999")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()

def test_get_client_brief(client):
    response = client.get("/api/clients/CLIENT-003/brief")
    assert response.status_code == 200
    data = response.json()
    assert data["client_id"] == "CLIENT-003"
    assert "DRAFT" in data["draft_notice"]
    assert len(data["suggested_review_questions"]) > 0

def test_list_insights_queue(client):
    response = client.get("/api/insights?sort=priority")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["score"] >= data[-1]["score"]
    assert "evidence" in data[0]

def test_update_insight_status(client):
    insights_res = client.get("/api/insights")
    ins_list = insights_res.json()
    assert len(ins_list) > 0
    test_ins = ins_list[0]
    ins_id = test_ins["insight_id"]
    
    update_res = client.post(
        f"/api/insights/{ins_id}/status",
        json={"status": "reviewed", "reason": "Reviewed during mock audit test"}
    )
    assert update_res.status_code == 200
    data = update_res.json()
    assert data["new_status"] == "reviewed"

def test_update_nonexistent_insight_status(client):
    update_res = client.post(
        "/api/insights/NONEXISTENT-INSIGHT/status",
        json={"status": "reviewed"}
    )
    assert update_res.status_code == 404

def test_add_client_note(client):
    note_payload = {
        "author": "Senior Advisor Jane Doe",
        "content": "Discussed asset allocation drift and planned rebalancing.",
        "category": "PORTFOLIO_REVIEW"
    }
    response = client.post("/api/clients/CLIENT-001/notes", json=note_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["client_id"] == "CLIENT-001"
    assert data["author"] == "Senior Advisor Jane Doe"
    assert data["note_id"].startswith("NOTE-")

    detail_res = client.get("/api/clients/CLIENT-001")
    detail_data = detail_res.json()
    notes = detail_data["notes"]
    assert any(n["note_id"] == data["note_id"] for n in notes)

def test_metrics_summary(client):
    response = client.get("/api/metrics/summary")
    assert response.status_code == 200
    data = response.json()
    assert "proposed_engine" in data
    assert "return_only_baseline" in data
    assert "comparisons" in data
    assert data["total_clients_evaluated"] >= 200
    assert data["proposed_engine"]["precision_at_10"] >= data["return_only_baseline"]["precision_at_10"]

# ==========================================
# Member 2 Advisor Workflow Endpoints
# ==========================================

def test_v1_health_check(client):
    response = client.get('/api/v1/health')
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'healthy'
    assert 'version' in data

def test_get_worklist_structure(client):
    response = client.get('/api/v1/advisors/worklist')
    assert response.status_code == 200
    data = response.json()
    assert 'totalCount' in data
    assert 'criticalCount' in data
    assert 'items' in data
    assert len(data['items']) == data['totalCount']
    assert data['totalCount'] >= 5

    # Check ranking order (descending urgencyScore)
    scores = [item['urgencyScore'] for item in data['items']]
    assert scores == sorted(scores, reverse=True)

    # Inspect first item contract fields
    first = data['items'][0]
    assert 'clientId' in first
    assert 'clientName' in first
    assert 'urgencyScore' in first
    assert 'urgencyLevel' in first
    assert 'scoreDrivers' in first
    assert 'evidence' in first

def test_filter_worklist_by_urgency(client):
    response = client.get('/api/v1/advisors/worklist?urgency=critical')
    assert response.status_code == 200
    data = response.json()
    for item in data['items']:
        assert item['urgencyLevel'] == 'critical'

def test_get_v1_client_by_id(client):
    response = client.get('/api/v1/clients/cli_001')
    assert response.status_code == 200
    data = response.json()
    assert data['id'] == 'cli_001'
    assert data['fullName'] == 'Eleanor Vance'

def test_get_v1_nonexistent_client(client):
    response = client.get('/api/v1/clients/cli_999999')
    assert response.status_code == 404
