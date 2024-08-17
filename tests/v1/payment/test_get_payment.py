import pytest
from uuid_extensions import uuid7
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from main import app
from api.db.database import get_db
from api.v1.models import User, Payment
from api.v1.services.user import user_service

client = TestClient(app)

# Mock database
@pytest.fixture
def mock_db_session(mocker):
    db_session_mock = mocker.MagicMock(spec=Session)
    app.dependency_overrides[get_db] = lambda: db_session_mock
    return db_session_mock

@pytest.fixture
def mock_user_service():
    with patch("api.v1.services.user.user_service", autospec=True) as user_service_mock:
        yield user_service_mock

@pytest.fixture
def mock_payment_service():
    with patch("api.v1.services.payment.payment_service", autospec=True) as payment_service_mock:
        yield payment_service_mock

# Test User
@pytest.fixture
def test_user():
    return User(
        id=str(uuid7()),
        email="testuser@gmail.com",
        password="hashedpassword",
        first_name="test",
        last_name="user",
        is_active=True
    )

# Super Admin
@pytest.fixture
def super_admin():
    return User(
        id=str(uuid7()),
        email="superadmin@gmail.com",
        password="hashedpassword",
        first_name="super",
        last_name="admin",
        is_active=True,
        is_superadmin=True
    )


@pytest.fixture()
def test_payment(test_user):
    payment = Payment(
        id=str(uuid7()),
        amount=5000.00,
        currency="NGN",
        status="completed",
        method="flutterwave",
        user_id=test_user.id,
        transaction_id=str(uuid7()),
        created_at=datetime.now(tz=timezone.utc)
    )
    return payment


@pytest.fixture
def access_token_test_user(test_user):
    return user_service.create_access_token(user_id=test_user.id)

@pytest.fixture
def access_token_super_admin(super_admin):
    return user_service.create_access_token(user_id=super_admin.id)

@pytest.fixture
def random_access_tokenr():
    return user_service.create_access_token(user_id='hshsdgdgdgdgdgdg')

def make_request(token, payment):
    return client.get(
        f"/api/v1/payments/{payment.id}", 
        headers={"Authorization": f"Bearer {token}"}
    )


# Test for successful retrieve of payment
def test_get_payment_successful(
    mock_db_session,
    test_user,
    test_payment,
    access_token_test_user
):
    # Mock the query for getting user
    mock_db_session.query().filter().first.return_value = test_user

    # Mock the query for payment
    mock_db_session.query().get.return_value = test_payment

    # Make request
    response = make_request(access_token_test_user, test_payment)
    resp_d = response.json()

    print(resp_d)

    # FOR USER ONWER
    assert response.status_code == 200
    assert resp_d['success'] is True
    assert resp_d['message'] == "Payment fetched successfully"
    
    # FOR SUPER ADMIN
    mock_db_session.query().filter().first.return_value = super_admin
    # mock_user_service.
    response = make_request(access_token_super_admin, test_payment)
    resp_d = response.json()
    assert response.status_code == 200
    assert resp_d['success'] is True
    assert resp_d['message'] == "Payment fetched successfully"

    pay = resp_d['data']
    assert pay['id'] == test_payment.id
    assert pay['status'] == test_payment.status
    assert pay['method'] == test_payment.method
    assert pay['user_id'] == test_payment.user_id
    assert pay['currency'] == test_payment.currency
    assert float(pay['amount']) == test_payment.amount
    assert pay['transaction_id'] == test_payment.transaction_id
    assert datetime.fromisoformat(pay['created_at']) == test_payment.created_at


# Test for unauthenticated requests
def test_for_unauthenticated_requests(
    mock_db_session,
    test_user,
    test_payment
):
    # Mock the query for getting user
    mock_db_session.query().filter().first.return_value = test_user

    # WRONG AUTH TOKEN
    response = make_request(random_access_tokenr, test_payment)
    print(response.json())
    assert response.status_code == 401
    assert response.json()['message'] == "Could not validate credentials"

    # NO AUTH TOKEN
    response = client.get(f"/api/v1/payments/{test_payment.id}")
    assert response.status_code == 401
    assert response.json()['message'] == "Not authenticated"

    # NON-SUPERADMIN / NON-OWNER
    # --remove the superadmin privilege from superadmin-- #
    super_admin.is_superadmin = False
    mock_db_session.query().filter().first.return_value = super_admin
    resp = make_request(access_token_super_admin, test_payment)
    assert resp.status_code == 403
    assert resp.json()[
        "message"] == "You do not have permission to access this resource"


# Test for no payment 
def test_for_payment_not_found(
    mock_db_session,
    test_user,
    test_payment,
    access_token_test_user
):
    # Mock the query for getting user
    mock_db_session.query().filter().first.return_value = test_user

    mock_db_session.query().get.return_value = None

    # Make request
    response = make_request(access_token_test_user, test_payment)
    print(response.json())
    assert response.status_code == 404
    assert response.json()['message'] == "Payment does not exist"
    assert not response.json().get('data')
