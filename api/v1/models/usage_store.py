"""UsageStore data model"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, ForeignKey,JSON
from sqlalchemy.orm import relationship
from api.v1.models.base_model import BaseTableModel
from sqlalchemy.dialects.postgresql import ARRAY

class UsageStore(BaseTableModel):
    __tablename__ = "usage_store"
    
    ip_address = Column(String, index=True, nullable=False)
    tool_access_count = Column(Integer, default=0)
    tools_accessed = Column(JSON, default={})
    last_accessed = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserUsageStore(BaseTableModel):
    __tablename__ = "user_usage_store"
    
    user_id = Column(String, ForeignKey('users.id', ondelete="CASCADE"))
    tool_access_count = Column(Integer, default=0)
    tools_accessed = Column(JSON, default={})
    last_accessed = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship('User', back_populates='usage_stored')
