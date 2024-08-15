import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from main import app

client = TestClient(app)

# Define mock settings
mock_video_id = 'mock-video-id'
mock_thumbnail_id = 'mock-thumbnail-id'
mock_resolution = '720'
mock_base_url = 'http://testserver'
mock_thumbnail_url = f"{mock_base_url}/media/downloads/thumbnails/{mock_video_id}_thumbnail_{mock_thumbnail_id}_{mock_resolution}.jpg"


@pytest.fixture
def mock_celery_task(mocker):
    mock_task = MagicMock()
    mock_task.id = 'mock-task-id'
    mocker.patch('celery.app.task.Task.apply_async', return_value=mock_task)
    return mock_task


@pytest.fixture
def mock_select_and_download_thumbnail_task(mocker):
    mock_task = MagicMock()
    mock_task.id = 'mock-task-id'
    mock_task.delay.return_value = mock_task
    return mocker.patch("api.core.dependencies.celery.tasks.video_tasks.select_and_download_thumbnail_task", return_value=mock_task)


@pytest.fixture
def mock_create_project_with_job(mocker):
    return mocker.patch("api.v1.services.job.job_service.create_project_with_job", return_value=MagicMock(id='project-id'))


def test_select_thumbnail_success(mock_celery_task, mock_create_project_with_job):
    mock_celery_task.get.return_value = mock_thumbnail_url

    response = client.post(
        f'/api/v1/tools/thumbnail-generator/select-thumbnail/{mock_video_id}',
        json={
            'thumbnail_id': mock_thumbnail_id,
            'resolution': mock_resolution
        }
    )
    assert response.status_code == 200
    assert response.json()['data']['thumbnail_url'] == mock_thumbnail_url


def test_select_thumbnail_failure(mock_celery_task, mock_create_project_with_job):
    mock_celery_task.get.return_value = None

    response = client.post(
        f'/api/v1/tools/thumbnail-generator/select-thumbnail/{mock_video_id}',
        json={
            'thumbnail_id': mock_thumbnail_id,
            'resolution': mock_resolution
        }
    )
    assert response.status_code == 404
