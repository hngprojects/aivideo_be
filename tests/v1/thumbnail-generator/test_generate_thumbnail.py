import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app
from api.utils.settings import settings

client = TestClient(app)


class MockTask:
    def __init__(self, task_id):
        self.id = task_id


class MockSettings:
    MEDIA_DIR = './media'
    MAX_FILE_SIZE = 100 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi'}


settings = MockSettings()


@pytest.fixture
def mock_generate_thumbnails_task(mocker):
    return mocker.patch("api.core.dependencies.celery.tasks.video_tasks.generate_thumbnails_task.delay", return_value=MockTask(task_id='mock-task-id'))


@patch('subprocess.run')
@patch('os.path.isfile')
@patch('os.makedirs')
def test_generate_thumbnails_success(mock_makedirs, mock_isfile, mock_run, mock_generate_thumbnails_task):
    mock_isfile.return_value = True
    mock_run.return_value = MagicMock(returncode=0, stdout=b"120.0")

    response = client.post(
        '/api/v1/thumbnails/generate-thumbnails',
        json={
            "video_id": "video-id-mocked",
        }
    )

    assert response.status_code == 200


@patch('subprocess.run')
@patch('os.path.isfile')
@patch('os.makedirs')
def test_generate_thumbnails_manual_capture_success(mock_makedirs, mock_isfile, mock_run):
    mock_isfile.return_value = True
    mock_run.return_value = MagicMock(returncode=0)

    response = client.post(
        '/api/v1/thumbnails/generate-thumbnails',
        json={
            "video_id": "video-id-mocked",
            "manual_capture": True,
            "timestamp": 30.0
        }
    )

    assert response.status_code == 200


@patch('os.path.isfile')
def test_generate_thumbnails_video_not_found(mock_isfile):
    mock_isfile.return_value = False

    response = client.post(
        '/api/v1/thumbnails/generate-thumbnails',
        json={
            "video_id": "non-existent-video-id",

        }
    )

    assert response.status_code == 404


@patch('subprocess.run')
@patch('os.path.isfile')
@patch('os.makedirs')
def test_generate_thumbnails_ffmpeg_error(mock_makedirs, mock_isfile, mock_run):
    mock_isfile.return_value = True
    mock_run.return_value = MagicMock(
        returncode=1, stderr=b"Error")  
    response = client.post(
        '/api/v1/thumbnails/generate-thumbnails',
        json={
            "video_id": "video-id-mocked",

        }
    )

    assert response.status_code == 500
