from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid_extensions import uuid7

from api.db.database import get_db
from api.v1.models.project import Project
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

@pytest.fixture
def db_session_mock():
    db_session = MagicMock(spec=Session)
    yield db_session

@pytest.fixture
def client():
    client = TestClient(app)
    yield client

test_project_req_body = {
    "title": "Summarize Joe Rogan",
    "project_type": "Podcast Summarizer",
}

ENDPOINT = '/api/v1/projects'

class TestCodeUnderTest:

    @classmethod
    def teardown_class(cls):
        app.dependency_overrides = {}

    def test_create_projects_success(self, client):
        '''Test to successfully create a new project'''

        mock_data = mock_project()

        with patch("api.v1.services.project.project_service.create", return_value=mock_project()) as mock_create:
            response = client.post(
                ENDPOINT,
                json=test_project_req_body
            )
            assert response.status_code == 201
            assert response.json()['data']['title'] == mock_data.title
            assert response.json()['data']['project_type'] == mock_data.project_type

    def test_create_project_missing_field(self, client, db_session_mock):
        '''Test for missing field when creating a new project'''

        mock_data = mock_project()

        with patch("api.v1.services.project.project_service.create", return_value=mock_data) as mock_create:
            response = client.post(
                ENDPOINT,
                json={
                    "title": "The best"
                }
            )
            assert response.status_code == 422

    def test_get_all_projects(self, client):
        """Test to verify response for getting all projects."""

        mock_data = [
            mock_project(),
            Project(id='project_id_2', user_id=str(uuid7()), title="Summarize YT Video",
                    project_type="Video Summarizer", created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                    )
        ]

        with patch("api.v1.services.project.project_service.fetch_all_projects", return_value=mock_data):
            response = client.get(ENDPOINT)

            assert response.status_code == 200
            assert response.json()['data'][0]['title'] == mock_data[0].title
            assert response.json()['data'][1]['project_type'] == mock_data[1].project_type

    def test_get_all_projects_empty(self, client):
        """Test to verify response for getting an empty list of projects."""

        mock_data = []

        with patch("api.v1.services.project.project_service.fetch_all_projects", return_value=mock_data):
            response = client.get(ENDPOINT)

            assert response.status_code == 200
            assert response.json().get('data') is None

    def test_get_single_project(self, client):
        '''Test to successfully fetch a single project'''

        mock_data = mock_project()

        with patch("api.v1.services.project.project_service.fetch_project_by_id", return_value=mock_data):
            response = client.get(f'{ENDPOINT}/{mock_data.id}')
            assert response.status_code == 200
            assert response.json()['data']['title'] == mock_data.title
            assert response.json()['data']['project_type'] == mock_data.project_type

    def test_get_project_not_found(self, client):
        """Test when the project ID does not exist."""

        nonexistent_id = str(uuid7())
        with patch("api.v1.services.project.project_service.fetch_project_by_id", return_value=None):
            response = client.get(f'{ENDPOINT}/{nonexistent_id}')

            assert response.status_code == 404
            assert response.json()['message'] == 'Project not found'
