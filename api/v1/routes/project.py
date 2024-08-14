from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from api.db.database import get_db
from api.v1.services.project import project_service
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

project = APIRouter(prefix="/projects", tags=["Projects"])


@project.post("", response_model=success_response, status_code=201)
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
    full_project = AddFullProjectSchema(user_id=current_user.id, **schema.model_dump())
    
    new_project = project_service.create(db, full_project)

    
    logging.info(f'Creating new Project. ID: {new_project.id}.')
    return success_response(
        data=jsonable_encoder(ProjectCreateResponseSchema.model_validate(new_project)),
        message="Successfully created project",
        status_code=status.HTTP_201_CREATED,
    )

@project.get("", response_model=success_response, status_code=200)
async def get_all_projects(db: Session = Depends(get_db),
                           current_user: User = Depends(user_service.get_current_user),
                           ):
    """Endpoint to get all projects

    Args:
        db (Session, optional): The db session object. Defaults to Depends(get_db).
        current_user: The signed-in user
    """    
    
    projects = project_service.fetch_all_user_projects(current_user)
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

@project.get("/{id}", response_model=success_response, status_code=200)
async def get_single_project(id: str, db: Session = Depends(get_db),
                             current_user: User = Depends(user_service.get_current_user),):
    """Endpoint to get a single project

    Args:
        id (str): project ID
        db (Session, optional): Defaults to Depends(get_db).

    Raises:
        HTTPException: 404 NOT FOUND (project to be retrieved cannot be found)
    """
    project = project_service.fetch_user_project(current_user, project_id=id)

    if project == None:
        raise HTTPException(status_code=404, detail="Project not found")

    return success_response(
        data=jsonable_encoder(ProjectCreateResponseSchema.model_validate(project)),
        message="Project retrieved successfully",
        status_code=status.HTTP_200_OK,
    )
