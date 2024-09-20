from datetime import datetime, timedelta
import json
from sqlalchemy import Column, String, Text, ForeignKey, JSON, Enum as saEnum, Boolean, update, DateTime
from enum import Enum
from sqlalchemy.orm import relationship
from sqlalchemy import event

from api.v1.models.base_model import BaseTableModel
from api.v1.models.project import Project


class Job(BaseTableModel):
    __tablename__ = "jobs"

    job_id = Column(String, nullable=False)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    status = Column(String, server_default="PENDING")
    result = Column(Text, nullable=True)

    project = relationship("Project", back_populates="job", uselist=False)
    user = relationship("User", back_populates="jobs")


class JobStatus(str, Enum):

    pending = 'Pending'
    processing = 'Processing'
    progress = 'Progress'
    completed = 'Completed'
    failed = 'Failed'
    canceled = 'Canceled'


class TifiJob(BaseTableModel):

    __tablename__ = "tifi_jobs"

    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    # project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    tool_name = Column(String, nullable=False)
    is_premium = Column(Boolean, server_default='false', nullable=True)
    status = Column(String, server_default='Pending')
    progress = Column(String)
    status_message = Column(String, nullable=True)
    payload = Column(JSON, nullable=True)
    result = Column(JSON, nullable=True)
    expiration_time = Column(DateTime(timezone=True), nullable=True)
    is_parallel = Column(Boolean, server_default='false')  # New field to indicate parallel compatibility

    # user = relationship("User", back_populates="tifi_jobs")
    # project = relationship("Project", back_populates="tifi_job")

    def is_expired(self) -> bool:
        return self.expiration_time.replace(tzinfo=None) <= datetime.now().replace(tzinfo=None)


def run_job(mapper, connection, target):
    try:
        # Update expiration time to 1 hour ahead
        connection.execute(
            update(TifiJob)
            .where(TifiJob.id == target.id)
            .values(
                expiration_time=target.created_at + timedelta(hours=1)
            )
        )
    
    except Exception as e:
        print(f'An exception occured: {str(e)}')

        
event.listen(TifiJob, 'after_insert', run_job)
