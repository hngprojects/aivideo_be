import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from unittest.mock import patch, MagicMock, mock_open
from main import app
from api.utils.settings import settings

client = TestClient(app)


class MockSettings:
    MEDIA_DIR = './media'
    MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
    ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi'}


settings = MockSettings()


@patch('api.core.dependencies.celery.tasks.video_tasks.upload_video_task.delay')
def test_upload_video_success(mock_task):
    mock_task.return_value.id = 'mock-task-id'

    response = client.post(
        '/api/v1/thumbnails/upload',
        files={'file': ('video.mov', b'test video content')}
    )

    assert response.status_code == 200


@patch('os.path.exists')
@patch('os.makedirs')
def test_upload_video_file_size_exceeds_limit(mock_makedirs, mock_exists):
    mock_exists.return_value = False

    response = client.post(
        '/api/v1/thumbnails/upload',
        files={'file': ('video.mov', b'x' * (settings.MAX_FILE_SIZE + 1))}
    )

    assert response.status_code == 400
    assert response.json()['message'] == 'File exceeds size limit'


@patch('os.path.exists')
@patch('os.makedirs')
def test_upload_video_invalid_file_extension(mock_makedirs, mock_exists):
    mock_exists.return_value = False

    response = client.post(
        '/api/v1/thumbnails/upload',
        files={'file': ('video.txt', b'test video content')}
    )

    assert response.status_code == 400
    assert response.json()['message'] == 'Invalid file format'
