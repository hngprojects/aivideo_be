from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from api.v1.services.job import JobService
from main import app

client = TestClient(app)
endpoint = "/api/v1/jobs/statistics/sse"


def test_sse_job_activity(
    db_session_mock,
    access_token,
    mock_job_statistics,
):
    response = client.get(
        endpoint,
        headers={
            "Content-Type": "text/event-stream",
            "authorization": f"Bearer {access_token}",
        },
    )

    print(response.content)

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    assert (
        b'data: {"total_tasks": 10, "failed_tasks": 0, "in_progress_tasks": 0, "pending_tasks": 8, "completed_tasks": 1,"created_in_last_hour": 1, "active_in_last_hour": 0,"pending_in_last_hour": 0,"completed_in_last_hour": 1}'
        == response.content
    )
