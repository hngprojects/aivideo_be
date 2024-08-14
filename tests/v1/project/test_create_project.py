from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid_extensions import uuid7

from api.db.database import get_db
from api.v1.services.user import oauth2_scheme, user_service
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

        # Mock the user service to return the current user
        app.dependency_overrides[user_service.get_current_user] = lambda: MagicMock(id='user_id')

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

        # Mock the user service to return the current admin
        app.dependency_overrides[user_service.get_current_super_admin] = lambda: MagicMock()

        mock_data = mock_project()

        with patch("api.v1.services.project.project_service.create", return_value=mock_data) as mock_create:
            response = client.post(
                ENDPOINT,
                json={
                    "title": "The best"
                }
            )

            assert response.status_code == 422


    def test_create_project_unauthorized(self, client, db_session_mock):
        """Test unauthenticated user

        Args:
            client: TestClient object
            db_session_mock (MagicMock): 
        """
        app.dependency_overrides = {}
        
        response = client.post(
            ENDPOINT, json=test_project_req_body
            )

        assert response.status_code == 401
        assert response.json()['message'] == 'Not authenticated'