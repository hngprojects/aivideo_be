import pytest
from decimal import Decimal
from unittest.mock import patch
from uuid_extensions import uuid7
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from main import app
from api.db.database import get_db
from api.v1.models import User, BillingPlan, Payment


class StripeEvent:
    type = "checkout.session.completed"
    # data below is an actual 
    # data from a stripe test event
    data = {
        "object": {
            "id": "cs_test_a1VUSiYCvuxUnSTUaa8vdYEaTbfVWuvP8N7DtF8cpxpMqk7on1tlNfufmw",
            "object": "checkout.session",
            "after_expiration": None,
            "allow_promotion_codes": False,
            "amount_subtotal": 4999,
            "amount_total": 4999,
            "automatic_tax": {
            "enabled": False,
            "liability": None,
            "status": None
            },
            "billing_address_collection": "auto",
            "cancel_url": "https://stripe.com",
            "client_reference_id": None,
            "client_secret": None,
            "consent": None,
            "consent_collection": {
            "payment_method_reuse_agreement": None,
            "promotions": "none",
            "terms_of_service": "none"
            },
            "created": 1725101930,
            "currency": "usd",
            "currency_conversion": None,
            "custom_fields": [
            ],
            "custom_text": {
            "after_submit": None,
            "shipping_address": None,
            "submit": None,
            "terms_of_service_acceptance": None
            },
            "customer": "cus_QlLj7O144sr9er",
            "customer_creation": "if_required",
            "customer_details": {
            "address": {
                "city": None,
                "country": "NG",
                "line1": None,
                "line2": None,
                "postal_code": None,
                "state": None
            },
            "email": "chimeobioha@gmail.com",
            "name": "Chimeziri Obioha",
            "phone": None,
            "tax_exempt": "none",
            "tax_ids": [
            ]
            },
            "customer_email": None,
            "expires_at": 1725188329,
            "invoice": "in_1Ptp1zIiKrudT8J2WG2ygUnS",
            "invoice_creation": None,
            "livemode": False,
            "locale": "auto",
            "metadata": {
            "billing_plan_id": "premium_yearly",
            "platform_name": "tifi"
            },
            "mode": "subscription",
            "payment_intent": None,
            "payment_link": "plink_1PtmXfIiKrudT8J2yfZsynte",
            "payment_method_collection": "always",
            "payment_method_configuration_details": {
            "id": "pmc_1PthBwIiKrudT8J2JZ5UCemY",
            "parent": None
            },
            "payment_method_options": {
            "card": {
                "request_three_d_secure": "automatic"
            }
            },
            "payment_method_types": [
            "card",
            "link",
            "cashapp"
            ],
            "payment_status": "paid",
            "phone_number_collection": {
            "enabled": False
            },
            "recovered_from": None,
            "saved_payment_method_options": {
            "allow_redisplay_filters": [
                "always"
            ],
            "payment_method_remove": None,
            "payment_method_save": None
            },
            "setup_intent": None,
            "shipping_address_collection": None,
            "shipping_cost": None,
            "shipping_details": None,
            "shipping_options": [
            ],
            "status": "complete",
            "submit_type": "auto",
            "subscription": "sub_1Ptp1zIiKrudT8J2SD3qBtCN",
            "success_url": "https://tifi.tv/subscribe/success",
            "total_details": {
            "amount_discount": 0,
            "amount_shipping": 0,
            "amount_tax": 0
            },
            "ui_mode": "hosted",
            "url": None
        }
    }


client = TestClient(app)


# Mock database
@pytest.fixture
def mock_db_session(mocker):
    db_session_mock = mocker.MagicMock(spec=Session)
    app.dependency_overrides[get_db] = lambda: db_session_mock
    return db_session_mock


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
def test_bill_plan():
    bill_plan = BillingPlan(
        features=['One', 'Two'],
        plan_interval="yearly",
        plan_name="Premium Yearly",
        id="premium_yearly",
        currency="usd",
        price=49.99
    )
    return bill_plan


@pytest.fixture()
def test_payment(test_user):
    payment = Payment(
        id=str(uuid7()),
        amount=49.99,
        currency="uds",
        status="completed",
        method="stripe",
        user_id=test_user.id,
        transaction_id=StripeEvent.data['object']['id'],
        created_at=datetime.now(tz=timezone.utc)
    )
    return payment


@pytest.mark.asyncio
@patch("api.v1.services.payment.PaymentService.create")
@patch("api.v1.routes.payment.get_model_by_params")
@patch("api.v1.services.payment.PaymentService.fetch_by_params")
@patch("api.v1.routes.payment.bp_service")
@patch("api.v1.services.payment.stripe")
@patch("api.v1.services.payment.PaymentGatewayService.get_stripe_webhook_event")
async def test_subscription_success(
    mock_get_stripe_webhook_event,
    mock_stripe,
    mock_bp_service,
    mock_fetch_payment_by_params,
    mock_get_model_by_params,
    mock_payment_create,
    mock_db_session,
    test_user,
    test_bill_plan
):
    # set value for mocks
    mock_get_stripe_webhook_event.return_value = StripeEvent
    mock_stripe.api_key = "test_secret_key"
    mock_bp_service.fetch.return_value = test_bill_plan
    mock_fetch_payment_by_params.return_value = None
    mock_get_model_by_params.return_value = test_user

    response = client.post('api/v1/payments/stripe/webhook')

    assert response.status_code == 200

    event_data = StripeEvent.data['object']
    
    # test that call to create payment was made
    mock_payment_create.assert_called_once_with(
        mock_db_session,
        {
            "user_id": test_user.id,
            "transaction_id": event_data['id'],
            "amount": Decimal(format(test_bill_plan.price, ".2f")),
            "currency": event_data['currency'],
            "status": "completed",
            "method": "stripe",
        }
    )
    
    # this will fail if args are 
    # passed due to datetime differences
    mock_payment_create.assert_called_once()