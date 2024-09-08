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
