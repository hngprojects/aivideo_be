from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch, MagicMock
import pytest

client = TestClient(app)

class MockTask:
    def __init__(self, task_id):
        self.id = task_id

@pytest.fixture
def mock_transcribe_task(mocker):
    return mocker.patch("api.core.dependencies.celery.tasks.audio_task.transcribe_audio_task.delay", return_value=MockTask(task_id='task-id'))

@pytest.fixture
def mock_create_project_with_job(mocker):
    return mocker.patch("api.v1.services.job.job_service.create_project_with_job", return_value=MagicMock(id='project-id'))

def test_upload_audio_success(mock_transcribe_task, mock_create_project_with_job):

    valid_audio_content = b"audio data"  

    response = client.post(
        "/api/v1/tools/audio-transcribe/upload/",
        files={"file": ("audio.mp3", valid_audio_content, "audio/mpeg")}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Audio transcription job initiated successfully"
    assert data["data"]["job_id"] == "task-id"
    assert data["data"]["project_id"] == "project-id"