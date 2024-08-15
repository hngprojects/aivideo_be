from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.v1.models.project import Project
from api.v1.services.project import project_service
from api.v1.services.user import user_service
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


ENDPOINT = '/api/v1/dashboard/projects'

class TestCodeUnderTest:
    @classmethod 
    def setup_class(cls):
        app.dependency_overrides[user_service.get_current_user] = lambda: MagicMock(id='user_id')
        app.dependency_overrides[get_db] = mock_db_session
        app.dependency_overrides[project_service.fetch_all_user_projects] = lambda: mock_data


    @classmethod
    def teardown_class(cls):
        app.dependency_overrides = {}

    def test_get_all_project(self, client):
        """Test to verify response for getting all projects."""
    
        mock_data = [
            Project(id='user_id', user_id=str(uuid7()), title="Summarize Joe Rogan",
                    project_type="Podcast Summarizer", created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                    ),
            Project(id='user_id', user_id=str(uuid7()), title="Summarize YT Video",
                    project_type="Video Summarizer", created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                    )
        ]

        app.dependency_overrides[project_service.fetch_all_user_projects] = lambda: mock_data

        with patch("api.v1.services.project.ProjectService.fetch_all_user_projects", return_value=mock_data):
            response = client.get(ENDPOINT)
            assert response.status_code == 200
            assert response.json()['data'][0]['title'] == mock_data[0].title
            assert response.json()['data'][1]['project_type'] == mock_data[1].project_type


    def test_get_all_projects_empty(self, client):
        """Test to verify response for getting empty list of projects."""

        mock_data = []

        app.dependency_overrides[project_service.fetch_all_user_projects] = mock_data

        with patch("api.v1.services.project.project_service.fetch_all_user_projects", return_value=mock_data):
            response = client.get(ENDPOINT)

            assert response.status_code == 200
            assert response.json().get('data') == None



    def test_get_project_single(self, client):
        '''Test to successfully fetch a single project'''

        mock_data = mock_project()

        with patch("api.v1.services.project.project_service.fetch_user_project", return_value=mock_data):
            response = client.get(
                f'{ENDPOINT}/{mock_data.id}',
            )

            assert response.status_code == 200
            assert response.json()['data']['title'] == mock_data.title
            assert response.json()['data']['project_type'] == mock_data.project_type

    
    def test_get_project_not_found(self, client):
        """Test when the project ID does not exist."""

        nonexistent_id = str(uuid7())
        with patch("api.v1.services.project.project_service.fetch_user_project", return_value=None):
            response = client.get(
                f'{ENDPOINT}/{nonexistent_id}',
            )

        assert response.status_code == 404
        response_json = response.json()
        assert 'message' in response_json
        assert response_json['message'] == 'Project not found'
