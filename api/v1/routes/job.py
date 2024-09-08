from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from typing import List, Annotated, Optional
from api.v1.schemas.job import JobResponse
from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import event
from sse_starlette import EventSourceResponse
from api.db.database import get_db
from api.utils.success_response import success_response
from api.v1.models.job import Job, TifiJob, JobStatus
from api.v1.models.user import User
from api.v1.services.user import user_service
from api.v1.services.project import project_service
from api.v1.services.job import job_service
from api.v1.services.notification import notification_service
from api.v1.services.job import tifi_job_service
from api.core.dependencies.jobs.service import run_pending_jobs, process_job
from api.core.dependencies.celery.tasks.run_job import run_job_in_celery, run_pending_jobs_in_celery
import json
import asyncio

job_router = APIRouter(prefix="/jobs", tags=["Jobs"])


# Get all jobs
@job_router.get("", response_model=success_response, status_code=status.HTTP_200_OK)
async def get_all_jobs(
    db: Session = Depends(get_db),
    # is_expired: bool = False,
    # tool_name: Optional[str] = None,
):
    """Fetch all jobs from the database."""

    # jobs = job_service.fetch_all_jobs(db=db)
    jobs = tifi_job_service.fetch_all(
        db=db, 
        # is_expired=is_expired, 
        # tool_name=tool_name
    )

    return success_response(
        status_code=200,
        message='Jobs fetched successfully',
        data=jsonable_encoder(jobs)
    )


@job_router.get("/process-jobs-synchronous", response_model=success_response, status_code=status.HTTP_200_OK)
async def process_jobs_synchronous(db: Session = Depends(get_db)):
    """This endpoint processes all pending jobs synchronously"""

    run_pending_jobs()

    return success_response(
        status_code=200,
        message='All pending jobs processed successfully',
    )


@job_router.get("/process-jobs-async", response_model=success_response, status_code=status.HTTP_200_OK)
async def process_jobs_asynchronous(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """This endpoint processes all pending jobs asynchronously"""

    # background_tasks.add_task(run_pending_jobs)
    # run_pending_jobs_in_celery.delay()

    jobs = tifi_job_service.fetch_all_pending(db=db)
    for job in jobs:
        run_job_in_celery.delay(job_id=job.id)

    return success_response(
        status_code=200,
        message='Pending jobs executing in the background',
    )


@job_router.get("/{job_id}", response_model=success_response, status_code=status.HTTP_200_OK)
async def get_single_job(job_id: str, db: Session = Depends(get_db)):
    """Fetch a single job from the database."""

    job = tifi_job_service.fetch(db=db, job_id=job_id)

    return success_response(
        status_code=200,
        message='Job fetched successfully',
        data=jsonable_encoder(job)
    )


@job_router.get("/{job_id}/process", response_model=success_response, status_code=status.HTTP_200_OK)
async def process_and_execute_job(background_tasks: BackgroundTasks, job_id: str, db: Session = Depends(get_db)):
    """Processes and executes a single job from the database as long as it is pending or failed.
    This is done in the background.
    """

    job = tifi_job_service.fetch(db=db, job_id=job_id)

    if job.is_expired():
        raise HTTPException(status_code=400, detail="Job has expired")
    
    # Check if job state is valid
    if job.status not in [JobStatus.pending, JobStatus.failed]:
        raise HTTPException(status_code=400, detail="Job is not in pending or failed state")

    # background_tasks.add_task(process_job,job_id=job_id)

    # Run job in celery
    run_job_in_celery.delay(job_id)

    return success_response(
        status_code=200,
        message='Job processing started in the background',
    )


# ------------------------ SSE ------------------------

async def job_process_event_generator(
    job_id: str, 
    user: Optional[User] = None,
    save_project = True  # Set to true if a project is to be saved after completion
):
    '''Generates events for job processing'''

    while True:
        # Open new session each iteration to get updates data
        db = next(get_db())

        try:
            job = tifi_job_service.fetch(db=db, job_id=job_id)
            project = project_service.fetch(db=db, project_id=job.project_id)

            status = job.status
            progress = job.progress
            result = job.result

            event_name = 'other'

            if status == JobStatus.failed:
                event_name = 'failure'
                yield f'event: {event_name}\ndata: {json.dumps({"status": status.capitalize(), "result": result, "progress": progress})}\n\n'
                
                if user and save_project:
                    # Send notification to user
                    notification_service.send_notification(
                        db=db,
                        user=user,
                        title="Project creation failed",
                        message=f"The project '{project.title}' has failed to create.",
                        type='warning'
                    )

                break

            elif status == JobStatus.progress:
                event_name = 'progress'
                yield f'event: {event_name}\ndata: {json.dumps({"status": status.capitalize(), "result": result, "progress": progress})}\n\n'

            elif status == JobStatus.completed:
                event_name = 'success'
                yield f'event: {event_name}\ndata: {json.dumps({"status": status.capitalize(), "result": result, "progress": progress})}\n\n'
                
                if user and save_project:
                    # Send notification to user
                    notification_service.send_notification(
                        db=db,
                        user=user,
                        title="Project created",
                        message=f"The project '{project.title}' has been created successfully."
                    )

                break
        
        finally:
            db.close()

        await asyncio.sleep(15)  # Delay between status checks


@job_router.get("/{job_id}/sse/progress")
async def send_job_status_updates_over_sse(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(user_service.get_current_user_optional),
    save_project: bool = True  # Set to True if a project is to be saved after job execution. If not set it to False
):
    '''
    Function to send job status over server sent events and this updates the project associated with the job.
    Set save_project to True if a project is to be saved after job execution. If not set it to false
    '''

    try:
        event_stream = job_process_event_generator(
            job_id=job_id, 
            user=current_user,
            save_project=save_project
        )
        return StreamingResponse(event_stream, media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------

@job_router.get("/activity")
async def get_managed_jobs(
    current_admin: User = Depends(user_service.get_current_super_admin),
    db: Session = Depends(get_db),
    page: int = 1,
    per_page: int = 10,
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
        page=page,
        per_page=per_page,
        search=search,
        status=status,
        project_type=project_type,
    )


@job_router.get("/export")
async def export_jobs_as_csv(
    db: Session = Depends(get_db),
    current_admin: User = Depends(user_service.get_current_super_admin),
):
    csv_file = job_service.export_jobs_as_csv(db)

    response = StreamingResponse(csv_file, media_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename=job-data.csv"
    response.status_code = 200

    return response


@job_router.get("/activity/sse", summary="Get job activity via SSE")
async def get_sse_job_activity(db: Session = Depends(get_db)):
    """
    Retrieve a server-sent event stream for job activity updates.
    """

    return StreamingResponse(
        job_service.stream_job_activity(db=db),
        media_type="text/event-stream",
    )


@job_router.get("/statistics/sse", summary="Get job statistics via SSE")
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


@job_router.get("/recent-activity", status_code=status.HTTP_200_OK)
def get_user_statistics(db: Annotated[Session, Depends(get_db)]):
    """Endpoint to fetch all user statistics"""

    return EventSourceResponse(event_generator(db))

#########################################


