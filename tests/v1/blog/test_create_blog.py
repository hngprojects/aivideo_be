# Dependencies:
# pip install pytest-mock
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app
from api.v1.services.user import user_service
from api.db.database import get_db
from sqlalchemy.orm import Session
from datetime import datetime
from api.v1.schemas.blog import BlogCreate
from api.v1.services.user import oauth2_scheme


def mock_deps():
    return MagicMock(id="user_id")

def mock_db():
    return MagicMock(spec=Session)

def mock_oauth():
    return 'access_token'

@pytest.fixture
def client():
    client = TestClient(app)
    yield client

class TestCodeUnderTest:
    @classmethod 
    def setup_class(cls):
        app.dependency_overrides[user_service.get_current_super_admin] = mock_deps
        app.dependency_overrides[get_db] = mock_db

        
    @classmethod
    def teardown_class(cls):
        app.dependency_overrides = {}


    # Successfully adding a job to the database
    def test_add_jobs_success(self, client):
        test_blog = {
                    "title": "string",
                    "subtitle": "string",
                    "content": "string",
                    "thumbnail_url": "string",
                    "tags": [
                        "string"
                    ],
                    "excerpt": "string"
                    }
                
        with patch('api.v1.services.blog.BlogService.create') as mock_job:
            mock_job.return_value = MagicMock(spec=BlogCreate,
            id='user_id',
            created_at=datetime.now())

            with patch('api.v1.schemas.blog.BlogCreate.model_validate') as sc:
                sc.return_value = test_blog
                response = client.post("/api/v1/blogs", json=test_blog)

                assert response.status_code == 201
                assert response.json()['message'] == "Blog created successfully!"
                assert response.json()['success'] == True

    def test_add_jobs_unauthorized(self, client):
            test_blog = {
                        "title": "string",
                        "subtitle": "string",
                        "content": "string",
                        "thumbnail_url": "string",
                        "tags": [
                            "string"
                        ],
                        "excerpt": "string"
                        }
                    
            
            app.dependency_overrides = {}

            response = client.post("/api/v1/blogs", json=test_blog)
            assert response.status_code == 401
            assert response.json()['message'] == 'Not authenticated'
