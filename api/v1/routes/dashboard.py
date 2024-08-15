from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.success_response import success_response
from api.v1.models.user import User
from api.v1.services.user import user_service
from api.v1.services.notification import notification_service
from api.v1.schemas.notification import RetrieveNotificationSchema

dashboard = APIRouter(prefix="/dashboard", tags=["Dashboard"])



@dashboard.get("/notifications", response_model=success_response, status_code=200)
async def get_all_notifications(db: Session = Depends(get_db),
                                current_user: User = Depends(user_service.get_current_user)):
    """Endpoint to get all projects"""
    
    notifications = notification_service.fetch_all(current_user)
    notifications_filtered = list(
        map(lambda x: RetrieveNotificationSchema.model_validate(x), notifications)
    )
    if len(notifications_filtered) == 0:
        notifications_filtered = None

    return success_response(
        status_code=200,
        message="Notifications retrieved successfully",
        data=jsonable_encoder(notifications_filtered),
    )

@dashboard.get("/notifications/{id}", response_model=success_response, status_code=200)
async def get_single_notification(id: str, db: Session = Depends(get_db),
                                  current_user: User = Depends(user_service.get_current_user)):

    """Endpoint to get a single notification"""

    notification = notification_service.fetch(current_user, notification_id=id)

    if notification == None:
        raise HTTPException(status_code=404, detail="Notification not found")

    return success_response(
        data=jsonable_encoder(RetrieveNotificationSchema.model_validate(notification)),
        message="Notification retrieved successfully",
        status_code=status.HTTP_200_OK,
    )
