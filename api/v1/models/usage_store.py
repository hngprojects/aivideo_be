"""UsageStore data model"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from api.v1.models.base_model import BaseTableModel
from sqlalchemy.dialects.postgresql import ARRAY



class ToolAccess(BaseTableModel):
    __tablename__ = 'tool_access'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    usage_store_id = Column(Integer, ForeignKey('usage_store.id'))
    tool_name = Column(String, nullable=False)
    access_count = Column(Integer, default=0)
    
    usage_store = relationship('UsageStore', back_populates='tool_accesses')

class UsageStore(BaseTableModel):
    __tablename__ = 'usage_store'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ip_address = Column(String, nullable=False)
    tool_access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime, nullable=False)
    
    tool_accesses = relationship('ToolAccess', back_populates='usage_store')

class UserUsageStore(BaseTableModel):
    __tablename__ = "user_usage_store"
    
    user_id = Column(String, ForeignKey('users.id', ondelete="CASCADE"))
    tool_access_count = Column(Integer, default=0)
    tool_accesses = relationship('ToolAccess', back_populates='usage_store')
    last_accessed = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship('User', back_populates='usage_stored')
