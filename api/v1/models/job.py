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
    received = 'Received'
    progress = 'Progress'
    completed = 'Completed'
    failed = 'Failed'
    canceled = 'Canceled'


class TifiJob(BaseTableModel):

    __tablename__ = "tifi_jobs"

    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    tool_name = Column(String, nullable=False)
    is_premium = Column(Boolean, server_default='false', nullable=True)
    status = Column(saEnum('Pending', 'Received', 'Progress', 'Completed', 'Failed', 'Canceled', name='job_status'), server_default='Pending')
    progress = Column(String)
    payload = Column(JSON, nullable=True)
    result = Column(JSON, nullable=True)
    expiration_time = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="tifi_jobs")
    project = relationship("Project", back_populates="tifi_job")

    def is_expired(self) -> bool:
        return self.expiration_time.replace(tzinfo=None) <= datetime.now().replace(tzinfo=None)


def update_job(target, connection, status, result=None, progress='0% complete'):
    """This function updates a job

    Args:
        target (TifiJob): This is the specific job object you want to run the update on
        connection: This is the db connection
        status (str): Status you want to update the job status to
        result (JSON, optional): Result you want to update job result to. Defaults to None.
        progress (str, optional): The progress you want to update job progress to. Defaults to '0% complete'.
    """

    connection.execute(
        update(TifiJob)
        .where(TifiJob.id == target.id)
        .values(
            status=status,
            result=result,
            progress=progress
        )
    )


def run_job(mapper, connection, target):

    # from api.core.dependencies.jobs.service import execute_job
    # from api.core.dependencies.celery.tasks.run_job import run_job_in_celery

    try:
        # Update expiration time to 1 hour ahead
        connection.execute(
            update(TifiJob)
            .where(TifiJob.id == target.id)
            .values(
                expiration_time=target.created_at + timedelta(hours=1)
            )
        )
        
        # Initiate job in the background through celery
        # run_job_in_celery.delay(target.id)

        # update_job(
        #     target, 
        #     connection, 
        #     JobStatus.progress, 
        #     progress='50% complete'
        # )

        # # Call the tool to execute the job
        # job_result = execute_job(job=target)
        # update_job(
        #     target, 
        #     connection, 
        #     JobStatus.completed, 
        #     result=json.loads(job_result), 
        #     progress='100% complete'
        # )

        # # Update project result as well
        # connection.execute(
        #     update(Project)
        #     .where(Project.id == target.project_id)
        #     .values(
        #         result=json.loads(job_result),
        #         is_active=True
        #     )
        # )
    
    except Exception as e:
        # update_job(
        #     target, 
        #     connection, 
        #     JobStatus.failed, 
        #     result = {"error": f"{str(e)}"},
        #     progress='Job failed'
        # )
        print(f'An exception occured: {str(e)}')

        
event.listen(TifiJob, 'after_insert', run_job)
