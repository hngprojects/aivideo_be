import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# Mocked settings and data
mock_video_id = 'mock-video-id'
mock_thumbnail_id = 'mock-thumbnail-id'
mock_resolution = '720p'
mock_base_url = 'http://testserver'
mock_thumbnail_url = f"{mock_base_url}/media/downloads/thumbnails/{mock_video_id}_thumbnail_{mock_thumbnail_id}_{mock_resolution}.jpg"


@pytest.fixture
def mock_select_and_download_thumbnail_task(mocker):
    mock_task = MagicMock()
    mock_task.id = 'mock-task-id'

    return mocker.patch("api.core.dependencies.celery.tasks.video_tasks.select_and_download_thumbnail_task.delay", return_value=mock_task)


@pytest.fixture
def mock_create_project_with_job(mocker):
    return mocker.patch("api.v1.services.job.job_service.create_project_with_job", return_value=MagicMock(id='project-id'))


def test_select_thumbnail_success(
    mock_select_and_download_thumbnail_task,
    mock_create_project_with_job
):
    response = client.post(
        f'/api/v1/tools/thumbnail-generator/select-thumbnail/{mock_video_id}',
        json={
            'thumbnail_id': mock_thumbnail_id,
            'resolution': mock_resolution
        }
    )

    assert response.status_code == 200
