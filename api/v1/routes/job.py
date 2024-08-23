from fastapi import APIRouter, Depends, status, BackgroundTasks
from typing import List, Annotated
from api.v1.schemas.job import JobResponse
from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import event
from sse_starlette import EventSourceResponse
from api.db.database import get_db
from api.utils.pagination import paginated_response
from api.utils.success_response import success_response
from api.v1.models.job import Job
from api.v1.models.user import User
from api.v1.services.user import user_service
from api.v1.services.job import job_service
import json
import asyncio

job = APIRouter(prefix="/jobs", tags=["Jobs"])


# Get all jobs
@job.get("/", response_model=List[JobResponse], status_code=status.HTTP_200_OK)
async def get_all_jobs():
    """Fetch all jobs from the database."""
    jobs = job_service.fetch_all_jobs()
    return jobs


@job.get("/activity")
async def get_managed_jobs(
    current_admin: User = Depends(user_service.get_current_super_admin),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 30,
    search: str = "",
    status: str = "",
    project_type: str = "",
):
    """
    Retrieve a list of jobs with related project and user data, filtered by various criteria and paginated.

    Args:
        :oaram current_admin (User): The currently logged in admin user
        :param db (Session): The SQLAlchemy database session used for querying the database.
        :param skip (int): The number of records to skip (used for pagination).
        :param limit (int): The maximum number of records to return (used for pagination).
        :param search (str, optional): A string used to search for jobs based on job ID, user's first name, or user's last name. Defaults to an empty string.
        :param status (Optional[List[str]], optional): A list of job statuses to filter the results. Jobs will be included if their status matches any item in this list. Defaults to None, which means no status filter is applied.
        :param project_type (Optional[List[str]], optional): A list of project types to filter the results. Jobs will be included if their associated project's type matches any item in this list. Defaults to None, which means no project type filter is applied.

    Returns:
        dict: A dictionary containing the paginated list of jobs and related data, along with pagination metadata.
            - status_code (int): The HTTP status code for the operation (always 200 for successful fetch).
            - message (str): A message indicating the success of the operation.
            - data (dict): A dictionary containing the returned data.

    Raises:
        None: This function does not raise any exceptions directly but may propagate exceptions from the database query or data processing if errors occur.
    """

    status = [value.strip() for value in status.split(",")]
    project_type = [value.strip() for value in project_type.split(",")]

    return job_service.fetch_job_activity(
        db=db,
        skip=skip,
        limit=limit,
        search=search,
        status=status,
        project_type=project_type,
    )


@job.get("/export")
async def export_jobs_as_csv(
    db: Session = Depends(get_db),
    current_admin: User = Depends(user_service.get_current_super_admin),
):
    csv_file = job_service.export_jobs_as_csv(db)

    response = StreamingResponse(csv_file, media_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename=job-data.csv"
    response.status_code = 200

    return response


@job.get("/activity/sse", summary="Get job activity via SSE")
async def get_sse_job_activity(db: Session = Depends(get_db)):
    """
    Retrieve a server-sent event stream for job activity updates.
    """

    return StreamingResponse(
        job_service.stream_job_activity(db=db),
        media_type="text/event-stream",
    )


@job.get("/statistics/sse", summary="Get job statistics via SSE")
async def get_sse_job_statistics(db: Session = Depends(get_db)):
    """
    Retrieve a server-sent event stream for job statistics updates.
    """

    return StreamingResponse(
        job_service.stream_job_statistics(db=db),
        media_type="text/event-stream",
    )

################ SSE ENDPOINT FOR USER STATISTICS ###################

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


@event.listens_for(Job, "after_insert")
@event.listens_for(Job, "after_update")
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


async def event_generator(db: Session):
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
            data = json.dumps(jsonable_encoder(job_service.fetch_recent_job_activity(db)))

            # reset current connection update_state to 0
            state_map[map_key][0] = 0

            yield {"event": "recentActivityUpdate", "data": data}
        await asyncio.sleep(1)


@job.get(
    "/recent-activity", status_code=status.HTTP_200_OK
)
def get_user_statistics(
    db: Annotated[Session, Depends(get_db)],
):
    """Endpoint to fetch all user statistics"""
    return EventSourceResponse(event_generator(db))

#########################################


