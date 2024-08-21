from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from api.v1.services.job import JobService
from main import app

client = TestClient(app)
endpoint = "/api/v1/jobs/sse"


def test_sse_job_activity(db_session_mock, access_token, mock_job_activity):
    response = client.get(
        endpoint,
        headers={
            "Content-Type": "text/event-stream",
            "authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    assert b'data: {"job_id": "123-xxx", "status": "PENDING"}' == response.content
