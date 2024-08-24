import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from main import app
from api.v1.routes.ai_tools.talking_avatar import video_router

client = TestClient(app)

@pytest.mark.asyncio
@patch('api.core.dependencies.celery.tasks.video_tasks.geenerate_video_from_script_task.apply_async')
@patch('api.v1.services.job.job_service.create_project_with_job')
async def test_text_to_video_success_validation_error(
    mock_create_project_with_job,
    mock_apply_async
):
    # Arrange
    mock_apply_async.return_value.id = "test_task_id"
    mock_create_project_with_job.return_value.id = "test_project_id"

    # Act
    response = client.post(
        "/api/v1/tools/video/text-to-video/generate-video",
        json={
            "script": "test script",
        }
    )

    # Assert
    assert response.status_code == 422
    

@pytest.mark.asyncio
@patch('api.core.dependencies.celery.tasks.video_tasks.geenerate_video_from_script_task.apply_async')
@patch('api.v1.services.job.job_service.create_project_with_job')
@patch('api.v1.services.presets.preset_service.fetch_music_by_id')
async def test_text_to_video_success(
    mock_create_project_with_job,
    mock_apply_async,
    mock_music_by_id
):
    # Arrange
    mock_apply_async.return_value.id = "test_task_id"
    mock_create_project_with_job.return_value.id = "test_project_id"
    mock_music_by_id.return_value.id = "audio-id"

    # Act
    response = client.post(
        "/api/v1/tools/video/text-to-video/generate-video",
        json={
            "script": "Test script to test video",
            "audio_id": "audio-id",
            "aspect_ratio": "horizontal",
            "voice_over": "woman",
            "scenes": [
                "A man jogging with a red shirt and white shoes", 
                "1. In a bustling office, a group of programmers sit at their computers", 
                "2. A young child sits in front of a computer, eagerly typing "
            ]
        }
    )

    # Assert
    assert response.status_code == 202


@pytest.mark.asyncio
@patch('api.db.database.get_db')
@patch('api.v1.services.ai_tools.text_to_video.ttv_service')
def test_recompose_script(mock_db, mock_ttv_service):
    # Arrange
    sample_script = "This is a sample script."
    recomposed_script = "This is the recomposed script."
    mock_ttv_service.recompose_script.return_value = recomposed_script

    schema = {
        "script": sample_script
    }

    # Act
    response = client.post("/api/v1/tools/video/text-to-video/recompose-script", json=schema)

    # Assert
    assert response.status_code == 200
