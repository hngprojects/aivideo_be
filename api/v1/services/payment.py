from fastapi import HTTPException, status
from api.v1.models.payment import Payment
from sqlalchemy.orm import Session
from typing import Any, Optional
from decimal import Decimal
import requests

from api.v1.models.payment import Payment
from api.v1.models import User, BillingPlan
from api.utils.db_validators import check_model_existence
from api.utils.settings import settings


class PaymentService:
    """Payment service functionality"""

    def create(self, db: Session, schema):
        """Create a new payment"""

        new_payment = Payment(**schema)
        db.add(new_payment)
        db.commit()
        db.refresh(new_payment)

        return new_payment

    def fetch_all(self, db: Session, offset: int = 0, limit: int = 0, **query_params: Optional[Any]):
        """Fetch all payments with option to search using query parameters"""

        query = db.query(Payment)

        # Enable filter by query parameter
        if query_params:
            for column, value in query_params.items():
                if hasattr(Payment, column) and value:
                    query = query.filter(getattr(Payment, column).ilike(f"%{value}%"))

        if limit and offset:
            payments = query.offset(offset).limit(limit).all()
        else:
            payments = query.all()

        if len(payments) < 1:
            # RETURN not found message
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Payments not found"
            )
        
        return payments

    def fetch(self, db: Session, payment_id: str):
        """Fetches a payment by id"""
        
        payment = check_model_existence(db, Payment, payment_id)
        return payment

    def fetch_all_for_user(
            self, db: Session, user_id, limit: int = 0, page: int = 0):
        """Fetches all payments for a user"""

        # check if user exists
        _ = check_model_existence(db, User, user_id)

        if limit and page:
            # calculating offset value
            # from page and limit given
            offset_value = (page - 1) * limit

            # Filter to return only 
            # payments of the user_id
            payments = (
                db.query(Payment)
                .filter(Payment.user_id == user_id)
                .offset(offset_value)
                .limit(limit)
                .all()
            )
        else:
            # Filter to return only 
            # payments of the user_id
            payments = (
                db.query(Payment)
                .filter(Payment.user_id == user_id)
                .all()
            )

        return payments

    def update(self, db: Session, payment_id: str, schema):
        """Updates a payment"""

        payment = self.fetch(db=db, payment_id=payment_id)

        # Update the fields with the provided schema data
        update_data = schema.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(payment, key, value)

        db.commit()
        db.refresh(payment)
        return payment

    def delete(self, db: Session, payment_id: str):
        """Deletes a payment"""

        payment = self.fetch(db=db, payment_id=payment_id)
        db.delete(payment)
        db.commit()


class PaymentGatewayService:
    """Payment gateway service functionality"""

    PAYMENT_GATEWAYS = ["Stripe", "Flutterwave", "Lemonsqueezy"]

    FLUTTERWAVE_CHECKOUT_URL = "https://checkout.flutterwave.com/v3/hosted/pay"

    FLUTTERWAVE_PAYMENTS_URL = "https://api.flutterwave.com/v3/payments"

    def confirm_flutterwave_payment(self, data: dict, billing_plan: BillingPlan):
        """Handle checkout response from `flutterwave`"""

        if data.get('status') not in ("successful", "completed"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transaction not successful."
            )

        if Decimal(data.get('amount')) != Decimal(f"{billing_plan.price}"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid payment amount."
            )
        
        if data.get('currency') != billing_plan.currency:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid currency."
            )
        
        return True

    def create_subscription_plan(self, plan: BillingPlan):
        """
        Set up flutterwave subscription plan with plan name and interval
        """

        payload = {
            "amount": float(plan.price),
            "name": plan.plan_name,
            "interval": plan.plan_interval,
        }

        API_URL = 'https://api.flutterwave.com/v3/payment-plans'
        header = {'Authorization': f"Bearer {settings.FLUTTERWAVE_SECRET}"}

        try:
            response = requests.post(
                API_URL,
                json=payload,
                headers=header
            )
        except Exception as e:
            print(e)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Error enabling auto-renewal"
            )

        if response.status_code == 200:
            response = response.json()
            subscription_plan_id = response['data']['id']

            return subscription_plan_id
            
payment_service = PaymentService()
payment_gateway_service = PaymentGatewayService()