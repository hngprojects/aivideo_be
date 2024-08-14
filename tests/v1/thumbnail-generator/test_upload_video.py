import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from unittest.mock import patch, MagicMock
from main import app
from api.utils.settings import settings

client = TestClient(app)


class MockSettings:
    MEDIA_DIR = './media'
    MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
    ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi'}


settings = MockSettings()


@patch('os.path.exists')
@patch('os.makedirs')
@patch('api.utils.files.upload_file')
def test_upload_video_success(mock_upload_file, mock_makedirs, mock_exists):
    mock_exists.return_value = False
    mock_upload_file.return_value = './media/uploads/videos/video-mocked.mov'

    mock_file = MagicMock()
    mock_file.filename = 'video.mov'
    mock_file.read.return_value = b'test video content'
    mock_upload_file_class.return_value = mock_file

    return mock_file


@patch('api.utils.files.upload_file', return_value='./media/uploads/videos/video-mocked.mov')
@patch('os.path.exists', return_value=False)
@patch('os.makedirs')
def test_upload_video_success(mock_makedirs, mock_exists, mock_upload_file):
    response = client.post(
        '/api/v1/thumbnails/upload', files={'file': ('video.mov', b'test video content')}
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
