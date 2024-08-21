"""
Test for GET tool statistics endpoint
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
from api.v1.models.project import Project


client = TestClient(app)


ENDPOINT = "/api/v1/projects/statistics"


@pytest.fixture
def mock_db_session():
    """Fixture to create a mock database session."

    Yields:
        MagicMock: mock database
    """

    with patch("api.v1.services.user.get_db", autospec=True) as mock_get_db:
        mock_db = MagicMock()
        app.dependency_overrides[get_db] = lambda: mock_db
        yield mock_db
    app.dependency_overrides = {}


mock_projects = [
    Project(
        id="user_id",
        user_id=str(uuid7()),
        title="Summarize Joe Rogan",
        project_type="Podcast Summarizer",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
]


def test_tool_stats_retrieval(
    mock_db_session: Session,
):
    mock_db_session.query.return_value.all.return_value = mock_projects
    response = client.get(ENDPOINT)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["data"]["podcast_summarizer"] == 100.0


def test_no_tool_stats_retrieval(mock_db_session: Session):
    mock_db_session.query.return_value.all.return_value = []
    response = client.get(ENDPOINT)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["data"]["podcast_summarizer"] == 0
