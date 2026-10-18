import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get('/api/v1/health')
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'healthy'
    assert 'version' in data

def test_get_worklist_structure():
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

def test_filter_worklist_by_urgency():
    response = client.get('/api/v1/advisors/worklist?urgency=critical')
    assert response.status_code == 200
    data = response.json()
    for item in data['items']:
        assert item['urgencyLevel'] == 'critical'

def test_get_client_by_id():
    response = client.get('/api/v1/clients/cli_001')
    assert response.status_code == 200
    data = response.json()
    assert data['id'] == 'cli_001'
    assert data['fullName'] == 'Eleanor Vance'

def test_get_nonexistent_client():
    response = client.get('/api/v1/clients/cli_999999')
    assert response.status_code == 404
