from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from api.db.database import get_db
from api.v1.models.user import User
from api.v1.services.user import user_service
from api.v1.services.job_management import job_management_service
from api.v1.schemas.job_management import PaginatedResponse


job_management = APIRouter(prefix="/contents", tags=["Job Management"])


@job_management.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Get summary records",
    description="This endpoint returns a list of all the jobs that have been done on the application. Data can be filtered for specific project type.",
    response_model=PaginatedResponse,
    responses={
        403: {
            "description": "You do not have permission to access this resource",
            "content": {
                "application/json": {
                    "example": {
                        "status": False,
                        "status_code": 403,
                        "message": "You do not have permission to access this resource",
                    }
                }
            },
        }
    },
)
async def get_jobs(
    current_admin: User = Depends(user_service.get_current_super_admin),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 10,
    project_type: str = "",
    filters: dict = {},
):
    """
    Endpoint to get the list of all summarized videos

    :param db: Session Database session
    :param skip: int The number of items to skip
    :param limit: int The maximum number of items to be returned
    :param project_type: str = A filter to return a specific project type
    skip:
    """

    filters["project_type"] = project_type

    return job_management_service.fetch_all_summarized_videos(db, skip, limit, filters)
