from fastapi import Depends, APIRouter, status, HTTPException, Request, Query
from sqlalchemy.orm import Session
from uuid_extensions import uuid7
from typing import Annotated
from decimal import Decimal
import requests
import stripe
import json

from api.v1.services.billing_plan import billing_plan_service as bp_service
from api.v1.services.payment import payment_gateway_service as pg_service
from api.v1.schemas.payment import (
    InitiatePaymentSchema, InitiatePaymentResponse, PaymentListResponse,
    GetPaymentResponse
)
from api.utils.success_response import success_response
from api.v1.services.user import user_service
from api.utils.settings import settings
from api.db.database import get_db
from api.v1.models import User
from api.v1.services.payment import payment_service, payment_event_types
from api.v1.services.user_subscription import user_subscription_service


payments = APIRouter(prefix="/payments", tags=["Payments"])


@payments.post(
    "/initiate", response_model=InitiatePaymentResponse, status_code=status.HTTP_200_OK
)
async def initiate_payment(
    schema: InitiatePaymentSchema,
    current_user: User = Depends(user_service.get_current_user),
    db: Session = Depends(get_db),
):
    """
    This endpoint generates data for requests going to payment gateways
    """
    # validate payment_gateway
    # this checks that ONLY accepted payment gateways pass through
    payment_gateway = pg_service.validate_gateway(schema.payment_gateway)

    # get billing plan
    bill_plan = bp_service.fetch(db, schema.billing_plan_id)

    if payment_gateway == "flutterwave":
        # get a dictionary containing "payment_url" for flutterwave
        payment_url = pg_service.get_payment_url_for_flutterwave(
            current_user, bill_plan, schema)

    else:  # stripe
        # get a dictionary containing "payment_url" for stripe
        payment_url = pg_service.get_payment_url_for_stripe(
            current_user, bill_plan, schema)

    # RETURN payment data
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Payment initialized successfully",
        data=payment_url,
    )


@payments.get("/verify/{transaction_id}")
async def verify_payment_status(
    transaction_id: int | str,
    current_user: User = Depends(user_service.get_current_user),
    db: Session = Depends(get_db),
):
    """
    Verify payment status
    """

    VERIFY_URL = f"https://api.flutterwave.com/v3/transactions/{transaction_id}/verify"
    header = {"Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET}"}

    try:
        response = requests.get(VERIFY_URL, headers=header)
        response = response.json()

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Error verifying payment"
        )

    if response["status"] == "error":
        return success_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="No transaction was found for this id",
        )

    paid_amount = Decimal(response['data']['amount'])
    paid_currency = response['data']['currency']
    billing_plan_id = response['data']['tx_ref']
    bill_plan = bp_service.fetch(db, billing_plan_id)

    # Verify that paid amount is exact multiples of `bill_plan.price`
    pg_service.check_paid_amount_and_bill_per_interval(
        paid_amount, paid_currency, bill_plan)

    # check if payment record already exist
    payment_exist = payment_service.fetch_by_params(
        db, {'transaction_id': transaction_id})

    if not payment_exist:
        payload = {
            "user_id": current_user.id,
            "transaction_id": str(transaction_id),
            "amount": paid_amount,
            "currency": paid_currency,
            "status": "completed",
            "method": "flutterwave",
        }

        # Record payment
        payment_service.create(db, payload)

        # create a user subscription plan
        start_date, end_date = user_subscription_service.get_sub_start_and_end_datetime(
            bill_plan.plan_interval)

        user_subscription_payload = {
            "start_date": start_date,
            "billing_plan_id": billing_plan_id,
            "user_id": current_user.id,
            "end_date": end_date
        }
        user_subscription_service.create(db, user_subscription_payload)

    return success_response(
        status_code=status.HTTP_200_OK,
        message="Payment success",
        data={
            "amount": response["data"]["amount"],
            "currency": response["data"]["currency"],
        },
    )


@payments.post("/stripe/webhook")
async def stripe_webhook(
    req: Request,
    db: Session = Depends(get_db),
):
    """
    stripe webhook for event listening
    """

    payload = await req.body()
    stripe.api_key = settings.STRIPE_SECRET
    event = None

    try:
        event = stripe.Event.construct_from(
            json.loads(payload), stripe.api_key
        )
    except ValueError as e:
        return success_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Payment failed"
        )

    # Handle the event
    if event.type == payment_event_types.STRIPE_CHECHOUT_COMPLETED:
        payment = event.data
        paid_amount = Decimal(payment["amount_total"])
        paid_currency = payment['currency']
        billing_plan_id = payment['metadata']['billing_plan_id']

        bill_plan = bp_service.fetch(db, billing_plan_id)

        # Verify that paid amount is exact multiples of `bill_plan.price`
        pg_service.check_paid_amount_and_bill_per_interval(
            paid_amount, paid_currency, bill_plan)

        payment_payload = {
            "user_id": payment['metadata']['user_id'],
            "transaction_id": payment['id'],
            "amount": paid_amount,
            "currency": paid_currency,
            "status": "completed",
            "method": "stripe",
        }

        # Record payment
        payment_service.create(db, payment_payload)

        # create a user subscription plan
        start_date, end_date = user_subscription_service.get_sub_start_and_end_datetime(
            bill_plan.plan_interval)

        user_subscription_payload = {
            "start_date": start_date,
            "billing_plan_id": billing_plan_id,
            "user_id": payment['metadata']['user_id'],
            "end_date": end_date
        }
        user_subscription_service.create(db, user_subscription_payload)

    return success_response(
        status_code=status.HTTP_200_OK,
        message="Payment success"
    )


@payments.get("", status_code=status.HTTP_200_OK, response_model=PaymentListResponse)
def get_all_payments(
    _: User = Depends(user_service.get_current_super_admin),
    limit: Annotated[int, Query(
        ge=1, description="Number of payments per page")] = 10,
    page: Annotated[int, Query(
        ge=1, description="Page number (starts from 1)")] = 1,
    db: Session = Depends(get_db),
):
    """
    Endpoint to retrieve a paginated list of all payments by ``superadmin``.

    Query parameter:
        - limit: Number of payment per page (default: 10, minimum: 1)
        - page: Page number (starts from 1)
    """
    # get offset from page and limit
    offset = (page - 1) * limit

    # fetch all payments
    payments_l = payment_service.fetch_all(
        db, offset=offset, limit=limit,
    )

    # return success and data
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Payments fetched successfully",
        data=payment_service.dictize_payments_and_pagination(
            payments_l, offset, limit)
    )


@payments.post("/flutterwave/webhook")
async def flutterwave_webhook(
    req: Request,
    db: Session = Depends(get_db),
):
    """
    Flutterwave webhook for event listening
    """

    secret_hash = settings.FLW_SECRET_HASH
    signature = req.headers.get("verifi-hash")
    if signature == None or (signature != secret_hash):
        return success_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Payment failed"
        )

    payment = await req.body()

    # Handle the event
    if payment.event == payment_event_types.FLW_CHARGE_COMPLETED:
        paid_amount = Decimal(payment['data']["amount"])
        paid_currency = payment['data']['currency']
        user = user_service.fetch_by_params(
            db, {"email": payment['data']['email']})
        billing_plan_id = payment['data']['tx_ref']

        bill_plan = bp_service.fetch(db, billing_plan_id)

        # Verify that paid amount is exact multiples of `bill_plan.price`
        pg_service.check_paid_amount_and_bill_per_interval(
            paid_amount, paid_currency, bill_plan)

        payload = {
            "user_id": user.id,
            "transaction_id": payment['data']['id'],
            "amount": paid_amount,
            "currency": paid_currency,
            "status": "completed",
            "method": "flutterwave",
        }

        # Record payment
        payment_service.create(db, payload)

        # create a user subscription plan
        start_date, end_date = user_subscription_service.get_sub_start_and_end_datetime(
            bill_plan.plan_interval)

        user_subscription_payload = {
            "start_date": start_date,
            "billing_plan_id": billing_plan_id,
            "user_id": user.id,
            "end_date": end_date
        }
        user_subscription_service.create(db, user_subscription_payload)

        return success_response(
            status_code=status.HTTP_200_OK,
            message="Payment success"
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail='Payment not found'
    )


@payments.get("/current-user",
              status_code=status.HTTP_200_OK, response_model=PaymentListResponse
              )
def get_all_payments_for_current_user(
    current_user: User = Depends(user_service.get_current_user),
    limit: Annotated[int, Query(
        ge=1, description="Number of payments per page")] = 10,
    page: Annotated[int, Query(
        ge=1, description="Page number (starts from 1)")] = 1,
    db: Session = Depends(get_db),
):
    """
    Endpoint to retrieve a paginated list of all payments for/by ``current-user``.

    Query parameter:
        - limit: Number of payment per page (default: 10, minimum: 1)
        - page: Page number (starts from 1)
    """
    # get offset from page and limit
    offset = (page - 1) * limit

    # fetch all payments for current user
    payments_l = payment_service.fetch_all_for_user(
        db, current_user, offset, limit,
    )

    # return success and data
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Current user payments fetched successfully",
        data=payment_service.dictize_payments_and_pagination(
            payments_l, offset, limit)
    )


@payments.get("/{payment_id}",
              status_code=status.HTTP_200_OK, response_model=GetPaymentResponse)
def get_payment(
    payment_id: str,
    current_user: User = Depends(user_service.get_current_user),
    db: Session = Depends(get_db),
):
    """
    Endpoint to retrieve a single payment object by 
    ``superadmin`` OR ``user who owns the payment``.
    """
    # get the payment object
    payment = payment_service.fetch(db, payment_id)

    # check that current user is superadmin OR owns the payment
    user_service.check_superadmin_or_user_in_object(current_user, payment)

    # return success and data
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Payment fetched successfully",
        data=payment.to_dict()
    )
