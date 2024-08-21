from fastapi import Depends, APIRouter, status, Query
from sqlalchemy.orm import Session
from typing import Annotated


from api.v1.models import User
from api.db.database import get_db
from api.v1.services.user import user_service
from api.utils.success_response import success_response
from api.v1.schemas.user_subscription import UserSubscriptionListResponse
from api.v1.services.user_subscription import user_subscription_service as user_sub_service


user_subs = APIRouter(prefix="/user-subscriptions", tags=["User Subscription"])


@user_subs.get("", status_code=status.HTTP_200_OK, response_model=UserSubscriptionListResponse)
def get_all_user_subscriptions(
    _: User = Depends(user_service.get_current_super_admin),
    limit: Annotated[int, Query(ge=1, description="Number of user subscriptions per page")] = 10,
    page: Annotated[int, Query(ge=1, description="Page number (starts from 1)")] = 1,
    db: Session = Depends(get_db),
):
    """
    Endpoint to retrieve a paginated list of all user subscriptions by ``superadmin``. \n

    Query parameter:
        - limit: Number of user subscriptions per page (default: 10, minimum: 1)
        - page: Page number (starts from 1)
    """
    # get offset from page and limit
    offset = (page - 1) * limit

    # fetch all user subscriptions
    user_subs_l = user_sub_service.fetch_all(
        db, offset=offset, limit=limit,
    )

    data = user_sub_service.dictize_user_subscriptions_and_pagination(
        user_subs_l, offset, limit)

    # return success and data
    return success_response(
        status_code=status.HTTP_200_OK,
        message="User subscriptions fetched successfully",
        data=data
    )
