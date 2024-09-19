#!/usr/bin/env/python3

"""Test for youtube_summarizer tool"""


from collections import namedtuple
import pytest
from unittest.mock import AsyncMock, patch, Mock
from fastapi.testclient import TestClient
from api.v1.routes.ai_tools.youtube_summarizer import video_summary
from api.db.database import get_db
from main import app

# Create a test client
client = TestClient(app)

# Mock the database session for dependency injection


# @pytest.fixture
# def mock_db():
#     yield AsyncMock()


@pytest.fixture
def mock_db():
    db_session = Mock()
    db_session.query.return_value.filter_by.return_value.first.return_value = None  # Adjust this to your use case
    yield db_session

# Mock the upload_files function and the Celery task


@pytest.fixture
def mock_upload_files():
    with patch("api.utils.files.upload_files") as mock:
        mock.return_value = ["test_video.mp4"]
        yield mock


# @pytest.fixture
# def mock_generate_video_summary_task():
#     # with patch("api.core.dependencies.celery.tasks.video_summary_tasks.generate_video_summary_task.delay") as mock:
#     with patch("api.v1.services.job.tifi_job_service.create") as mock:
#         # mock.return_value.id = "mock_job_id"
#         TifiJob = namedtuple('TifiJob', ['id'])
#         Project = namedtuple('Project', ['id'])

#         mock.return_value = (TifiJob(id="test_job_id"), Project(id="test_project_id"))
#         yield mock


# @pytest.fixture
# def mock_create_project_with_job():
#     with patch("api.v1.services.job.job_service.create_project_with_job") as mock:
#         mock.return_value = AsyncMock(
#             id="mock_project_id"
#         )
#         yield mock


@pytest.fixture
def mock_create():
    # with patch("api.core.dependencies.celery.tasks.video_summary_tasks.generate_video_summary_task.delay") as mock:
    with patch("api.v1.services.job.tifi_job_service.create") as mock:
        # mock.return_value.id = "mock_job_id"
        TifiJob = namedtuple('TifiJob', ['id'])
        Project = namedtuple('Project', ['id'])

        mock.return_value = (TifiJob(id="test_job_id"), Project(id="test_project_id"))
        yield mock


@pytest.fixture
def override_get_db(mock_db):
    app.dependency_overrides[get_db] = lambda: mock_db
    yield
    app.dependency_overrides = {}

# Test the endpoint


# def test_enqueue_summarize_batch_job(mock_upload_files, mock_generate_video_summary_task, mock_create_project_with_job, override_get_db):
def test_enqueue_summarize_batch_job(mock_upload_files, mock_create, override_get_db):
    # Prepare test files
    files = {
        "files": ("video.mp4", b"dummy video data", "video/mp4")
    }

    # Send a POST request to the summarize_batch endpoint
    response = client.post(
        "/api/v1/tools/summary/batch-video-summarize", files=files)

    # Assertions
    assert response.status_code == 202
    assert response.json()[
        "message"] == "Video summary generation task initiated successfully"
    assert "job_ids" in response.json()["data"]
