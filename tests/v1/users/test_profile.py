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



# Test for unauthorized access
def test_update_profile_unauthorized(client):
    '''Test unauthorized access when no token is provided'''
    response = client.put(
        "/api/v1/profile",  
        json={}
    )
    response_data = response.json()
    assert response.status_code == 401
    assert response_data['status_code'] == 401
    
    
    
    

# Test for invalid data
def test_update_profile_invalid_data(client, db_session_mock):
    '''Test for invalid profile data'''
    app.dependency_overrides[user_service.get_current_user] = lambda: mock_get_current_user()

    response = client.put(
        "/api/v1/profile",  
        json={
            "username": 12,  
            "pronouns": "him",
            "job_title": "job Engineer",
            "social": {
                "twitter": "@username",
                "linkedin": "linkedin.com/in/username"
            },
            "bio": "Bio",  
            "phone_number": "+123",
            "avatar_url": "invalid-url",
            "email": "user103@example.com"
        },
        headers={'Authorization': 'Bearer token'}
    )

    response_data = response.json()
    assert response.status_code == 422
    assert response_data['status_code'] == 422





# Test for email already in use
def test_update_profile_email_in_use(client, db_session_mock):
    '''Test for email already in use error'''

    app.dependency_overrides[user_service.get_current_user] = lambda: mock_get_current_user()
    
    with patch("api.v1.services.profile.profile_service.update", side_effect=HTTPException(status_code=409, detail="Email address already in use")) as mock_update:
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
                "email": "existing_email@example.com"
            },
            headers={'Authorization': 'Bearer token'}
        )

        response_data = response.json()
        assert response.status_code == 409
        assert response_data['status_code'] == 409


def custom_service_function(*args, **kwargs):
    raise HTTPException(status_code=500, detail="Database error occurred")

def test_update_profile_custom_error(client, db_session_mock):
    '''Test for server error using a custom exception'''

    # Mock the current user
    app.dependency_overrides[user_service.get_current_user] = lambda: mock_get_current_user()

    # Use a custom service function that raises an HTTPException
    with patch("api.v1.services.profile.profile_service.update", side_effect=custom_service_function):
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

        # Assert that the response status code is 500
        assert response.status_code == 500