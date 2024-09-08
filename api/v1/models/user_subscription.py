from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from api.v1.models.base_model import BaseTableModel

class UserSubscription(BaseTableModel):
    __tablename__ = 'user_subscriptions'

    billing_plan_id = Column(String, ForeignKey('billing_plans.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(String, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)

    billing_plan = relationship('BillingPlan', back_populates='subscriptions')
    user = relationship('User', back_populates='subscription')

    def is_active(self):
        return self.start_date <= datetime.now() and (self.end_date is None or self.end_date > datetime.now())
    