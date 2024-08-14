from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
endpoint = "/api/v1/jobs/activity"


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
            "total": 2,
            "skip": 0,
            "limit": 30,
            "items": [
                {
                    "user_id": "066bcc17-063d-74ca-8000-61f211cfb3bb",
                    "project_id": "8031a9e4-7414-40ab-b993-8a76ae9bcc38",
                    "result": None,
                    "created_at": "2024-08-14T15:45:23.907752+01:00",
                    "job_id": "123AB",
                    "status": "COMPLETED",
                    "id": "0836dcc1-9499-446a-85aa-1e24a9d8053f",
                    "updated_at": "2024-08-14T15:45:23.907752+01:00",
                    "user": {
                        "id": "066bcc17-063d-74ca-8000-61f211cfb3bb",
                        "first_name": "Test",
                        "last_name": "User",
                    },
                    "project": {
                        "is_active": False,
                        "id": "8031a9e4-7414-40ab-b993-8a76ae9bcc38",
                        "updated_at": "2024-08-14T15:42:15.896913+01:00",
                        "user_id": "066bcc17-063d-74ca-8000-61f211cfb3bb",
                        "project_type": "video",
                        "archived_at": None,
                        "created_at": "2024-08-14T15:42:15.896913+01:00",
                    },
                },
                {
                    "user_id": "066bcc17-063d-74ca-8000-61f211cfb3bb",
                    "project_id": "8031a9e4-7414-40ab-b993-8a76ae9bcc38",
                    "result": None,
                    "created_at": "2024-08-14T15:45:58.542153+01:00",
                    "job_id": "123AB",
                    "status": "FAILED",
                    "id": "3f89c1ff-a87b-4708-a9c7-af1ce995a111",
                    "updated_at": "2024-08-14T15:45:58.542153+01:00",
                    "user": {
                        "id": "066bcc17-063d-74ca-8000-61f211cfb3bb",
                        "first_name": "Test",
                        "last_name": "User",
                    },
                    "project": {
                        "is_active": False,
                        "id": "8031a9e4-7414-40ab-b993-8a76ae9bcc38",
                        "updated_at": "2024-08-14T15:42:15.896913+01:00",
                        "user_id": "066bcc17-063d-74ca-8000-61f211cfb3bb",
                        "project_type": "video",
                        "archived_at": None,
                        "created_at": "2024-08-14T15:42:15.896913+01:00",
                    },
                },
            ],
        },
    }
