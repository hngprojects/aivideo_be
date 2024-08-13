from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from api.db.database import get_db
from api.v1.models.user import User
from api.v1.services.user import user_service
from api.v1.services.job_management import job_management_service
from api.utils.pagination import paginated_response


job_management = APIRouter(prefix="/contents", tags=["Content Management"])


@job_management.get("/video", status_code=status.HTTP_200_OK)
async def get_summarized_videos(
    current_admin: User = Depends(user_service.get_current_super_admin),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 10,
    project_type: str = "",
    filters: dict = {},
):
    """
    Endpoint to get the list of all summarized videos
    """

    filters["project_type"] = project_type

    return job_management_service.fetch_all_summarized_videos(db, skip, limit, filters)
