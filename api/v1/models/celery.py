from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from api.v1.models.base_model import BaseTableModel


class CeleryTask(BaseTableModel):
    __tablename__ = "celery_tasks"

    task_id = Column(String, nullable=False)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    status = Column(String, server_default="PENDING")
    result = Column(Text, nullable=True)

    project = relationship("Project", back_populates="celery_tasks")
