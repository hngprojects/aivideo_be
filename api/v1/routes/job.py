from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from api.db.database import get_db
from api.utils.pagination import paginated_response
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
