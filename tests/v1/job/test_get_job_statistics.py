from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
endpoint = "/api/v1/jobs/statistics"


# Mock the database dependency
def test_get_job_statistics(db_session_mock, access_token, mock_get_job_statistics):
    response = client.get(endpoint, headers={"authorization": f"Bearer {access_token}"})

    assert response.status_code == 200

    data = response.json()

    assert data["status_code"] == 200
    assert data["success"] == True
    assert data["message"] == "Job statistics retrieved successfully"
