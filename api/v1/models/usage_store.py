"""UsageStore data model"""

from datetime import datetime, timedelta

from sqlalchemy import Column, DateTime, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from api.v1.models.base_model import BaseTableModel


class UsageStore(BaseTableModel):
    __tablename__ = 'usage_store'
    
    ip_address = Column(String, nullable=False)
    tool_access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    tools = relationship('ToolAccess', back_populates='usage_store', cascade="all, delete-orphan")
    
    def is_access_count_exceeded(self, access_limit):
        """Check if tool_access_count is greater than 3."""
        return self.tool_access_count >= access_limit

    def is_last_accessed_old(self, hours: int):
        """Check if last_accessed is more than hours old."""
        if self.last_accessed:
            return datetime.utcnow() - self.last_accessed > timedelta(hours=hours)
        return False
    
    def time_until(self, hours: int):
        """Calculate the remaining time until last_accessed reaches 24 hours."""
        now = datetime.utcnow()
        
        # Time elapsed since last_accessed
        time_elapsed = now - self.last_accessed
        
        # Remaining time to reach 24 hours
        time_remaining = timedelta(hours=24) - time_elapsed
        
        # If more than 24 hours have already passed
        if time_remaining < timedelta():
            time_remaining = timedelta(0)
        
        # Convert timedelta to hours, minutes, and seconds
        hours, remainder = divmod(time_remaining.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return int(hours), int(minutes), int(seconds)


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

    def is_access_count_exceeded(self, access_limit):
        """Check if tool_access_count is greater than 3."""
        return self.tool_access_count >= access_limit

    def is_last_accessed_old(self, hours: int):
        """Check if last_accessed is more than 24 hours old."""
        if self.last_accessed:
            return datetime.utcnow() - self.last_accessed > timedelta(hours=hours)
        return False
    
    from datetime import datetime, timedelta

    def time_until(self, hours: int):
        """Calculate the remaining time until last_accessed reaches 24 hours."""
        now = datetime.utcnow()
        
        # Time elapsed since last_accessed
        time_elapsed = now - self.last_accessed
        
        # Remaining time to reach 24 hours
        time_remaining = timedelta(hours=24) - time_elapsed
        
        # If more than 24 hours have already passed
        if time_remaining < timedelta():
            time_remaining = timedelta(0)
        
        # Convert timedelta to hours, minutes, and seconds
        hours, remainder = divmod(time_remaining.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return int(hours), int(minutes), int(seconds)


class UserToolAccess(BaseTableModel):
    __tablename__ = 'user_tool_access'
    
    tool_name = Column(String, nullable=False)
    access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    usage_store_id = Column(String, ForeignKey('user_usage_store.id'), nullable=False)
    
    # Relationship with UsageStore
    usage_store = relationship('UserUsageStore', back_populates='tools')
    