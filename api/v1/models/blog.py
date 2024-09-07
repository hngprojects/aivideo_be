#!/usr/bin/env python3
"""The Blog Post Model."""

from sqlalchemy import Column, String, Text, ForeignKey, Boolean, text
from sqlalchemy.orm import relationship
from api.v1.models.base_model import BaseTableModel


class Blog(BaseTableModel):
    __tablename__ = "blogs"

    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    image_url = Column(String, nullable=True)
    cover_image_url = Column(String)
    is_deleted = Column(Boolean, default=False)
    category = Column(String, nullable=False)