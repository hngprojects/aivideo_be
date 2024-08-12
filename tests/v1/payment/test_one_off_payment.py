import pytest
import requests
from decouple import config
from rave_python import Rave
from uuid_extensions import uuid7
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from main import app
from api.db.database import get_db
from api.utils.settings import settings
from api.v1.services.user import user_service
from api.v1.models import User, Organisation, BillingPlan, Payment
from api.v1.services.payment import payment_service, payment_gateway_service as pg_service


client = TestClient(app)


# Mock database
@pytest.fixture
def mock_db_session(mocker):
    db_session_mock = mocker.MagicMock(spec=Session)
    app.dependency_overrides[get_db] = lambda: db_session_mock
    db_session_mock.rave = Rave(
        config("RAVE_PUBLIC_KEY_TEST"),
        config("RAVE_SECRET_KEY_TEST"),
        usingEnv=False
    )
    return db_session_mock


@pytest.fixture
def mock_user_service():
    with patch("api.v1.services.user.user_service", autospec=True) as user_service_mock:
        yield user_service_mock


@pytest.fixture
def mock_payment_service():
    with patch(
        "api.v1.services.payment.payment_service", autospec=True
    ) as payment_service_mock:
        yield payment_service_mock


@pytest.fixture
def mock_gateway_service():
    with patch(
        "api.v1.services.payment.payment_gateway_service", autospec=True
    ) as gateway_service_mock:
        yield gateway_service_mock


@pytest.fixture
def mock_rave_account():
    # with patch(".venv.Lib.site-packages.rave_python.Rave", autospec=True) as rave_account_mock:
    with patch(".venv.Lib.site-packages.rave_python.rave_account.Account", autospec=True) as rave_account_mock:
        yield rave_account_mock


@pytest.fixture()
def test_org():
    org = Organisation(id=str(uuid7()), name="Org 1")
    return org


@pytest.fixture()
def test_bill_plan(test_org):
    bill_plan = BillingPlan(
        organisation_id=test_org.id,
        duration="Monthly",
        id=str(uuid7()),
        currency="NGN",
        description="",
        name="BP 1",
        price=5000
    )
    return bill_plan


# Test User
@pytest.fixture
def test_user():
    user = User(
        id=str(uuid7()),
        email="testuser@gmail.com",
        password="hashedpassword",
        first_name="test",
        last_name="user",
        is_active=True,
    )
    return user


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
def access_token_user(test_user):
    return user_service.create_access_token(user_id=test_user.id)


@pytest.fixture
def random_access_token():
    return user_service.create_access_token(user_id=str(uuid7()))


def test_configure_payment_successful(
    mock_db_session,
    test_user,
    test_bill_plan,
    access_token_user,
):
    mock_db_session.query().filter().first.return_value = test_user
    mock_db_session.query().get.return_value = test_bill_plan

    # Make request
    headers = {"Authorization": f"Bearer {access_token_user}"}
    get_url = f"/api/v1/payments/configure/{test_bill_plan.id}/flutterwave"
    response = client.get(get_url, headers=headers)
    assert response.status_code == 200

    resp_d = response.json()
    assert resp_d['success'] == True
    assert resp_d["message"] == "Payment data configured successfully"

    data =  resp_d['data']
    assert data['user_email'] == test_user.email
    assert data['price'] == test_bill_plan.price
    assert data['tx_ref'].startswith(test_user.id)
    assert data['currency'] == test_bill_plan.currency
    assert data['payment_title'] == "Convey AI Video Suites"
    assert data['public_key'] == config('RAVE_PUBLIC_KEY_TEST')
    assert data['payment_description'] == "User subscription payment"
    assert data['action_url'] == pg_service.FLUTTERWAVE_ONE_OFF_PAY_URL
    assert data['user_name'] == f"{test_user.first_name} {test_user.last_name}"
    assert data['redirect_url'] == f"http://testserver/api/v1/payments/handle/{test_bill_plan.id}/flutterwave"


# def test_handle_payment_successful(
#     mock_db_session,
#     test_user,
#     test_payment,
#     test_bill_plan,
#     access_token_user,
# ):
#     mock_db_session.query().filter().first.return_value = test_user
#     mock_db_session.query().get.return_value = test_bill_plan
#     mock_db_session.get.return_value = test_payment
#     mock_rave_account.verify = test_payment
#     mock_db_session.rave.verify = test_payment

#     tx_ref = f"{test_user.id}#{datetime.now(tz=timezone.utc).timestamp()}"

#     payment_data = {
#         "tx_ref": tx_ref,
#         "currency": test_bill_plan.currency,
#         "amount": float(test_bill_plan.price),
#         "redirect_url": "http://example.com",
#         "customer":{
#             "email": test_user.email,
#             "name": f"{test_user.first_name} {test_user.last_name}"
#         },
#     }

#     # Make request to flutterwave
#     post_url = 'https://api.flutterwave.com/v3/payments'
#     headers = {"Authorization": f"Bearer {config('RAVE_SECRET_KEY_TEST')}"}
#     response = requests.post(post_url, json=payment_data, headers=headers)
#     assert response.status_code == 200

#     t_return = pg_service.confirm_flutterwave_payment(
#         test_user.id, 
#         {'tx_ref': tx_ref, 'status': 'completed', 'transaction_id': tx_ref},
#         test_bill_plan
#     )
#     print(t_return)


def test_configure_payment_unsuccessful(
    mock_db_session,
    test_user,
    test_bill_plan,
    access_token_user,
):
    headers = {"Authorization": f"Bearer {access_token_user}"}
    mock_db_session.query().filter().first.return_value = test_user
    mock_db_session.query().get.return_value = test_bill_plan

    # NON-FLUTTERWAVE
    get_url = f"/api/v1/payments/configure/{test_bill_plan.id}/anothergateway"
    response = client.get(get_url, headers=headers)
    assert response.status_code == 403
    assert response.json()["message"] == "Only fullterwave supported for now"
    # reset url to correct one
    get_url = f"/api/v1/payments/configure/{test_bill_plan.id}/flutterwave"


    # WRONG billing plan id
    mock_db_session.query().get.return_value = None
    response = client.get(get_url, headers=headers)
    assert response.status_code == 404
    assert response.json()["message"] == "Billing plan not found."
    # reset billing plan mock to correct one
    mock_db_session.query().get.return_value = test_bill_plan


    # NO AUTH
    response = client.get(get_url)
    assert response.status_code == 401
    assert response.json()['message'] == 'Not authenticated'
