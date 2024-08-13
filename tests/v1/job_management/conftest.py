import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from main import app
from api.v1.models.user import User
from api.v1.services.user import user_service
from uuid_extensions import uuid7
from api.db.database import get_db

client = TestClient(app)
endpoint = "/api/v1/contents/video"


@pytest.fixture
def db_session_mock():
    db_session = MagicMock()
    yield db_session


# Override the dependency with the mock
@pytest.fixture(autouse=True)
def override_get_db(db_session_mock):
    def get_db_override():
        yield db_session_mock

    app.dependency_overrides[get_db] = get_db_override
    yield
    app.dependency_overrides = {}


@pytest.fixture
def test_admin_user():
    return User(id=str(uuid7()))


@pytest.fixture
def access_token(test_admin_user):
    return user_service.create_access_token(test_admin_user.id)


@pytest.fixture
def mock_paginated_response():
    with patch(
        "api.v1.services.job_management.job_management_service.fetch_all_summarized_videos"
    ) as fetch_all_summarized_videos:
        response = {
            "status_code": 200,
            "success": True,
            "message": "Successfully fetched items",
            "data": {
                "pages": 1,
                "total": 1,
                "skip": 0,
                "limit": 30,
                "items": [
                    {
                        "duration": "15:30",
                        "title": "vid-one",
                        "status": "pending",
                        "created_at": "2024-08-12T19:37:52.759308+01:00",
                        "size": "12.2kb",
                        "user_id": "066ba546-9a61-7268-8000-fd722771734f",
                        "id": "0ed24c1f-b92a-40e7-8877-1275b5108443",
                        "updated_at": "2024-08-12T19:37:52.759308+01:00",
                        "user": {
                            "id": "066ba546-9a61-7268-8000-fd722771734f",
                            "first_name": "Test",
                        },
                    },
                ],
            },
        }

        fetch_all_summarized_videos.return_value = response
        yield fetch_all_summarized_videos
