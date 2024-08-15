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

# Mock the upload_file function and the Celery task


@pytest.fixture
def mock_upload_file():
    with patch("api.utils.files.upload_file") as mock:
        mock.return_value = ["test_video.mp4"]
        yield mock


@pytest.fixture
def mock_generate_video_summary_task():
    with patch("api.core.dependencies.celery.tasks.video_summary_tasks.generate_video_summary_task.delay") as mock:
        mock.return_value.id = "mock_job_id"
        yield mock


@pytest.fixture
def override_get_db(mock_db):
    app.dependency_overrides[get_db] = lambda: mock_db
    yield
    app.dependency_overrides = {}

# Test the endpoint


def test_enqueue_summarize_batch_job(mock_upload_file, mock_generate_video_summary_task, override_get_db):
    # Prepare test files
    files = {
        "files": ("video.mp4", b"dummy video data", "video/mp4")
    }

    # Send a POST request to the summarize_batch endpoint
    response = client.post(
        "api/v1/tools/youtube_summarizer/summarize_batch", files=files)

    assert response.status_code == 202
