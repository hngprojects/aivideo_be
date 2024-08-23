"""UsageStore data model"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from api.v1.models.base_model import BaseTableModel
from sqlalchemy.dialects.postgresql import ARRAY

class UsageStore(BaseTableModel):
    __tablename__ = "usage_store"
    
    ip_address = Column(String, index=True, nullable=False)
    tool_access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime, default=datetime.utcnow, nullable=False)
    tools_accessed = Column(ARRAY(String), nullable=True)
