import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException
from uuid_extensions import uuid7


from main import app
from sqlalchemy.orm import Session
from api.utils.success_response import success_response
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from api.db.database import get_db
from api.v1.services.user import user_service
from api.v1.models.user import User
from api.v1.models.profile import Profile
from api.v1.services.profile import profile_service
from faker import Faker

fake = Faker()



def mock_get_current_user():
    return User(
        id=str(uuid7()),
        email="user103@example.com",
        password=user_service.hash_password("TestaUser@123"),
        first_name='John',
        last_name='Doe',
        is_active=True,
        is_superadmin=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

def mock_profile():
    return Profile(
        id=str(uuid7()),
        user_id=str(uuid7()),
        username="john_doe",
        pronouns="he/him",
        job_title="Software Engineer",
        social='{"twitter": "@username", "linkedin": "linkedin.com/in/username"}',
        bio="Passionate software engineer with a love for open-source projects.",
        phone_number="+1234567890",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

@pytest.fixture
def db_session_mock():
    db_session = MagicMock(spec=Session)
    return db_session

@pytest.fixture
def client(db_session_mock):
    app.dependency_overrides[get_db] = lambda: db_session_mock
    client = TestClient(app)
    yield client
    app.dependency_overrides = {}

def test_update_profile_success(client, db_session_mock):
    '''Test to successfully update a user profile'''

    # Mock the user service to return the current user
    app.dependency_overrides[user_service.get_current_user] = lambda: mock_get_current_user()
    
    # Mock profile update behavior
    mock_profile_instance = mock_profile()
    with patch("api.v1.services.profile.profile_service.update", return_value=mock_profile_instance) as mock_update:
        response = client.put(
            "/api/v1/profile",  
            json={
                "username": "mary",
                "pronouns": "him",
                "job_title": "job Engineer",
                "social": {
                    "twitter": "@username",
                    "linkedin": "linkedin.com/in/username"
                },
                "bio": "Passionate software engineer with a love for open-source projects new.",
                "phone_number": "+1234537890",
                "avatar_url": "https://example.com/avatar.jpg",
                "email": "user103@example.com"
            },
            headers={'Authorization': 'Bearer token'}
        )

        # Assert that the response was successful
        assert response.status_code == 200
        response_data = response.json()
        assert response_data['success'] is True
        assert response_data['message'] == "User Profile Updated Successfully!!!"
        assert response_data['data']  
