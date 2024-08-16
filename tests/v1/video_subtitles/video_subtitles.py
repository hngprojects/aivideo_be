import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from main import app
from api.v1.schemas.video_subtitles import TranscriptionRequest, TranslationRequest, SubtitleRequest

client = TestClient(app)

@pytest.fixture
def mock_transcribe_video_task():
    with patch("api.core.dependencies.celery.tasks.video_subtitles_tasks.transcribe_video_task.delay") as mock:
        mock.return_value.id = "mock_transcribe_job_id"
        yield mock

@pytest.fixture
def mock_translate_text_task():
    with patch("api.core.dependencies.celery.tasks.video_subtitles_tasks.translate_text_task.delay") as mock:
        mock.return_value.id = "mock_translate_job_id"
        yield mock

@pytest.fixture
def mock_generate_subtitles_task():
    with patch("api.core.dependencies.celery.tasks.video_subtitles_tasks.generate_subtitles_task.delay") as mock:
        mock.return_value.id = "mock_subtitles_job_id"
        yield mock

@pytest.fixture
def mock_create_project_with_job():
    with patch("api.v1.services.job.job_service.create_project_with_job") as mock:
        mock.return_value = AsyncMock(id="mock_project_id")
        yield mock

def test_translate_text_success(mock_translate_text_task, mock_create_project_with_job):
    request_data = TranslationRequest(text="Hello, world!", target_language="es")

    response = client.post(
        "/api/v1/tools/video-subtitles/translate",
        json=request_data.dict()
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Text translation job initiated successfully"
    assert "job_id" in response.json()["data"]
    assert "project_id" in response.json()["data"]

def test_transcribe_video_success(mock_transcribe_video_task, mock_create_project_with_job):
    with open("test_video.mp4", "rb") as video_file:
        response = client.post(
            "/api/v1/tools/video-subtitles/transcribe",
            files={"file": ("test_video.mp4", video_file, "video/mp4")},
        )

    assert response.status_code == 200
    assert response.json()["message"] == "Transcription job initiated successfully"
    assert "job_id" in response.json()["data"]
    assert "project_id" in response.json()["data"]

def test_generate_subtitles_success(mock_generate_subtitles_task, mock_create_project_with_job):
    with open("test_video.mp4", "rb") as video_file:
        response = client.post(
            "/api/v1/tools/video-subtitles/generate_subtitles",
            files={"file": ("test_video.mp4", video_file, "video/mp4")},
        )

    assert response.status_code == 200
    assert response.json()["message"] == "Subtitle generation job initiated successfully"
    assert "job_id" in response.json()["data"]
    assert "project_id" in response.json()["data"]
