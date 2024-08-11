# app/models/billing_plan.py
from sqlalchemy import Column, String, ARRAY, DECIMAL
from sqlalchemy.orm import relationship
from api.v1.models.base_model import BaseTableModel


class BillingPlan(BaseTableModel):
    __tablename__ = 'billing_plans'

    id = Column(String, primary_key=True)
    plan_name = Column(String, nullable=False)
    price = Column(DECIMAL, nullable=False)
    currency = Column(String, nullable=False)
    features = Column(ARRAY(String), nullable=False)

    subscriptions = relationship('UserSubscription', back_populates='billing_plan')