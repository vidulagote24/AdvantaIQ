import sys
import json
from pathlib import Path

# Add backend directory to path if run from repo root
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

REPO_ROOT = BASE_DIR.parent
MOCK_PATH = REPO_ROOT / 'frontend' / 'src' / 'mocks' / 'worklist.json'

from app.services.data_loader import get_worklist_response

def verify():
    live = get_worklist_response().model_dump()
    with open(MOCK_PATH, 'r', encoding='utf-8') as f:
        mock = json.load(f)

    print(f"Live items count: {len(live['items'])}, Mock items count: {len(mock['items'])}")
    assert live['totalCount'] == mock['totalCount'], f"Total count mismatch: {live['totalCount']} vs {mock['totalCount']}"
    assert live['criticalCount'] == mock['criticalCount'], f"Critical count mismatch: {live['criticalCount']} vs {mock['criticalCount']}"
    assert live['highCount'] == mock['highCount'], f"High count mismatch: {live['highCount']} vs {mock['highCount']}"
    assert live['mediumCount'] == mock['mediumCount'], f"Medium count mismatch: {live['mediumCount']} vs {mock['mediumCount']}"
    assert live['lowCount'] == mock['lowCount'], f"Low count mismatch: {live['lowCount']} vs {mock['lowCount']}"

    for idx, (l, m) in enumerate(zip(live['items'], mock['items'])):
        print(f"Row {idx+1}: {l['clientId']} ({l['clientName']}) -> Live score: {l['urgencyScore']}, Mock score: {m['urgencyScore']}")
        assert l['clientId'] == m['clientId'], f"Client ID mismatch at row {idx}: {l['clientId']} vs {m['clientId']}"
        assert l['urgencyScore'] == m['urgencyScore'], f"Score mismatch: {l['urgencyScore']} vs {m['urgencyScore']}"
        assert l['urgencyLevel'] == m['urgencyLevel'], f"Level mismatch: {l['urgencyLevel']} vs {m['urgencyLevel']}"
        
        # Verify score drivers sum to urgencyScore
        driver_sum = sum(d['pointsAwarded'] for d in l['scoreDrivers'])
        assert driver_sum == l['urgencyScore'], f"Driver sum {driver_sum} != urgencyScore {l['urgencyScore']} for {l['clientId']}"

    print("\n[OK] SUCCESS: Mock JSON and Live Backend API Worklists are 100% Consistent and Verified!")

if __name__ == '__main__':
    verify()
