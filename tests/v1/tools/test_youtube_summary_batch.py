#!/usr/bin/env python3

"""Test youtube summarization batch """


from collections import namedtuple
from unittest.mock import AsyncMock, patch, Mock
import pytest
from fastapi.testclient import TestClient
from api.v1.routes.ai_tools.youtube_summarizer import video_summary
from main import app
from api.db.database import get_db

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


# @pytest.fixture
# def moch_download_and_generate_video_summmary_task():
#     with patch(
#         "api.core.dependencies.celery.tasks.video_summary_tasks.download_and_generate_video_summmary_task.delay"
#     ) as mock:
#         mock.return_value.id = "mock_job_id"
#         yield mock


@pytest.fixture
# def mock_create_project_with_job():
def mock_create():
    # with patch("api.v1.services.job.job_service.create_project_with_job") as mock:
    with patch("api.v1.services.job.tifi_job_service.create") as mock:
        # mock.return_value = AsyncMock(id="mock_project_id")
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


def test_enqueue_summarize_batch_job(
    # moch_download_and_generate_video_summmary_task,
    # mock_create_project_with_job,
    mock_create,
    override_get_db,
):
    # Prepare test files
    link = {
        "links": ["https://www.youtube.com/watch?v=testvideo"]
    }

    # Send a POST request to the summarize_batch endpoint
    response = client.post("/api/v1/tools/summary/batch-youtube-summarize", json=link)

    # Assertions
    assert response.status_code == 202
