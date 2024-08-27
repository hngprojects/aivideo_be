#!/usr/bin/env python3
"""Tests for the save_project endpoint"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from api.v1.routes.project import project_router
from api.v1.models.user import User
from api.db.database import get_db
from api.v1.services.project import project_service
from api.v1.services.user import user_service
from main import app

# Fixture to create a mock client with dependency overrides


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = lambda: MagicMock()
    app.dependency_overrides[project_service.fetch_project_by_id] = MagicMock()
    app.dependency_overrides[project_service.save_project] = MagicMock()
    app.dependency_overrides[user_service.get_current_user] = lambda: MagicMock(
        spec=User)
    client = TestClient(app)
    return client

# Mock user fixture


@pytest.fixture
def mock_user():
    return User(
        id="test_user_id",
        email="test_user@example.com",
    )

# Updated Mock project fixture


@pytest.fixture
def mock_project():
    project_mock = MagicMock()
    project_mock.id = "1"
    project_mock.name = "Test Project"
    project_mock.description = "A test project"
    project_mock.project_type = "Type A"  # Add a valid string for project_type
    project_mock.user_id = None  # None indicates the project isn't yet saved by a user
    project_mock.title = "Test Project"
    project_mock.file_url = "test_file_url"
    project_mock.result = "test_result"
    return project_mock

# Test the successful saving of a project


def test_save_project_success(client, mocker, mock_project, mock_user):
    # Mock the project and user services
    mocker.patch('api.v1.services.project.project_service.fetch_project_by_id',
                 return_value=mock_project)
    mocker.patch('api.v1.services.project.project_service.save_project')
    mocker.patch('api.v1.services.user.user_service.get_current_user',
                 return_value=mock_user)

    # Call the save_project endpoint
    response = client.put(
        "/api/v1/projects/1/save", headers={"Authorization": "Bearer test_token"})

    # Assert the response and service calls
    assert response.status_code == 200


# Test the scenario where a project is already saved


def test_save_project_already_saved(client, mocker, mock_project, mock_user):
    # Set the mock project to already have a user_id, simulating it being saved
    mock_project.user_id = mock_user.id

    # Mock the project service
    mocker.patch('api.v1.services.project.project_service.fetch_project_by_id',
                 return_value=mock_project)

    # Call the save_project endpoint
    response = client.put(
        "/api/v1/projects/1/save", headers={"Authorization": "Bearer test_token"},
        json={
            "result": "test_result"
        }
    )

    # Assert the response and service calls
    assert response.status_code == 400
