from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, Numeric, Enum
from sqlalchemy.orm import relationship
from api.v1.models.base_model import BaseTableModel
from secrets import token_hex


class Payment(BaseTableModel):
    __tablename__ = "payments"

    def generate_transaction_id():
        return f'cv-{datetime.now().strftime("%d%m%Y%H%M%S")}{token_hex(8)}'

    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    transaction_id = Column(String, unique=True, nullable=False, default=generate_transaction_id)
    amount = Column(Numeric, nullable=False)
    currency = Column(String, nullable=False)
    status = Column(Enum('pending', 'completed', 'canceled', name='payment_status_name'), nullable=False, server_default='pending')
    method = Column(String, nullable=False)  # credit card, paypal, stripe, flutterwave

    user = relationship("User", back_populates="payments")
