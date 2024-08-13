from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
endpoint = "/api/v1/contents/video"


# Mock the database dependency
def test_get_summarized_videos_success(
    db_session_mock,
    access_token,
    mock_paginated_response,
):
    response = client.get(endpoint, headers={"authorization": f"Bearer {access_token}"})

    assert response.status_code == 200
    assert response.json() == {
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
