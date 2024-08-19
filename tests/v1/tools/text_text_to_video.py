import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from main import app
from api.v1.routes.ai_tools.talking_avatar import video_router

client = TestClient(app)

@pytest.mark.asyncio
@patch('api.v1.routes.ai_tools.talking_avatar.geenerate_video_from_text_task.delay')
@patch('api.v1.routes.ai_tools.talking_avatar.job_service.create_project_with_job')
async def test_talking_head_avatar_selection(
    mock_create_project_with_job,
    mock_delay
):
    # Arrange
    mock_delay.return_value.id = "test_task_id"
    mock_create_project_with_job.return_value.id = "test_project_id"

    # Act
    response = client.post(
        "/api/v1/tools/video/text-to-video",
        json={
            "scritp": "test script",
        }
    )

    # Assert
    assert response.status_code == 202
