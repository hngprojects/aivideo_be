from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.v1.models.notifications import Notification
from api.v1.services.notification import notification_service
from api.v1.services.user import user_service
from datetime import datetime, timezone
from uuid_extensions import uuid7
from api.v1.schemas.notification import NotificationStatusEnum, NotificationTypeEnum

from main import app

def mock_notification():
    return Notification(
        id='user_id',
        receiver_id=str(uuid7()),
        title="Summarize Joe Rogan",
        message="Task done",
        notification_type= NotificationTypeEnum.SUCCESS,
        status=NotificationStatusEnum.UNREAD,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

def mock_db_session():
    db_session = MagicMock(spec=Session)
    return db_session

@pytest.fixture
def client():
    client = TestClient(app)
    return client

ENDPOINT = '/api/v1/dashboard/notifications'

class TestCodeUnderTest:
    @classmethod
    def setup_class(cls):
        app.dependency_overrides[user_service.get_current_user] = lambda: MagicMock()
        app.dependency_overrides[get_db] = mock_db_session

    @classmethod
    def teardown_class(cls):
        app.dependency_overrides = {}

    def test_get_all_notifications(self, client):
        """Test to verify response for getting all notifications."""

        mock_data = [
            Notification(
                id='user_id', receiver_id=str(uuid7()),
                title="Summarize Joe Rogan", message="Task done",
                created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
                notification_type= NotificationTypeEnum.SUCCESS,
                status=NotificationStatusEnum.UNREAD,
                ),
            Notification(
                id='user_id', receiver_id=str(uuid7()),
                title="Summarize Youtube", message="Task not done",
                created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
                notification_type= NotificationTypeEnum.SUCCESS,
                status=NotificationStatusEnum.UNREAD,
                )
        ]

        with patch("api.v1.services.notification.notification_service.fetch_all", return_value=mock_data):
            response = client.get(ENDPOINT)

            assert response.status_code == 200
            assert response.json()['data'][0]['title'] == mock_data[0].title
            assert response.json()['data'][1]['message'] == mock_data[1].message

    def test_get_all_notifications_empty(self, client):
        """Test to verify response for getting an empty list of notifications."""

        mock_data = []

        with patch("api.v1.services.notification.notification_service.fetch_all", return_value=mock_data):
            response = client.get(ENDPOINT)

            assert response.status_code == 200
            assert response.json().get('data') is None

    def test_get_notification_single(self, client):
        '''Test to successfully fetch a single notification'''

        mock_data = mock_notification()

        with patch("api.v1.services.notification.notification_service.fetch", return_value=mock_data):
            response = client.get(f'{ENDPOINT}/{mock_data.id}')

            assert response.status_code == 200
            response_json = response.json()
            assert 'data' in response_json  # Ensure 'data' key exists
            assert response.json()['data']['title'] == mock_data.title
            assert response.json()['data']['message'] == mock_data.message

    def test_get_notification_not_found(self, client):
        """Test when the notification ID does not exist."""

        nonexistent_id = str(uuid7())
        with patch("api.v1.services.notification.notification_service.fetch", return_value=None):
            response = client.get(f'{ENDPOINT}/{nonexistent_id}')

            assert response.status_code == 404
            assert response.json()['message'] == 'Notification not found'
# 