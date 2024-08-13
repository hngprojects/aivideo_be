from enum import Enum
from sqlalchemy import (
    Column,
    String,
    ForeignKey,
    DateTime,
    Boolean,
    Enum as SQLAlchemyEnum,
)
from sqlalchemy.orm import relationship
from api.v1.models.base_model import BaseTableModel


class ProjectStatus(Enum):
    rejected = "rejected"
    failed = "failed"
    pending = "pending"
    completed = "completed"


class Project(BaseTableModel):
    __tablename__ = "projects"

    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"))
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    project_type = Column(String, nullable=False)
    file_url = Column(String, nullable=True)
    result = Column(String, nullable=True)
    archived = Column(Boolean, server_default="false")
    is_deleted = Column(Boolean, server_default="false")
    archived_at = Column(DateTime, nullable=True)
    duration = Column(String, nullable=True)
    size = Column(String, nullable=False)
    status = Column(SQLAlchemyEnum(ProjectStatus), nullable=False, default="pending")

    user = relationship("User", back_populates="projects")
    celery_tasks = relationship("CeleryTask", back_populates="project")

    def __str__(self) -> str:
        return self.title
