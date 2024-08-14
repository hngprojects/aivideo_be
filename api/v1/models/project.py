from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from api.v1.models.base_model import BaseTableModel


class Project(BaseTableModel):
    __tablename__ = 'projects'

    user_id = Column(String, ForeignKey('users.id', ondelete="CASCADE"))
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    project_type = Column(String, nullable=False)
    file_url = Column(String, nullable=True)
    result = Column(Text, nullable=True)
    archived = Column(Boolean, server_default='false')
    is_deleted = Column(Boolean, server_default='false')
    archived_at = Column(DateTime, nullable=True)

    user = relationship('User', back_populates='projects')
    jobs = relationship("Job", back_populates="project")
