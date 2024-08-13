import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from unittest.mock import patch, MagicMock
from main import app
from api.v1.services.ai_tools.thumbnail import upload_video_service
from api.utils.settings import settings

client = TestClient(app)


class MockSettings:
    MEDIA_DIR = './media'
    MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
    ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi'}


settings = MockSettings()


@patch('os.path.exists')
@patch('os.makedirs')
@patch('api.v1.services.ai_tools.thumbnail.upload_file')
@patch('api.v1.services.ai_tools.thumbnail.UploadFile')
async def mock_upload_file(mock_upload_file_class, mock_upload_file, mock_makedirs, mock_exists):
    def mock_exists_side_effect(path):
        if 'uploads' in path:
            return False
        return True

    mock_exists.side_effect = mock_exists_side_effect
    mock_upload_file.return_value = './media/uploads/videos/video-mocked.mov'

    mock_file = MagicMock()
    mock_file.filename = 'video.mov'
    mock_file.read.return_value = b'test video content'
    mock_upload_file_class.return_value = mock_file

    return mock_file


@patch('api.v1.services.ai_tools.thumbnail.upload_file', return_value='./media/uploads/videos/video-mocked.mov')
@patch('os.path.exists', return_value=False)
@patch('os.makedirs')
def test_upload_video_success(mock_makedirs, mock_exists, mock_upload_file):
    response = client.post(
        'api/v1/thumbnails/upload', files={'file': ('video.mov', b'test video content')})
    assert response.status_code == 200


@patch('api.v1.services.ai_tools.thumbnail.upload_file')
@patch('os.path.exists', return_value=False)
@patch('os.makedirs')
@patch('api.v1.services.ai_tools.thumbnail.UploadFile')
def test_upload_video_file_size_exceeds_limit(mock_file_class, mock_makedirs, mock_exists, mock_upload_file):

    mock_file = MagicMock()
    mock_file.filename = 'video.mov'
    mock_file.read.return_value = b'x' * (settings.MAX_FILE_SIZE + 1)
    mock_file_class.return_value = mock_file

    response = client.post(
        '/api/v1/thumbnails/upload',
        files={'file': ('video.mov', b'x' * (settings.MAX_FILE_SIZE + 1))}
    )

    assert response.status_code == 400


@patch('api.v1.services.ai_tools.thumbnail.upload_file')
@patch('os.path.exists', return_value=True)
@patch('os.makedirs')
def test_upload_video_file_already_exists(mock_makedirs, mock_exists, mock_upload_file):
    response = client.post(
        'api/v1/thumbnails/upload', files={'file': ('video.mov', b'test video content')})
    assert response.status_code == 400


@patch('api.v1.services.ai_tools.thumbnail.upload_file')
@patch('os.path.exists', return_value=False)
@patch('os.makedirs')
def test_upload_video_invalid_file_extension(mock_makedirs, mock_exists, mock_upload_file):
    response = client.post(
        'api/v1/thumbnails/upload', files={'file': ('video.txt', b'test video content')})
    assert response.status_code == 400
