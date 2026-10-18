"""Pytest Configuration and Fixtures.

Configures test database, FastAPI TestClient, and shared fixtures.
Includes compatibility patch for httpx 0.28+ with Starlette TestClient.
"""

import sys
from pathlib import Path
import pytest
import httpx

# Compatibility patch for httpx 0.28+ where Client.__init__ removed 'app' argument
_orig_httpx_client_init = httpx.Client.__init__
def _patched_httpx_client_init(self, *args, **kwargs):
    kwargs.pop("app", None)
    return _orig_httpx_client_init(self, *args, **kwargs)
httpx.Client.__init__ = _patched_httpx_client_init

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from app.main import app
from app.data.repositories import ClientRepository

@pytest.fixture(scope="session")
def test_db_path(tmp_path_factory):
    temp_dir = tmp_path_factory.mktemp("test_db")
    return temp_dir / "test_advisor.db"

@pytest.fixture(scope="session")
def test_repo(test_db_path):
    repo = ClientRepository(db_path=test_db_path)
    return repo

@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client
