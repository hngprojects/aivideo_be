"""
Test for resource search endpoint
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app
from uuid_extensions import uuid7
from fastapi import status
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.v1.models.resource import Resource
from api.v1.services.resource import resource_service, ResourceService


client = TestClient(app)


SEARCH_ENDPOINT = "/api/v1/resources/search"


@pytest.fixture
def mock_db_session():
    """Fixture to create a mock database session."""

    with patch("api.v1.services.resource.get_db", autospec=True) as mock_get_db:
        mock_db = MagicMock()
        app.dependency_overrides[get_db] = lambda: mock_db
        yield mock_db
    app.dependency_overrides = {}


@pytest.fixture
def mock_resource_service():
    """Fixture to create a mock resource service."""

    with patch("api.v1.services.resource.resource_service", autospec=True) as mock_service:
        yield mock_service


@pytest.fixture
def mock_get_current_user():
    """Fixture to create a mock current user."""
    with patch(
        "api.v1.services.user.UserService.get_current_user", autospec=True
    ) as mock_get_current_user:
        yield mock_get_current_user


mock_resources = [
    Resource(
        id=str(uuid7()),
        title="Test Resource 1",
        content="This is a test content for Resource 1.",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    ),
    Resource(
        id=str(uuid7()),
        title="Test Resource 2",
        content="This is another test content for Resource 2.",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
]


def test_search_resources(
    mock_get_current_user, mock_resource_service: ResourceService, mock_db_session: Session
):
    """Test for successful search of resources by keywords."""

    # Set up mock return values
    mock_get_current_user.return_value = MagicMock()  # Simulating an authenticated user
    mock_db_session.query().filter().order_by().limit().offset().all.return_value = mock_resources
    mock_db_session.query().filter().count.return_value = len(mock_resources)

    # Make the API request
    response = client.get(
        SEARCH_ENDPOINT,
        params={"keywords": "test", "page": 1, "per_page": 10},
        headers={"Authorization": "Bearer dummy_token"},
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert len(response_data["Data"]["resources"]) == len(mock_resources)
    assert response_data["Message"] == "Resources successfully retrieved"


def test_search_no_results(
    mock_get_current_user, mock_resource_service: ResourceService, mock_db_session: Session
):
    """Test search with no matching results."""

    # Set up mock return values
    mock_get_current_user.return_value = MagicMock()  # Simulating an authenticated user
    mock_db_session.query().filter().order_by().limit().offset().all.return_value = []
    mock_db_session.query().filter().count.return_value = 0

    # Make the API request
    response = client.get(
        SEARCH_ENDPOINT,
        params={"keywords": "nonexistent", "page": 1, "per_page": 10},
        headers={"Authorization": "Bearer dummy_token"},
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert len(response_data["Data"]["resources"]) == 0
    assert response_data["Message"] == "Resources successfully retrieved"
