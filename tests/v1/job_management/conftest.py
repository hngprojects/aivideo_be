from fastapi import HTTPException
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from main import app
from api.v1.models.user import User
from api.v1.services.user import user_service
from uuid_extensions import uuid7
from api.db.database import get_db
from io import StringIO

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
def mock_non_superadmin():
    with patch("api.v1.services.user.user_service.get_current_super_admin") as get_current_super_admin:
        get_current_super_admin.side_effect = HTTPException(403, "Not authorized")

        yield get_current_super_admin


@pytest.fixture
def access_token(test_admin_user):
    return user_service.create_access_token(test_admin_user.id)


@pytest.fixture
def mock_paginated_response():
    with patch(
        "api.v1.services.job_management.job_management_service.fetch_all_summarized_videos"
    ) as fetch_all_summarized_videos:
        response = {
            "pages": 1,
            "total": 1,
            "skip": 0,
            "limit": 10,
            "items": [
                {
                    "id": "string",
                    "title": "string",
                    "description": "string",
                    "file_url": "string",
                    "size": "string",
                    "status": "string",
                    "duration": "string",
                    "project_type": "string",
                    "user": {
                        "id": "string",
                        "email": "string",
                        "first_name": "string",
                        "last_name": "string",
                        "updated_at": "2024-08-13T09:48:59.916Z",
                    },
                    "created_at": "2024-08-13T09:48:59.916Z",
                    "updated_at": "2024-08-13T09:48:59.916Z",
                    "archived": False,
                    "archived_at": "2024-08-13T09:48:59.916Z",
                    "is_deleted": False,
                }
            ],
        }

        fetch_all_summarized_videos.return_value = response
        yield fetch_all_summarized_videos
