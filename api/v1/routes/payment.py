from fastapi import Depends, APIRouter, status, HTTPException, Request
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from typing import Annotated


from api.v1.services.payment import payment_service, payment_gateway_service as pg_service
from api.v1.services.user_subscription import user_subscription_service as user_sub_service
from api.v1.schemas.payment import CreatePaymentSchema, CreatePaymentResponse
from api.v1.services.billing_plan import billing_plan_service as bp_service
from api.v1.schemas.user_subscription import CreateUserSubSchema
from api.utils.success_response import success_response
from api.v1.services.user import user_service
from api.utils.settings import settings
from api.db.database import get_db
from api.v1.models import User


payment = APIRouter(prefix="/payments", tags=["Payments"])


@payment.get("/initiate/{billing_plan_id}/{payment_gateway}", 
             status_code=status.HTTP_200_OK)
def initiate_payment(
    billing_plan_id: str,
    payment_gateway: str,
    request: Request,
    current_user: User = Depends(user_service.get_current_user),
    db: Session = Depends(get_db)
):
    """
    This configures data for requests going to payment gateways
    """
    # CONFIRM payment_gateway
    if payment_gateway != "flutterwave":
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Only fullterwave supported for now"
        )
    
    # GET billing plan
    bill_plan = bp_service.fetch(db, billing_plan_id)

    # # CONFIGURE return url
    # redirect_url = request.url_for(
    #     'handle_payment', billing_plan_id=billing_plan_id, 
    #     payment_gateway=payment_gateway)
    
    # GENERATE transaction reference
    tx_ref = f"{current_user.id}#{datetime.now(tz=timezone.utc).timestamp()}"

    # SET actual data for payment
    payment_data = {
        "tx_ref": tx_ref,
        "price": bill_plan.price,
        # "redirect_url": f"{redirect_url}",
        "currency": bill_plan.currency,
        "user_email": current_user.email,
        "public_key": settings.RAVE_PUBLIC_KEY,
        "private_key": settings.RAVE,
        "payment_title": "Convey AI Video Suites",
        "payment_description": "User subscription payment",
        "action_url": pg_service.FLUTTERWAVE_ONE_OFF_PAY_URL,
        "user_name": f"{current_user.first_name} {current_user.last_name}",
    }

    # RETURN payment data
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Payment data configured successfully",
        data=payment_data,
    )


@payment.post("/complete/{billing_plan_id}/{payment_gateway}", 
              response_model=CreatePaymentResponse, 
              status_code=status.HTTP_201_CREATED)
def complete_payment(
    billing_plan_id: str,
    payment_gateway: str,
    handle_payment: str,
    request: Request,
    payment_schema: CreatePaymentSchema,
    current_user: Annotated[User, Depends(user_service.get_current_user)],
    db: Session = Depends(get_db),
):
    """
    This handles responses from payment gateways
    """
    # CONFIRM payment_gateway
    if payment_gateway != "flutterwave":
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Only fullterwave supported for now"
        )
    
    # GET billing plan
    bill_plan = bp_service.fetch(db, billing_plan_id)

    # GET response data
    resp_d = request.json()
    
    # CONFIRM flutterwave payment
    _ = pg_service.confirm_flutterwave_payment(current_user.id, resp_d, bill_plan)

    # # INIT payment schema
    # payment_schema = PaymentCreate(
    #     status="completed",
    #     method="flutterwave",
    #     user_id=current_user.id,
    #     amount=bill_plan.amount,
    #     currency=bill_plan.currency,
    #     transaction_id=resp_d['transaction_id']
    # )

    # CREATE payment
    new_payment = payment_service.create(db=db, schema=payment_schema)

    # COMPUTE subscription start and end date
    start_datetime, end_datetime = user_sub_service\
        .get_sub_start_and_end_datetime(payment_schema.amount, bill_plan.amount)

    # CREATE user subscription
    user_sub_schema = CreateUserSubSchema(
        user_id=current_user.id,
        billing_plan_id=bill_plan.id,
        start_date=start_datetime,
        end_date=end_datetime
    )
    new_user_sub = user_sub_service.create(db=db, schema=user_sub_schema)

    # RETURN success response
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Payment added successfully",
        data={
            "payment": new_payment.to_dict(),
            "billing_plan": bill_plan.to_dict(),
            "subscription": new_user_sub.to_dict()
        },
    )