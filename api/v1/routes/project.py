import logging

from fastapi import APIRouter, Depends, HTTPException, status,Query
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from typing import Optional
from api.db.database import get_db
from api.utils.success_response import success_response
from api.v1.models.user import User
from api.v1.schemas.project import (AddFullProjectSchema,
                                    CreateFullProjectSchema,
                                    ProjectCreateResponseSchema)
from api.v1.services.project import project_service
from api.v1.services.user import user_service

project = APIRouter(prefix="/projects", tags=["Projects"])


@project.post("", response_model=success_response, status_code=201)
async def create_project(
    schema: CreateFullProjectSchema,
    db: Session = Depends(get_db),
):
    """Endpoint to create a new project"""
    full_project = AddFullProjectSchema(
        user_id="default_user_id", **schema.model_dump())

    new_project = project_service.create(db, full_project)

    logging.info(f'Creating new Project. ID: {new_project.id}.')
    return success_response(
        data=jsonable_encoder(
            ProjectCreateResponseSchema.model_validate(new_project)),
        message="Successfully created project",
        status_code=status.HTTP_201_CREATED,
    )


@project.get("", response_model=success_response, status_code=200)
async def get_all_projects(
    description : Optional[str] = Query(None),
    title : Optional[str] = Query(None),
    type : Optional[str] = Query(None),
    db: Session = Depends(get_db)
     ):
    """Endpoint to get all projects With Search Funtctionality"""

    query_params = {
        'description': description,
        'project_type': type,
        'title': title
    }

    projects = project_service.fetch_all_projects(db=db, **query_params)
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
async def get_single_project(id: str, db: Session = Depends(get_db)):
    """Endpoint to get a single project"""

    project = project_service.fetch_project_by_id(project_id=id, db=db)

    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    return success_response(
        data=jsonable_encoder(
            ProjectCreateResponseSchema.model_validate(project)),
        message="Project retrieved successfully",
        status_code=status.HTTP_200_OK,
    )


@project.put("/{id}", response_model=success_response, status_code=200)
async def save_project(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(user_service.get_current_user)
):
    """Endpoint to save a project"""
    project = project_service.fetch_project_by_id(project_id=id, db=db)

    if project.user_id is not None:
        raise HTTPException(status_code=400, detail="Project is already saved")

    project_service.add_user_to_project(db, project=project, user=current_user)

    return success_response(
        data=jsonable_encoder(
            ProjectCreateResponseSchema.model_validate(project)),
        message="Project saved successfully",
        status_code=status.HTTP_200_OK,
    )
