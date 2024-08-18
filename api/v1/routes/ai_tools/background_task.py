import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from celery.result import AsyncResult

from api.core.dependencies.celery.celery_app import worker
from api.db.database import get_db
from api.utils.success_response import success_response
from api.v1.services.job import job_service

background_router = APIRouter(prefix="/jobs", tags=["Jobs"])

async def event_generator(job_id: str, db: Session):
    '''Generates events for SSE'''

    while True:
        task_result = AsyncResult(job_id, app=worker)
        project = job_service.get_project_from_job(job_id=job_id)

        status = task_result.state
        result = None

        try:
            project.is_active = False
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="Failed to update project status")
        
        job_service.update_job(job_id, status.capitalize())

        event_name = 'other'
        
        if status == 'FAILURE':
            # Safely convert task_result.info to a string
            result = str(task_result.info) if task_result.info else "Unknown error"
            event_name = 'failure'
            job_service.update_job(job_id, 'Failed', result)

            # Use json.loads on the result as it is already a stringified json
            yield f'event: {event_name}\ndata: {json.dumps({"status": status.capitalize(), "result": result})}\n\n'
            break
        
        elif status == 'SUCCESS':
            result = task_result.result
            event_name = 'success'
            job_service.update_job(job_id, 'Success', result)

            # Save project result
            try:
                project.result = result
                project.is_active = True
                db.commit()
            except Exception as e:
                db.rollback()
                raise HTTPException(status_code=500, detail="Failed to update project status")
            finally:
                db.close()

            yield f'event: {event_name}\ndata: {json.dumps({"status": status.capitalize(), "result": json.loads(result)})}\n\n'
            break
        
        yield f'event: {event_name}\ndata: {json.dumps({"status": status.capitalize(), "result": result})}\n\n'
        await asyncio.sleep(1)  # Delay between status checks


@background_router.get("/{job_id}/sse/progress")
async def send_job_status_updates_over_sse(
    job_id: str, 
    db: Session = Depends(get_db)
):
    '''Function to send job status over server sent events'''

    try:
        event_stream = event_generator(job_id, db)
        return StreamingResponse(event_stream, media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@background_router.get("/{job_id}/status")
async def send_job_status_updates(
    job_id: str, 
    db: Session = Depends(get_db)
):
    '''Function to send job status'''

    task_result = AsyncResult(job_id, app=worker)
    project = job_service.get_project_from_job(job_id=job_id)

    status = task_result.state
    result = None

    try:
        project.is_active = False
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    if status == "PENDING":
        job_service.update_job(job_id, "Pending")

    elif status == "FAILURE":
        # Safely convert task_result.info to a string
        result = str(task_result.info) if task_result.info else "Unknown error"
        job_service.update_job(job_id, "Failed", result)

    elif status == "SUCCESS":
        result = task_result.result
        job_service.update_job(job_id, "Success", result)

        try:
            # Save project result
            project.result = result
            project.is_active = True
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            db.close()
        
    else:
        job_service.update_job(job_id, status)

    return success_response(
        status_code=200,
        message="Job progress retrieved",
        data={
            'job_id': job_id,
            'status': status.capitalize(),
            'result': result
        }
    )
