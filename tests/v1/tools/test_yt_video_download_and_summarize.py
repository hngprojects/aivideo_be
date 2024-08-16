#!/usr/bin/env/python3

"""Test for youtube_summarizer tool"""


import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from api.v1.routes.ai_tools.youtube_summarizer import video_summary
from api.db.database import get_db
from main import app

# Create a test client
client = TestClient(app)

# Mock the database session for dependency injection


@pytest.fixture
def mock_db():
    yield AsyncMock()


# Mock the upload_files function and the Celery task


@pytest.fixture
def moch_download_and_generate_video_summmary_task():
    with patch(
        "api.core.dependencies.celery.tasks.video_summary_tasks.download_and_generate_video_summmary_task.delay"
    ) as mock:
        mock.return_value.id = "mock_job_id"
        yield mock


@pytest.fixture
def mock_create_project_with_job():
    with patch("api.v1.services.job.job_service.create_project_with_job") as mock:
        mock.return_value = AsyncMock(id="mock_project_id")
        yield mock


@pytest.fixture
def override_get_db(mock_db):
    app.dependency_overrides[get_db] = lambda: mock_db
    yield
    app.dependency_overrides = {}


# Test the endpoint


def test_enqueue_summarize_batch_job(
    moch_download_and_generate_video_summmary_task,
    mock_create_project_with_job,
    override_get_db,
):
    # Prepare test files
    link = {"link": "http://localhost:localhost"}

    # Send a POST request to the summarize_batch endpoint
    response = client.post("/api/v1/tools/summary/youtube", data=link)

    # Assertions
    assert response.status_code == 202
    assert response.json()["message"] == "Summary generation job initiated successfully"
    assert "job_ids" in response.json()["data"]
