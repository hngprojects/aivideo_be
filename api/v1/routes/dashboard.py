from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.success_response import success_response
from api.v1.models.user import User
from api.v1.services.user import user_service
from api.v1.services.project import project_service
from api.v1.schemas.project import CreateFullProjectSchema, AddFullProjectSchema, ProjectCreateResponseSchema
import logging
from api.v1.services.notification import notification_service
from api.v1.schemas.notification import RetrieveNotificationSchema
from typing import Optional

dashboard = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@dashboard.post("/projects", response_model=success_response, status_code=201)
async def create_project(
    schema: CreateFullProjectSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(user_service.get_current_user),
):
    """Endpoint to create a new projects. Only accessible to authenticated users
    Args:
        schema (CreateFullProjectSchema): Request Body for creating projects
        db (Session, optional): The db session object. Defaults to Depends(get_db).
        current_user (User, optional): User. Defaults to Depends(user_service.get_current_user).
    Returns:
        success_response
    """
    full_project = AddFullProjectSchema(**schema.model_dump())
    
    new_project = project_service.create(db, full_project)

    
    logging.info(f'Creating new Project. ID: {new_project.id}.')
    return success_response(
        data=jsonable_encoder(ProjectCreateResponseSchema.model_validate(new_project)),
        message="Successfully created project",
        status_code=status.HTTP_201_CREATED,
    )

@dashboard.get("/projects", response_model=success_response, status_code=200)
async def get_all_projects(keywords: Optional[str] = None,
                           db: Session = Depends(get_db),
                           current_user: User = Depends(user_service.get_current_user),
                           ):
    """Endpoint to get [all] projects

    Args:
        keywords: Optional query parameter to search through projects before retrieval
        db (Session, optional): The db session object. Defaults to Depends(get_db).
        current_user: The signed-in user
    """

    if keywords is None:
        projects = project_service.fetch_all_user_projects(current_user, db)
    else:
        projects = project_service.fetch_user_projects_by_keywords(db, current_user, keywords)

    
    projects_filtered = list(
        map(lambda x: ProjectCreateResponseSchema.model_validate(x), projects)
    )
    if len(projects_filtered) == 0:
        projects_filtered = None

    return success_response(
        status_code=200,
        message="Projects retrieved successfully",
        data=jsonable_encoder(projects_filtered),
    )

@dashboard.get("/projects/{project_id}", response_model=success_response, status_code=200)
async def get_single_project(project_id: str, db: Session = Depends(get_db),
                             current_user: User = Depends(user_service.get_current_user),):
    """Endpoint to get a single project

    Args:
        id (str): project ID
        db (Session, optional): Defaults to Depends(get_db).

    Raises:
        HTTPException: 404 NOT FOUND (project to be retrieved cannot be found)
    """
    project = project_service.fetch_user_project(current_user, project_id=project_id)

    if project == None:
        raise HTTPException(status_code=404, detail="Project not found")

    return success_response(
        data=jsonable_encoder(ProjectCreateResponseSchema.model_validate(project)),
        message="Project retrieved successfully",
        status_code=status.HTTP_200_OK,
    )

@dashboard.get("/notifications", response_model=success_response, status_code=200)
async def get_all_notifications(db: Session = Depends(get_db),
                                current_user: User = Depends(user_service.get_current_user)):
    """Endpoint to get all projects"""
    
    notifications = notification_service.fetch_all_user_notifications(current_user)
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

    notification = notification_service.fetch(db, current_user, notification_id=id)

    if notification == None:
        raise HTTPException(status_code=404, detail="Notification not found")

    return success_response(
        data=jsonable_encoder(RetrieveNotificationSchema.model_validate(notification)),
        message="Notification retrieved successfully",
        status_code=status.HTTP_200_OK,
    )
