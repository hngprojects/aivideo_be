from fastapi import Depends, APIRouter, status, HTTPException
from sqlalchemy.orm import Session
from uuid_extensions import uuid7
import requests


from api.v1.services.payment import payment_gateway_service as pg_service
from api.v1.schemas.payment import InitiatePaymentSchema, InitiatePaymentResponse
from api.v1.services.billing_plan import billing_plan_service as bp_service
from api.utils.success_response import success_response
from api.v1.services.user import user_service
from api.utils.settings import settings
from api.db.database import get_db
from api.v1.models import User
from api.v1.services.payment import payment_service


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
    # CONFIRM payment_gateway
    if schema.payment_gateway != "flutterwave":
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail="Only flutterwave supported for now"
        )

    # GET billing plan
    bill_plan = bp_service.fetch(db, schema.billing_plan_id)

    payment_data = {
        "tx_ref": str(uuid7()),
        "currency": bill_plan.currency,
        "amount": float(bill_plan.price),
        "redirect_url": schema.redirect_url,
        "payment_title": "Convey AI Video Suites",
        "payment_description": "User subscription payment",
        "customer": {
            "email": current_user.email,
            "name": f"{current_user.first_name} {current_user.last_name}",
        },
    }

    header = {"Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET}"}

    try:
        response = requests.post(
            pg_service.FLUTTERWAVE_PAYMENTS_URL, json=payment_data, headers=header
        )
        response = response.json()

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Error initializing payment"
        )

    # RETURN payment data
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Payment initialized successfully",
        data={"payment_url": response["data"]["link"]},
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

    payload = {
        "user_id": current_user.id,
        "transaction_id": transaction_id,
        "amount": response["data"]["amount"],
        "currency": response["data"]["currency"],
        "status": "completed",
        "method": "flutterwave",
    }

    payment_service.create(db, payload)

    return success_response(
        status_code=status.HTTP_200_OK,
        message="Payment success",
        data={
            "amount": response["data"]["amount"],
            "currency": response["data"]["currency"],
        },
    )
