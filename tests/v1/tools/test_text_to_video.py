import pytest
from fastapi.testclient import TestClient
from fastapi import status
from unittest.mock import patch, MagicMock
from main import app
from api.v1.models import User
from uuid_extensions import uuid7
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.v1.schemas.text_to_video import TextInputResponse, TextInputData


client = TestClient(app)

@pytest.fixture
def mock_db_session():
    """Fixture to create a mock database session."

    Yields:
        MagicMock: mock database
    """
    with patch("api.v1.services.user.get_db", autospec=True) as mock_get_db:
        mock_db = MagicMock()
        app.dependency_overrides[get_db] = lambda: mock_db
        yield mock_db
    app.dependency_overrides = {}

@pytest.fixture
def mock_get_current_user():
    """Fixture to create a mock current user"""
    with patch(
        "api.v1.services.user.UserService.get_current_user", autospec=True
    ) as mock_get_current_user:
        yield mock_get_current_user


@patch("api.v1.services.text_to_video.TextToVideoService.create", autospec=True)
def test_create_video_from_text(mock_create, mock_get_current_user, mock_db_session):
    """
    Test for text-to-video
    """
    user = User(id='user_id')
    
    (mock_get_current_user
     .return_value.query.return_value
     .filter.return_value.first.return_value) = user
    
    mock_create.return_value = TextInputResponse(
        message='successful',
        status_code=status.HTTP_200_OK,
        data=TextInputData(
            task_id='task_id',
            status='processing',
            user_id=user.id
        )
    )
    payload = {}
    headers = {"Authorization": "Bearer fake_token"}
    response = client.post('/api/v1/text-to-videos', json=payload, headers=headers)
    
    assert response.json() == {'status_code': 200,
                               'message': 'successful',
                               'data':
                                    {'status': 'processing',
                                     'task_id': 'task_id',
                                     'video_url': None}}