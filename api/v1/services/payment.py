from fastapi import HTTPException, status
import stripe.error
from sqlalchemy.orm import Session
from typing import Any, Optional, Union
from decimal import Decimal
import requests
import stripe

from api.v1.models.payment import Payment
from api.v1.models import User, BillingPlan
from api.utils.pagination import get_pagination_details
from api.utils.db_validators import check_model_existence, get_model_or_none, get_model_by_params
from api.utils.settings import settings


stripe.api_key = settings.STRIPE_SECRET


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
                    query = query.filter(
                        getattr(Payment, column).ilike(f"%{value}%"))

        if limit and offset:
            return query.offset(offset).limit(limit).all()
        
        return query.all()

    def fetch(self, db: Session, payment_id: str):
        """Fetches a payment by id"""
        payment = check_model_existence(db, Payment, payment_id)
        return payment

    def fetch_or_none(self, db: Session, payment_id: str):
        """Fetches a payment by id or returns None"""
        payment = get_model_or_none(db, Payment, payment_id)
        return payment

    def fetch_by_params(self, db: Session, query_params: dict):
        """Fetches a payment by one or more query params"""
        payment = get_model_by_params(db, Payment, query_params)
        return payment

    def fetch_all_for_user(
            self, db: Session, user: User, offset: int = 0, limit: int = 0):
        """Fetches all payments for/by a user"""

        query = db.query(Payment).filter(Payment.user_id == user.id)

        if limit and offset:
            payments = query.offset(offset).limit(limit).all()
        else:
            payments = query.all()

        return payments

    def dictize_payments_and_pagination(
            self, payments: list, offset: int = 0, limit: int = 0):
        """Return a list of dicts of all `Payment` objs with pagination
        
        Args:
          payments: A list of `Payment` objects.
          limit: For pagination: number of rows per page.
          offset: For pagination: number of rows to omit.
        
        Returns:
         A dictionary with two keys
         - payments: The list of dicts containg payments details
         - pagination: A dict containing pagination details
        """
        data = {
            "payments": [p.to_dict() for p in payments],
            "pagination": get_pagination_details(len(payments), offset, limit)
        }
        return data

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

    PAYMENT_GATEWAYS = ["stripe", "flutterwave"]

    FLUTTERWAVE_CHECKOUT_URL = "https://checkout.flutterwave.com/v3/hosted/pay"

    FLUTTERWAVE_PAYMENTS_URL = "https://api.flutterwave.com/v3/payments"

    def validate_gateway(self, gateway):
        """Confirm that the gateway passed in part 
        of the accepted payment gateways, then return 
        the lower case in case it's in another case"""
        if not isinstance(gateway, str) \
                or gateway.lower() not in self.PAYMENT_GATEWAYS:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail=f"Only {self.PAYMENT_GATEWAYS} supported for now"
            )
        return gateway.lower()

    def check_paid_amount_and_bill_per_interval(
        self, paid_amount: Union[int, float, Decimal], paid_currency: str, 
        bill_plan: BillingPlan, decimal_places: int = 2, enforce_one_interval=True
    ):
        """Check that payment received is equal to (or represents exact 
        multiples of) billing plan price per interval and checks currency accuracy.
        
        Args:
          paid_amount: The payment amount received.
          paid_currency: Currency of the payment received.
          bill_plan: The billing plan object being paid for.
          decimal_places: Number of decimal places to use in making the calculation.
          enforce_one_interval: Indicates whether payment for more than one interval
            should be allowed or not. Default is `True` meaning: Do Not Allow
        
        Returns:
          None

        Raises:
          HTTPException: If payment amount or currency do not match.
        """
        def invalid_pay_resp(message):
            return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
        
        paid_amount = Decimal(format(paid_amount, f".{decimal_places}f"))
        bill_per_interval = Decimal(format(bill_plan.price, f".{decimal_places}f"))
        
        # CHECK PAID AMOUNT AGAINST BILL PRICE PER INTERVAL
        if enforce_one_interval and (paid_amount != bill_per_interval):
            # checks that payment is equal to price when `enforce_one_interval` is True
            raise invalid_pay_resp("Error - paid amount doesn't match billing plan price")
        
        elif enforce_one_interval is False and (paid_amount % bill_per_interval):
            # checks that payment is multiples price when `enforce_one_interval` is False
            raise invalid_pay_resp("Error - paid amount is not multiples of billing plan price")
        
        # CHECK PAYMENT CURRENCY
        if paid_currency != bill_plan.currency:
            raise invalid_pay_resp("Error - invalid payment currency")

    def get_payment_url_for_flutterwave(self, user, bill_plan, schema):
        payment_data = {
            "tx_ref": bill_plan.id,
            "currency": bill_plan.currency,
            "amount": float(bill_plan.price),
            "redirect_url": schema.redirect_url,
            "payment_description": "User subscription payment",
            "payment_title": f"{bill_plan.plan_name} Subscription",
            "customer": {
                "email": user.email,
                "name": f"{user.first_name} {user.last_name}",
            },
        }

        # check for auto renew and create flutterwave payment plan
        if schema.auto_renew:
            subscription_plan_id = self.create_subscription_plan(bill_plan)
            payment_data['payment_plan'] = subscription_plan_id

        header = {"Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET}"}

        try:
            response = requests.post(
                self.FLUTTERWAVE_PAYMENTS_URL, json=payment_data, headers=header
            )

            return {"payment_url": response.json()["data"]["link"]}

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Error initializing payment"
            )

    def get_payment_url_for_stripe(self, user, bill_plan, schema):
        try:
            # Create a checkout session
            checkout_session = stripe.checkout.Session.create(
                line_items=[{
                    'price_data': {
                        'currency': bill_plan.currency,
                        'product_data': {
                            'name': bill_plan.plan_name,
                        },
                        # Convert to the smallest unit
                        'unit_amount': int(bill_plan.price * 100),
                    },
                    'quantity': 1,
                }],
                mode='subscription' if schema.auto_renew else 'payment',
                customer_email=user.email,  # Automatically fill in the user's email in the checkout
                success_url=schema.redirect_url,
                # cancel_url=cancel_url,
                metadata={
                    'user_id': user.id,
                    'billing_plan_id': bill_plan.id,
                    'plan_name': bill_plan.plan_name
                },
            )

            return {"payment_url": checkout_session["url"]}

        # except Exception as e:
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error initializing payment {str(e)}"
            )

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

            return response['data']['id']


payment_service = PaymentService()
payment_gateway_service = PaymentGatewayService()
