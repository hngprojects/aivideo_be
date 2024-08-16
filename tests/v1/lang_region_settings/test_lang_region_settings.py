import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import HTTPException
from uuid_extensions import uuid7
import json
import os
import tempfile
from main import app
from sqlalchemy.orm import Session
from api.db.database import get_db
from api.v1.services.lang_region_settings import region_service
from api.v1.services.user import user_service
from api.v1.models.user import User
from api.v1.schemas.lang_region_settings import RegionCreate, RegionUpdate
from datetime import datetime, timezone
from faker import Faker


fake = Faker()

def mock_get_current_user():
    return User(
        id=str(uuid7()),
        email="user103@example.com",
        password="hashed_password",
        first_name='John',
        last_name='Doe',
        is_active=True,
        is_superadmin=False,
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

def test_create_region(client, db_session_mock):
    '''Test for creating a region successfully'''
    
    app.dependency_overrides[user_service.get_current_user] = lambda: mock_get_current_user()

    mock_region = {
        "region": "Test Region",
        "timezone": "GMT",
        "language": "English"
    }
    
    with patch("api.v1.services.lang_region_settings.region_service.create", return_value=mock_region) as mock_create:
        response = client.post(
            "api/v1/regions",
            json=mock_region,
            headers={'Authorization': 'Bearer token'}
        )
        
        assert response.status_code == 201



def test_get_regions(client, db_session_mock):
    '''Test for fetching all regions successfully'''
    
    mock_regions = [{"name": "Region1", "code": "R1"}, {"name": "Region2", "code": "R2"}]
    
    with patch("api.v1.services.lang_region_settings.region_service.fetch_all", return_value=mock_regions) as mock_fetch:
        response = client.get(
            "api/v1/regions",
            headers={'Authorization': 'Bearer token'}
        )
        
        assert response.status_code == 200
    

def test_get_region_by_user(client, db_session_mock):
    '''Test for fetching a specific region by ID successfully'''
    
    region_id = str(uuid7())
    mock_region = {"id": region_id, "name": "Test Region", "code": "TR"}
    
    with patch("api.v1.services.lang_region_settings.region_service.fetch", return_value=mock_region) as mock_fetch:
        response = client.get(
            f"api/v1/regions/{region_id}",
            headers={'Authorization': 'Bearer token'}
        )
        
        assert response.status_code == 200
   

def test_update_region(client, db_session_mock):
    '''Test for updating a region successfully'''
    
    region_id = str(uuid7())
    update_data = {"name": "Updated Region", "code": "UR"}
    mock_region = {"id": region_id, **update_data}
    
    with patch("api.v1.services.lang_region_settings.region_service.update", return_value=mock_region) as mock_update:
        response = client.put(
            f"api/v1/regions/{region_id}",
            json=update_data,
            headers={'Authorization': 'Bearer token'}
        )
        
        assert response.status_code == 200
    

def test_delete_region(client, db_session_mock):
    '''Test for deleting a region successfully'''
    
    region_id = str(uuid7())
    
    with patch("api.v1.services.lang_region_settings.region_service.delete", return_value=None) as mock_delete:
        response = client.delete(
            f"api/v1/regions/{region_id}",
            headers={'Authorization': 'Bearer token'}
        )
        
        assert response.status_code == 204
