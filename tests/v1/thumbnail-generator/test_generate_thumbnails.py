import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# Mocked settings and data
mock_video_id = 'mock-video-id'
mock_base_url = 'http://testserver'
mock_thumbnail_url = f"{mock_base_url}/media/downloads/thumbnails/mock-thumbnail.jpg"


@pytest.fixture
def mock_generate_thumbnails_task(mocker):
    mock_task = MagicMock()
    mock_task.id = 'mock-task-id'
    # No need to mock `get()` here since we're just returning the task ID
    return mocker.patch("api.core.dependencies.celery.tasks.video_tasks.generate_thumbnails_task.delay", return_value=mock_task)


@pytest.fixture
def mock_create_project_with_job(mocker):
    return mocker.patch("api.v1.services.job.job_service.create_project_with_job", return_value=MagicMock(id='project-id'))


@pytest.fixture
def mock_isfile(mocker):
    return mocker.patch('os.path.isfile', return_value=True)


@pytest.fixture
def mock_makedirs(mocker):
    return mocker.patch('os.makedirs')


def test_generate_thumbnails_success(
    mock_generate_thumbnails_task,
    mock_create_project_with_job,
    mock_isfile,
    mock_makedirs
):
    response = client.post(
        '/api/v1/tools/thumbnail-generator/generate-thumbnails',
        data={
            'video_id': mock_video_id,
            'timestamp': 0
        }
    )
    assert response.status_code == 200


def test_generate_thumbnails_manual_capture(
    mock_generate_thumbnails_task,
    mock_create_project_with_job,
    mock_isfile,
    mock_makedirs
):
    response = client.post(
        '/api/v1/tools/thumbnail-generator/generate-thumbnails',
        data={
            'video_id': mock_video_id,
            'timestamp': 10.0
        }
    )
    assert response.status_code == 200
