from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
endpoint = "/api/v1/contents"


# Mock the database dependency
def test_get_summarized_videos_success(
    db_session_mock,
    access_token,
    mock_paginated_response,
):
    response = client.get(endpoint, headers={"authorization": f"Bearer {access_token}"})

    assert response.status_code == 200
    assert response.json() == {
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
                    "updated_at": "2024-08-13T09:48:59.916000Z",
                },
                "created_at": "2024-08-13T09:48:59.916000Z",
                "updated_at": "2024-08-13T09:48:59.916000Z",
                "archived": False,
                "archived_at": "2024-08-13T09:48:59.916000Z",
                "is_deleted": False,
            }
        ],
    }
