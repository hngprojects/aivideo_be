import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from celery.result import AsyncResult

from api.v1.routes import background_router
from api.utils.success_response import success_response
from api.v1.services.job import job_service

client = TestClient(background_router)

@pytest.fixture
def mock_db_session(mocker):
    # Mock the database session
    return mocker.MagicMock(spec=Session)

@pytest.fixture
def mock_async_result(mocker):
    # Mock Celery AsyncResult
    return mocker.patch('api.v1.endpoints.jobs.AsyncResult', autospec=True)

@pytest.fixture
def mock_job_service(mocker):
    # Mock job_service methods
    mocker.patch('api.v1.endpoints.jobs.job_service.get_project_from_job', return_value=MagicMock())
    mocker.patch('api.v1.endpoints.jobs.job_service.update_job', return_value=None)

def test_send_job_status_updates_success(mock_db_session, mock_async_result, mock_job_service):
    mock_async_result.return_value.state = 'SUCCESS'
    mock_async_result.return_value.result = "Job completed successfully"
    
    response = client.get('/api/v1/jobs/test_job_id/status', dependencies=[mock_db_session])
    
    assert response.status_code == 200

def test_send_job_status_updates_failure(mock_db_session, mock_async_result, mock_job_service):
    mock_async_result.return_value.state = 'FAILURE'
    mock_async_result.return_value.info = "Some error occurred"
    
    response = client.get('/api/v1/jobs/test_job_id/status', dependencies=[mock_db_session])
    
    assert response.status_code == 200

def test_send_job_status_updates_pending(mock_db_session, mock_async_result, mock_job_service):
    mock_async_result.return_value.state = 'PENDING'
    
    response = client.get('/api/v1//jobs/test_job_id/status', dependencies=[mock_db_session])
    
    assert response.status_code == 200

# Example test for the SSE endpoint
@pytest.mark.asyncio
async def test_send_job_status_updates_over_sse(mock_db_session, mock_async_result, mock_job_service):
    mock_async_result.return_value.state = 'SUCCESS'
    mock_async_result.return_value.result = "Job completed successfully"

    response = client.get('/api/v1/jobs/test_job_id/sse/progress', dependencies=[mock_db_session])

    assert response.status_code == 200
