import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from unittest.mock import patch, MagicMock, mock_open
from main import app
from api.utils.settings import settings

client = TestClient(app)


class MockTask:
    def __init__(self, task_id):
        self.id = task_id

    def get(self, timeout=None):
        return '{"video_id": "mock-video-id"}'


class MockSettings:
    MEDIA_DIR = './media'
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi'}


settings = MockSettings()


@pytest.fixture
def mock_upload_video_task(mocker):
    return mocker.patch("api.core.dependencies.celery.tasks.video_tasks.upload_video_task.delay", return_value=MockTask(task_id='mock-task-id'))


@pytest.fixture
def mock_process_youtube_video_task(mocker):
    return mocker.patch("api.core.dependencies.celery.tasks.video_tasks.process_youtube_video_task.delay", return_value=MockTask(task_id='mock-task-id'))


@pytest.fixture
def mock_create_project_with_job(mocker):
    return mocker.patch("api.v1.services.job.job_service.create_project_with_job", return_value=MagicMock(id='project-id'))


@patch('api.utils.files.upload_file', return_value='./media/uploads/videos/video-mocked.mov')
@patch('os.path.exists', return_value=True)
@patch('os.makedirs')
@patch('builtins.open', new_callable=mock_open)
def test_upload_video_success(mock_open, mock_makedirs, mock_exists, mock_upload_file, mock_upload_video_task, mock_create_project_with_job):
    mock_file = MagicMock()
    mock_file.filename = 'video.mov'
    mock_file.read.return_value = b'test video content'

    response = client.post(
        '/api/v1/tools/thumbnail-generator/upload-or-process',
        files={'file': ('video.mov', mock_file.read())}
    )

    assert response.status_code == 200
    assert 'job_id' in response.json()['data']
    assert 'project_id' in response.json()['data']


@patch('os.path.exists')
@patch('os.makedirs')
def test_upload_video_file_size_exceeds_limit(mock_makedirs, mock_exists):
    mock_exists.return_value = False

    response = client.post(
        '/api/v1/tools/thumbnail-generator/upload-or-process',
        files={'file': ('video.mov', b'x' * (settings.MAX_FILE_SIZE + 1))}
    )

    assert response.status_code == 400


@patch('os.path.exists')
@patch('os.makedirs')
def test_upload_video_invalid_file_extension(mock_makedirs, mock_exists):
    mock_exists.return_value = False

    response = client.post(
        '/api/v1/tools/thumbnail-generator/upload-or-process',
        files={'file': ('video.txt', b'test video content')}
    )

    assert response.status_code == 400


def test_process_youtube_video_success(mock_process_youtube_video_task, mock_create_project_with_job):
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    response = client.post(
        '/api/v1/tools/thumbnail-generator/upload-or-process',
        data={'youtube_url': youtube_url}
    )
    print(f"response: {response.json()}")

    assert response.status_code == 200


def test_upload_or_process_video_no_input_provided():
    response = client.post(
        '/api/v1/tools/thumbnail-generator/upload-or-process')

    assert response.status_code == 400
