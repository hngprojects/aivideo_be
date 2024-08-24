import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from celery.result import AsyncResult

from api.core.dependencies.celery.celery_app import worker
from api.db.database import get_db
from api.v1.services.job import job_service
from api.v1.services.project import project_service
from api.v1.services.user import user_service
from api.v1.services.notification import notification_service

background_router = APIRouter(prefix="/jobs", tags=["Jobs"])


async def event_generator(job_id: str, db: Session, request: Request):
# async def event_generator(job_id: str, db: Session):
    '''Generates events for SSE'''

    user = None
    if not job_id:
        return 
    refresh_token = request.cookies.get('refresh_token')
    if refresh_token:
        user = user_service.get_user_from_refresh_token(refresh_token=refresh_token, db=db)

    while True:
        task_result = AsyncResult(job_id, app=worker)
        project = job_service.get_project_from_job(job_id=job_id)

        status = task_result.state
        result = None

        if project.is_active:
            project_service.update_project_status(
                db=db,
                project_id=project.id,
                result=None,
                is_active=False
            )
        
        job_service.update_job(job_id, status.capitalize())

        event_name = 'other'

        if status == 'FAILURE':
            # Safely convert task_result.info to a string
            result = str(task_result.info) if task_result.info else "Unknown error"
            event_name = 'failure'
            job_service.update_job(job_id, 'Failed', result)

            # Use json.loads on the result as it is already a stringified json
            yield f'event: {event_name}\ndata: {json.dumps({"status": status.capitalize(), "result": result})}\n\n'
            
            if user:
                # Send notification to user
                notification_service.send_notification(
                    db=db,
                    user=user,
                    title="Project Failed",
                    message=f"The project '{project.title}' has failed to create.",
                    type='warning'
                )
            break

        elif status == 'PROGRESS':
            result = task_result.result
            event_name = 'progress'
            job_service.update_job(job_id, 'Progress', json.dumps(result))

            yield f'event: {event_name}\ndata: {json.dumps({"status": status.capitalize(), "result": result})}\n\n'

        elif status == 'SUCCESS':
            result = task_result.result
            event_name = 'success'
            job_service.update_job(job_id, 'Success', result)
            
            if user:
                # Send notification to user
                notification_service.send_notification(
                    db=db,
                    user=user,
                    title="Project created",
                    message=f"The project '{project.title}' has been created successfully."
                )

            # Save project result and link project to user
            try:
                project_service.update_project_status(
                    db=db,
                    project_id=project.id,
                    result=result,
                    is_active=True,
                    user=user
                )
            except Exception as e:
                print(f"Error saving project {e}")
                db.rollback()
            finally:
                db.close()
                print('Session closed')

            yield f'event: {event_name}\ndata: {json.dumps({"status": status.capitalize(), "result": json.loads(result)})}\n\n'
            break

        yield f'event: {event_name}\ndata: {json.dumps({"status": status.capitalize(), "result": result})}\n\n'
        await asyncio.sleep(1)  # Delay between status checks


async def event_generator_for_job(job_id: str):
    '''Generates events for SSE but for jobs'''

    while True:
        task_result = AsyncResult(job_id, app=worker)
        status = task_result.state

        result = None
        job_service.update_job(job_id, status.capitalize())
        event_name = 'other'

        if status == 'FAILURE':
            # Safely convert task_result.info to a string
            result = str(
                task_result.info) if task_result.info else "Unknown error"
            event_name = 'failure'
            job_service.update_job(job_id, 'Failed', result)

            # Use json.loads on the result as it is already a stringified json
            yield f'event: {event_name}\ndata: {json.dumps({"status": status.capitalize(), "result": result})}\n\n'
            break

        elif status == 'PROGRESS':
            result = task_result.result
            event_name = 'progress'
            job_service.update_job(job_id, 'Progress', json.dumps(result))

            yield f'event: {event_name}\ndata: {json.dumps({"status": status.capitalize(), "result": result})}\n\n'
            # await asyncio.sleep(1)

        elif status == 'SUCCESS':
            result = task_result.result
            event_name = 'success'
            job_service.update_job(job_id, 'Success', result)

            yield f'event: {event_name}\ndata: {json.dumps({"status": status.capitalize(), "result": json.loads(result)})}\n\n'
            break

        yield f'event: {event_name}\ndata: {json.dumps({"status": status.capitalize(), "result": result})}\n\n'
        await asyncio.sleep(1)  # Delay between status checks


@background_router.get("/{job_id}/sse/progress")
async def send_job_status_updates_over_sse(
    job_id: str,
    request: Request,
    save_project: bool = True,
    db: Session = Depends(get_db)
):
    '''
    Function to send job status over server sent events and this updates the project associated with the job.
    Set save_project to True if a project is to be saved after job execution. If not set it to false
    '''
    if not job_id:
        raise HTTPException(status_code=400, detail="job_id is required")

    try:
        event_stream = event_generator(job_id, db, request) if save_project else event_generator_for_job(job_id)
        return StreamingResponse(event_stream, media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
