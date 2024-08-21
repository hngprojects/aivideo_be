import logging

from fastapi import APIRouter, Depends, HTTPException, status, Request
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
    ToolStatsResponse,
)
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
        user_id="default_user_id", **schema.model_dump()
    )

    new_project = project_service.create(db, full_project)

    logging.info(f"Creating new Project. ID: {new_project.id}.")
    return success_response(
        data=jsonable_encoder(ProjectCreateResponseSchema.model_validate(new_project)),
        message="Successfully created project",
        status_code=status.HTTP_201_CREATED,
    )


@project.get("", response_model=success_response, status_code=200)
async def get_all_projects(db: Session = Depends(get_db)):
    """Endpoint to get all projects"""

    projects = project_service.fetch_all_projects(db=db)
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

# total number of connected clients
connections = 0
# {"connection": "state"}
state_map = {}

@event.listens_for(Project, "after_insert")
@event.listens_for(Project, "after_update")
def orm_event_listener(mapper, connection, target):
    # once a change in the db is detected
    # fill each connection in the state_map with 1
    for i in range(connections):
        state_map[f"connection_{i}"] = 1

    # - state -> 1 when there is an update
    # - state -> 0 when there is no update


async def event_generator(request: Request, db: Session):
    global connections, state_map
    connection_index = connections
    connections += 1
    map_key = f"connection_{connection_index}"

    # initialize current connection state
    state_map[map_key] = 1

    while True:
        # close connection is client disconnects
        if await request.is_disconnected():
            print(f"client {request.client.host} disconnected")
            connections -= 1
            del state_map[map_key]
            break

        # check if state map is non empty
        if state_map:
            if state_map[map_key] == 1:
                # send a message if state is 1
                data = project_service.fetch_statistics(db).model_dump_json()

                # reset current connection state to 0
                state_map[map_key] = 0

                yield {"event": "toolUsageStatisticsUpdate", "data": data}
        await asyncio.sleep(1)


@project.get("/statistics", response_model=ToolStatsResponse, status_code=200)
def get_statistics(request: Request, db: Session = Depends(get_db)):
    """Endpoint to get tool usage data"""

    return EventSourceResponse(event_generator(request, db))


@project.get("/{id}", response_model=success_response, status_code=200)
async def get_single_project(id: str, db: Session = Depends(get_db)):
    """Endpoint to get a single project"""

    project = project_service.fetch_project_by_id(project_id=id, db=db)

    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    return success_response(
        data=jsonable_encoder(ProjectCreateResponseSchema.model_validate(project)),
        message="Project retrieved successfully",
        status_code=status.HTTP_200_OK,
    )


@project.put("/{id}", response_model=success_response, status_code=200)
async def save_project(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(user_service.get_current_user),
):
    """Endpoint to save a project"""
    project = project_service.fetch_project_by_id(project_id=id, db=db)

    if project.user_id is not None:
        raise HTTPException(status_code=400, detail="Project is already saved")

    project_service.add_user_to_project(db, project=project, user=current_user)

    return success_response(
        data=jsonable_encoder(ProjectCreateResponseSchema.model_validate(project)),
        message="Project saved successfully",
        status_code=status.HTTP_200_OK,
    )
