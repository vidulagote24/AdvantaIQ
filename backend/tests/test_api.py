"""Integration Tests for FastAPI Endpoints.

Tests all required API endpoints:
- GET /health
- GET /api/clients
- GET /api/clients/{client_id}
- GET /api/clients/{client_id}/brief
- GET /api/insights
- POST /api/insights/{insight_id}/status
- POST /api/clients/{client_id}/notes
- GET /api/metrics/summary
- Error handling and 404 validations
"""

import pytest

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
    assert "/docs" in data["docs_url"]

def test_list_clients(client):
    response = client.get("/api/clients?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "clients" in data
    assert len(data["clients"]) == 10
    assert data["total_count"] >= 200
    
    # Check deterministic ordering: first item score >= second item score
    first_score = data["clients"][0]["priority_score"]
    second_score = data["clients"][1]["priority_score"]
    assert first_score >= second_score

def test_search_and_filter_clients(client):
    # Search for Vance
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
    # Top insight should have highest score
    assert data[0]["score"] >= data[-1]["score"]
    assert "evidence" in data[0]

def test_update_insight_status(client):
    # Find an active insight
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

    # Verify note appears in client detail
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
