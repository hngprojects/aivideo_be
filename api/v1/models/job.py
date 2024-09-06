from sqlalchemy import Column, String, Text, ForeignKey, JSON, Enum, Boolean
from enum import Enum
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


# class JobStatus(str, Enum):

#     pending = 'Pending'
#     received = 'Received'
#     progress = 'Progress'
#     completed = 'Completed'
#     failed = 'Failed'
#     cancelled = 'Cancelled'


# class TifiJob(BaseTableModel):

#     __tablename__ = "tifi_jobs"

#     user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
#     tool_name = Column(String, nullable=False)
#     is_premium = Column(Boolean, server_default='false', nullable=True)
#     status = Column(Enum(JobStatus), server_default=JobStatus.pending.value)
#     progress = Column(String)
#     payload = Column(JSON, nullable=True)
#     result = Column(JSON, nullable=True)

#     user = relationship("User", back_populates="tifi_jobs")
