from typing import Any, Optional
from sqlalchemy.orm import Session
from api.core.base.services import Service
from api.v1.models.notifications import Notification
from api.v1.models.user import User


class NotificationService(Service):
    """Notification service functionality"""

    def create(self, db: Session):
        """Create a new notification"""
        pass

    def fetch(self, user: User, notification_id: str):
        """Fetches a notification by id"""

        all_notifications = user.notifications

        for notification in all_notifications:
            if notification.id == notification_id:
                return notification
        
        return None
    
    def fetch_all(self, user: User):
        """Fetch all notifications"""
        all_notifications = user.notifications

        return all_notifications

    def update(self):
        pass
    
    def delete(self):
        pass

    

notification_service = NotificationService()