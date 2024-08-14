import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from api.v1.services.ai_tools.thumbnail import generate_thumbnails_service
from main import app

client = TestClient(app)


THUMBNAIL_GENERATION_URL = "/api/v1/thumbnails/generate-thumbnails"


@pytest.fixture
def mock_settings():
    class Settings:
        MEDIA_DIR = "/media"
    return Settings()


@patch('os.path.isfile', return_value=True)
@patch('os.makedirs')
@patch('subprocess.run')
def test_generate_thumbnails_success(mock_subprocess, mock_makedirs, mock_isfile, mock_settings):

    mock_subprocess.return_value = MagicMock(returncode=0, stdout=b'30.0')

    response = client.post(
        f"{THUMBNAIL_GENERATION_URL}?new_filename=test_video.mp4")

    assert response.status_code == 200


@patch('os.path.isfile', return_value=False)
@patch('os.makedirs')
def test_generate_thumbnails_file_not_found(mock_makedirs, mock_isfile, mock_settings):
    response = client.post(
        f"{THUMBNAIL_GENERATION_URL}?new_filename=non_existent_video.mp4")

    assert response.status_code == 404  


@patch('os.path.isfile', return_value=True)
@patch('os.makedirs')
@patch('subprocess.run')
def test_generate_thumbnails_ffprobe_failure(mock_subprocess, mock_makedirs, mock_isfile, mock_settings):

    mock_subprocess.return_value = MagicMock(returncode=1, stdout=b'')

    response = client.post(
        f"{THUMBNAIL_GENERATION_URL}?new_filename=test_video.mp4")

    assert response.status_code == 500


@patch('os.path.isfile', return_value=True)
@patch('os.makedirs')
@patch('subprocess.run')
def test_generate_thumbnails_ffmpeg_failure(mock_subprocess, mock_makedirs, mock_isfile, mock_settings):
    # Mocking subprocess to simulate a failure in generating a thumbnail
    mock_subprocess.side_effect = [
        MagicMock(returncode=0, stdout=b'30.0'),
        MagicMock(returncode=1)
    ]

    response = client.post(
        f"{THUMBNAIL_GENERATION_URL}?new_filename=test_video.mp4")

    assert response.status_code == 500
