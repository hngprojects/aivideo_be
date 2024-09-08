from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.v1.models.project import Project
from api.v1.services.project import project_service
from datetime import datetime, timezone
from uuid_extensions import uuid7

from main import app

def mock_project():
    return Project(
        id='user_id',
        user_id=str(uuid7()),
        title="Summarize Joe Rogan",
        project_type="Podcast Summarizer",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

def mock_db_session():
    db_session = MagicMock(spec=Session)
    return db_session

@pytest.fixture
def client():
    client = TestClient(app)
    return client

ENDPOINT = '/api/v1/projects'

class TestCodeUnderTest:
    @classmethod
    def setup_class(cls):
        app.dependency_overrides[get_db] = mock_db_session

    @classmethod
    def teardown_class(cls):
        app.dependency_overrides = {}

    def test_get_all_project(self, client):
        """Test to verify response for getting all projects."""

        mock_data = [
            Project(id='user_id_1', user_id=str(uuid7()), title="Summarize Joe Rogan",
                    project_type="Podcast Summarizer", created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)),
                    
            Project(id='user_id_2', user_id=str(uuid7()), title="Summarize YT Video",
                    project_type="Video Summarizer", created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc))
        ]

        with patch("api.v1.services.project.project_service.fetch_all_projects", return_value=mock_data):
            response = client.get(ENDPOINT)

            assert response.status_code == 200

    def test_get_all_projects_empty(self, client):
        """Test to verify response for getting an empty list of projects."""

        mock_data = []

        with patch("api.v1.services.project.project_service.fetch_all_projects", return_value=mock_data):
            response = client.get(ENDPOINT)

            assert response.status_code == 200

    def test_get_project_single(self, client):
        '''Test to successfully fetch a single project'''

        mock_data = mock_project()

        with patch("api.v1.services.project.project_service.fetch", return_value=mock_data):
            response = client.get(f'{ENDPOINT}/{mock_data.id}')

            assert response.status_code == 200
