#!/usr/bin/env python3

"""Test youtube summarization batch """


from collections import namedtuple
from unittest.mock import AsyncMock, patch, Mock
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from api.v1.routes.ai_tools.youtube_video_summarizer import video_summary
from main import app
from api.db.database import get_db
from api.v1.models.user import User

# Create a test client
client = TestClient(app)

# Mock the database session for dependency injection
@pytest.fixture
def mock_db():
    db_session = Mock()
    db_session.query.return_value.filter_by.return_value.first.return_value = None  # Adjust this to your use case
    yield db_session


@pytest.fixture
def mock_current_user():
    with patch("api.v1.services.user.user_service.get_current_user") as mock:
        mock.return_value = User(
            id=f'{uuid4()}',
            first_name='Joe',
            last_name='Joe'
        )
        yield mock


@pytest.fixture
def mock_create():
    with patch("api.v1.services.job.tifi_job_service.create") as mock:
        TifiJob = namedtuple('TifiJob', ['id'])
        mock.return_value = TifiJob(id="test_job_id")
        yield mock


@pytest.fixture
def override_get_db(mock_db):
    app.dependency_overrides[get_db] = lambda: mock_db
    yield
    app.dependency_overrides = {}


# Test the endpoint


def test_enqueue_summarize_batch_job(
    # mock_current_user,
    mock_create,
    override_get_db,
):
    # Prepare test files
    data = {
        "links": ["https://www.youtube.com/watch?v=testvideo"],
        "detail_level": "short"
    }

    # Send a POST request to the summarize_batch endpoint
    response = client.post(
        "/api/v1/tools/summary/batch-youtube-summarize", 
        # headers={
        #     'Authorization': 'Bearer test_token'
        # },
        json=data
    )

    # Assertions
    assert response.status_code == 202
