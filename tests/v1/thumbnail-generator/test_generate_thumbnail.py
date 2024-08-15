import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app
from api.utils.settings import settings

client = TestClient(app)

# Define mock settings


class MockSettings:
    MEDIA_DIR = './media'
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi'}


settings = MockSettings()

mock_video_id = 'mock-video-id'
mock_base_url = 'http://testserver'
mock_thumbnail_url = f"{mock_base_url}/media/downloads/thumbnails/mock-thumbnail.jpg"


@pytest.fixture
def mock_generate_thumbnails_service(mocker):
    return mocker.patch("api.v1.services.ai_tools.thumbnail.generate_thumbnails_service", return_value=[mock_thumbnail_url])


@pytest.fixture
def mock_generate_thumbnails_task(mocker):
    return mocker.patch("api.core.dependencies.celery.tasks.video_tasks.generate_thumbnails_task", return_value=[mock_thumbnail_url])


@pytest.fixture
def mock_create_project_with_job(mocker):
    return mocker.patch("api.v1.services.job.job_service.create_project_with_job", return_value=MagicMock(id='project-id'))


@pytest.fixture
def mock_isfile(mocker):
    return mocker.patch('os.path.isfile', return_value=True)


@pytest.fixture
def mock_makedirs(mocker):
    return mocker.patch('os.makedirs')


@pytest.mark.asyncio
async def test_generate_thumbnails_success(mock_generate_thumbnails_task, mock_create_project_with_job, mock_isfile, mock_makedirs):
    with patch('subprocess.run') as mock_subprocess_run:
        mock_subprocess_run.return_value.returncode = 0

        response = await client.post(
            '/api/v1/thumbnails/generate-thumbnails',
            json={
                'video_id': mock_video_id,
            }
        )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_generate_thumbnails_video_not_found(mock_isfile):
    with patch('os.path.isfile', return_value=False):
        response = await client.post(
            '/api/v1/thumbnails/generate-thumbnails',
            json={
                'video_id': mock_video_id,
                'manual_capture': False
            }
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_generate_thumbnails_error(mock_isfile):
    with patch('subprocess.run') as mock_subprocess_run:
        mock_subprocess_run.return_value.returncode = 1
        with patch('os.path.isfile', return_value=True):
            response = await client.post(
                '/api/v1/thumbnails/generate-thumbnails',
                json={
                    'video_id': mock_video_id,
                    'manual_capture': False
                }
            )

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_generate_thumbnails_manual_capture(mock_makedirs, mock_isfile):
    with patch('subprocess.run') as mock_subprocess_run:
        mock_subprocess_run.return_value.returncode = 0
        with patch('os.path.isfile', return_value=True):
            response = await client.post(
                '/api/v1/thumbnails/generate-thumbnails',
                json={
                    'video_id': mock_video_id,
                    'manual_capture': True,
                    'timestamp': 10.0
                }
            )

    assert response.status_code == 200
