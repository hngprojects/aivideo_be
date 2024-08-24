from sqlalchemy import Column, String, Text
from api.v1.models.base_model import BaseTableModel


class HelpTopics(BaseTableModel):
    __tablename__ = 'help_topics'

    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)