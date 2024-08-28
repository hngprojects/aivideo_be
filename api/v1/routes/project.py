import logging

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from typing import Optional
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy import event
from sse_starlette import EventSourceResponse
import asyncio

from api.db.database import get_db
from api.utils.success_response import success_response
from api.v1.models.user import User
from api.v1.models.project import Project
from api.v1.schemas.project import (
    AddFullProjectSchema,
    CreateFullProjectSchema,
    ProjectCreateResponseSchema,
    SaveProjectSchema,
    ToolStatsResponse,
)
from api.v1.services.project import project_service
from api.v1.services.user import user_service

project_router = APIRouter(prefix="/projects", tags=["Projects"])


@project_router.post("", response_model=success_response, status_code=201)
async def create_project(
    schema: CreateFullProjectSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(user_service.get_current_user),
):
    """Endpoint to create a new project"""

    schema_dump = schema.model_dump()
    schema_dump.pop('user_id')

    full_project = AddFullProjectSchema(
        user_id=current_user.id,
        **schema_dump
    )

    new_project = project_service.create(db, full_project)

    logging.info(f"Creating new Project. ID: {new_project.id}.")
    return success_response(
        data=jsonable_encoder(new_project),
        message="Successfully created project",
        status_code=status.HTTP_201_CREATED,
    )


@project_router.get("", response_model=success_response, status_code=200)
async def get_all_projects(
    description: Optional[str] = Query(None),
    title: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Endpoint to get all projects With Search Funtctionality"""

    query_params = {"description": description, "project_type": type, "title": title}

    projects = project_service.fetch_all_projects(db=db, **query_params)

    return success_response(
        status_code=200,
        message="Projects retrieved successfully",
        data=jsonable_encoder(projects),
    )


@project_router.get("/user", response_model=success_response, status_code=200)
async def get_user_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(user_service.get_current_user),
):
    """Endpoint to get all projects of the current logged in user"""

    projects = project_service.fetch_all_user_projects(db=db, user=current_user)

    return success_response(
        data=jsonable_encoder(projects),
        message="Projects retrieved successfully",
        status_code=status.HTTP_200_OK,
    )


@project_router.get("/user/archive", response_model=success_response, status_code=200)
async def get_user_archived_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(user_service.get_current_user),
):
    """Endpoint to get all projects of the current logged in user"""

    projects = project_service.fetch_all_user_archived_projects(
        db=db, user=current_user
    )

    return success_response(
        data=jsonable_encoder(projects),
        message="Projects retrieved successfully",
        status_code=status.HTTP_200_OK,
    )


################ SSE ENDPOINT FOR TOOL USAGE STATISTICS ###################

# total number of connected clients
connections = 0
# {"connection": ["state", "active_status"]}
state_map = {}


def reset_connection_active_status():
    """reset the active status for each open connection tracked by the state_map"""
    if state_map:
        for key, value in state_map.items():
            state_map[key][1] = 0


def remove_inactive_connections():
    """remove all inactive connections from the state_map"""
    connections_to_remove = []
    if state_map:
        for key, value in state_map.items():
            if state_map[key][1] == 0:
                connections_to_remove.append(key)
        for connection in connections_to_remove:
            del state_map[connection]


@event.listens_for(Project, "after_insert")
@event.listens_for(Project, "after_update")
def orm_event_listener(mapper, connection, target):
    """listen for db updates and update the state_map"""

    # once a change in the db is detected
    # clear all inactive connections from state_map
    # fill each connection in the state_map with [1, 1]
    # [update_state, active_state]

    remove_inactive_connections()

    if state_map:
        for key, value in state_map.items():
            state_map[key] = [1, 1]


async def event_generator(request: Request, db: Session):
    global connections, state_map
    connection_index = connections
    connections += 1
    map_key = f"connection_{connection_index}"

    reset_connection_active_status()

    # initialize current connection state
    state_map[map_key] = [1, 1]

    while True:
        # mark the current connection as active
        try:
            state_map[map_key][1] = 1
        except KeyError:
            # if connection is already deleted
            break
        # check if state map is non empty
        if state_map[map_key][0] == 1:
            # send a message if update_state is 1
            data = project_service.fetch_statistics(db).model_dump_json()

            # reset current connection update_state to 0
            state_map[map_key][0] = 0

            yield {"event": "toolUsageStatisticsUpdate", "data": data}
        await asyncio.sleep(1)


@project_router.get("/statistics", response_model=ToolStatsResponse, status_code=200)
def get_statistics(request: Request, db: Session = Depends(get_db)):
    """Endpoint to get tool usage data"""

    return EventSourceResponse(event_generator(request, db))


@project_router.get("/{id}", response_model=success_response, status_code=200)
async def get_single_project(id: str, db: Session = Depends(get_db)):
    """Endpoint to get a single project"""

    project = project_service.fetch_project_by_id(project_id=id, db=db)

    return success_response(
        data=jsonable_encoder(project),
        message="Project retrieved successfully",
        status_code=status.HTTP_200_OK,
    )


@project_router.put("/{id}/save", response_model=success_response, status_code=200)
async def save_project(
    id: str,
    schema: SaveProjectSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(user_service.get_current_user),
):
    """Endpoint to save a project"""

    project = project_service.fetch_project_by_id(project_id=id, db=db)

    if project.user_id is not None:
        raise HTTPException(status_code=400, detail="Project is already saved")

    project_service.save_project(
        db, 
        project=project, 
        user=current_user,
        project_result=schema.result
    )

    return success_response(
        data=jsonable_encoder(project),
        message="Project saved successfully",
        status_code=status.HTTP_200_OK,
    )
