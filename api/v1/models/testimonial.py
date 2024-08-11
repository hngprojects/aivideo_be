from sqlalchemy import Column, String, Text, Float
from api.v1.models.base_model import BaseTableModel


class Testimonial(BaseTableModel):
    __tablename__ = 'testimonials'

    content = Column(Text, nullable=False)
    client_name = Column(String, nullable=False)
    rating = Column(Float, default=1, nullable=False)
