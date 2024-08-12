#!/usr/bin/env python3
"""The Blog Post Model."""

from sqlalchemy import Column, String, Text, ForeignKey, Boolean, text
from sqlalchemy.orm import relationship
from api.v1.models.base_model import BaseTableModel


class Blog(BaseTableModel):
    __tablename__ = "blogs"

    author_id = Column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title = Column(String, index=True)
    subtitle = Column(String, index=True)
    content = Column(String, nullable=False, comment="has to be a markdown")
    is_deleted = Column(Boolean, server_default=text("false"))
    thumbnail_url = Column(String) 
    excerpt = Column(Text, nullable=True)
    tags = Column(
        Text, nullable=True
    )

    author = relationship("User", back_populates="blogs")