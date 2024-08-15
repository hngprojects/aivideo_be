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
    payment_gateway = pg_service.validate_gateway(schema.payment_gateway)

    # get billing plan
    bill_plan = bp_service.fetch(db, schema.billing_plan_id)

    # if payment_gateway == "flutterwave":
    #     pass
    # else:
    #     # stripe

    # payment_data = {
    #     "tx_ref": bill_plan.id,
    #     "currency": bill_plan.currency,
    #     "amount": float(bill_plan.price),
    #     "redirect_url": schema.redirect_url,
    #     "payment_title": "Convey AI Video Suites",
    #     "payment_description": "User subscription payment",
    #     "customer": {
    #         "email": current_user.email,
    #         "name": f"{current_user.first_name} {current_user.last_name}",
    #     },
    # }

    # if payment_gateway == "flutterwave" and schema.auto_renew:
    #     subscription_plan_id = pg_service.create_subscription_plan(bill_plan)
    #     payment_data['payment_plan'] = subscription_plan_id

    # header = {"Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET}"}

    if payment_gateway == "flutterwave":
        # get payment data for flutterwave
        payment_data = pg_service.get_payment_data_for_flutterwave(
            current_user, bill_plan, schema.redirect_url)
        
        # check for auto renew and create flutterwave payment plan
        if schema.auto_renew:
            subscription_plan_id = pg_service.create_subscription_plan(bill_plan)
            payment_data['payment_plan'] = subscription_plan_id

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
    else:
        # stripe
        pass

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

    amount = response['data']['amount']
    billing_plan_id = response['data']['tx_ref']
    bill_plan = bp_service.fetch(db, billing_plan_id)

    # Verify paid amount
    if bill_plan.price != amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Error - paid amount doesn't match billing plan price"
        )

    # check if payment record already exist
    payment_exist = payment_service.fetch(db, transaction_id)

    if not payment_exist:    
        payload = {
            "user_id": current_user.id,
            "transaction_id": str(transaction_id),
            "amount": amount,
            "currency": response['data']['currency'],
            "status": "completed",
            "method": "flutterwave",
        }

        # Record payment
        payment_service.create(db, payload)

        # create a user subscription plan
        start_date, end_date = user_subscription_service.get_sub_start_and_end_datetime(amount, amount)
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
