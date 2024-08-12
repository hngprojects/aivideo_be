""" User data model
"""

from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
from api.v1.models.base_model import BaseTableModel


class User(BaseTableModel):
    __tablename__ = "users"

    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=True)
    first_name = Column(String)
    last_name = Column(String)
    avatar_url = Column(String)
    is_active = Column(Boolean, server_default='true')
    is_superadmin = Column(Boolean, server_default='false')
    is_deleted = Column(Boolean, server_default='false')

    profile = relationship('Profile', back_populates='user', uselist=False)
    notifications = relationship('Notification', back_populates='user')
    activity_logs = relationship('ActivityLog', back_populates='user')
    subscriptions = relationship('UserSubscription', back_populates='user')
    payments = relationship("Payment", back_populates="user")
    projects = relationship('Project', back_populates='user')
    reviews = relationship('Review', back_populates='user')
    notification_setting = relationship("NotificationSetting", back_populates="user")
    data_privacy_setting = relationship("DataPrivacySetting", back_populates="user")
    lang_reg_timezone_settings = relationship("LanguageRegionTimezoneSetting", back_populates="user")
    blogs = relationship("Blog", back_populates="author", cascade="all, delete-orphan")

    def to_dict(self):
        obj_dict = super().to_dict()
        obj_dict.pop("password")
        return obj_dict

    def __str__(self):
        return self.email
