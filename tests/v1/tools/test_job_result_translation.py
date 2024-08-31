#!/usr/bin/env python3

"""Test youtube transcription jobs"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from api.v1.routes.ai_tools.yt_summary import yt_summary
from api.db.database import get_db
from main import app

# Create a test client
client = TestClient(app)


@pytest.fixture
def mock_db():
    yield MagicMock()


@pytest.fixture
def mock_async_result():
    with patch("api.v1.routes.ai_tools.yt_summary.AsyncResult") as mock:
        yield mock


@pytest.fixture
def mock_translate_text():
    with patch("api.v1.routes.ai_tools.yt_summary.translate_text") as mock:
        yield mock


@pytest.fixture
def override_get_db(mock_db):
    app.dependency_overrides[get_db] = lambda: mock_db
    yield
    app.dependency_overrides = {}


def test_translate_job_result_success(mock_async_result, mock_translate_text, override_get_db):
    # Mock successful job result
    mock_async_result.return_value.result = '{"summary": "Test summary", "transcript": "Test transcript"}'
    mock_async_result.return_value.state = "SUCCESS"

    # Mock successful translation
    mock_translate_text.return_value = {
        "summary": "Translated summary",
        "transcript": "Translated transcript"
    }

    # Prepare test data
    test_data = {
        "job_id": "test_job_id",
        "language": "fr"
    }

    # Send a POST request to the translate_job_result endpoint
    response = client.post(
        "/api/v1/tools/summary/translate_job_result", json=test_data)

    # Assertions
    assert response.status_code == 200
    assert response.json()["message"] == "Translation successful"
    assert "result" in response.json()["data"]
    assert response.json()["data"]["result"] == {
        "summary": "Translated summary",
        "transcript": "Translated transcript"
    }


def test_translate_job_result_failure_job_not_ready(mock_async_result, override_get_db):
    # Mock job result not ready
    mock_async_result.return_value.result = None
    mock_async_result.return_value.state = "PENDING"

    # Prepare test data
    test_data = {
        "job_id": "test_job_id",
        "language": "fr"
    }

    # Send a POST request to the translate_job_result endpoint
    response = client.post(
        "/api/v1/tools/summary/translate_job_result", json=test_data)

    # Assertions
    assert response.status_code == 400
