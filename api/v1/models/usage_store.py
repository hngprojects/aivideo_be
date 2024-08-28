"""UsageStore data model"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from api.v1.models.base_model import BaseTableModel
from sqlalchemy.dialects.postgresql import ARRAY

class UsageStore(BaseTableModel):
    __tablename__ = 'usage_store'
    
    ip_address = Column(String, nullable=False)
    tool_access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    tools = relationship('ToolAccess', back_populates='usage_store', cascade="all, delete-orphan")


class ToolAccess(BaseTableModel):
    __tablename__ = 'tool_access'
    
    tool_name = Column(String, nullable=False)
    access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    usage_store_id = Column(String, ForeignKey('usage_store.id'), nullable=False)
    
    # Relationship with UsageStore
    usage_store = relationship('UsageStore', back_populates='tools')


class UserUsageStore(BaseTableModel):
    __tablename__ = "user_usage_store"
    
    user_id = Column(String, ForeignKey('users.id', ondelete="CASCADE"))
    tool_access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    tools = relationship('UserToolAccess', back_populates='usage_store', cascade="all, delete-orphan")
    user = relationship('User', back_populates='tool_usage')


class UserToolAccess(BaseTableModel):
    __tablename__ = 'user_tool_access'
    
    tool_name = Column(String, nullable=False)
    access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    usage_store_id = Column(String, ForeignKey('user_usage_store.id'), nullable=False)
    
    # Relationship with UsageStore
    usage_store = relationship('UserUsageStore', back_populates='tools')