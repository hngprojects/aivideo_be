from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from api.v1.models.base_model import BaseTableModel


class Job(BaseTableModel):
    __tablename__ = "jobs"

    job_id = Column(String, nullable=False)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    status = Column(String, server_default="PENDING")
    result = Column(Text, nullable=True)

    project = relationship("Project", back_populates="job", uselist=False)
    user = relationship("User", back_populates="jobs")
