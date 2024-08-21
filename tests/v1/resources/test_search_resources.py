import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from api.v1.routes.resource import resource
from main import app

@pytest.fixture
def mock_db_session():
    """Fixture to create a mock database session."""
    # Adjust the patch target to the correct module where `get_db` is located
    with patch("api.database.get_db", autospec=True) as mock_get_db:
        yield mock_get_db

@pytest.fixture
def client(mock_db_session):
    """Fixture to create a test client with a mocked database session."""
    app.dependency_overrides[resource.dependencies[0]] = mock_db_session
    yield TestClient(app)
    app.dependency_overrides = {}

def test_search_resources(client):
    response = client.get("/api/v1/resources/search?query=test")
    assert response.status_code == 200
    assert response.json() == {"success": True, "data": []}

def test_search_no_results(client):
    response = client.get("/api/v1/resources/search?query=nonexistent")
    assert response.status_code == 200
    assert response.json() == {"success": True, "data": []}
