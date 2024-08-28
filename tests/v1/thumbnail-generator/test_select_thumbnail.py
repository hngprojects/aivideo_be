import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


mock_thumbnail_url = 'http://testserver/media/downloads/thumbnails/mock-video-id_thumbnail_mock-thumbnail-id_720p.jpg'


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
        '/api/v1/tools/thumbnail-generator/select-thumbnail',
        data={
            'thumbnail_url': mock_thumbnail_url
        }
    )

    assert response.status_code == 202
