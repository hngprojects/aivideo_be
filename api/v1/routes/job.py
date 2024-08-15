from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from api.db.database import get_db
from api.utils.pagination import paginated_response
from api.utils.success_response import success_response
from api.v1.models.job import Job
from api.v1.models.user import User
from api.v1.services.user import user_service
from api.v1.services.job import job_service

job = APIRouter(prefix="/jobs", tags=["Jobs"])


@job.get("/activity")
async def get_managed_jobs(
    current_admin: User = Depends(user_service.get_current_super_admin),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 30,
    filters: dict = {},
):
    return job_service.fetch_job_activity(
        db=db, skip=skip, limit=limit, filters=filters
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


@job.get(
    "/statistics",
    summary="Get job statistics",
    description="Get stats to be rendered on the admin dashboard for job management",
)
async def get_job_statistics(
    db: Session = Depends(get_db),
    current_admin: User = Depends(user_service.get_current_super_admin),
):
    """
    :param db: Session database session object
    :param current_admin: Super admin user
    :returns success_response {
      "status_code": 200,
      "success": true,
      "message": "Job statistics retrieved successfully",
      "data": {
        "total_tasks": 2,
        "failed_tasks": 1,
        "in_progress_tasks": 0,
        "pending_tasks": 0,
        "completed_tasks": 1
      }
    }
    """

    stats = job_service.get_job_statistics(db)

    return success_response(
        message="Job statistics retrieved successfully", data=stats, status_code=200
    )
