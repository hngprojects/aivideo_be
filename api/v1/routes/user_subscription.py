from fastapi import Depends, APIRouter, status, Query
from sqlalchemy.orm import Session
from typing import Annotated


from api.v1.models import User
from api.db.database import get_db
from api.v1.services.user import user_service
from api.utils.success_response import success_response
from api.v1.schemas.user_subscription import UserSubscriptionListResponse, ViewUserSubReturnData
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


@user_subs.get("/{subscription_id}", 
              status_code=status.HTTP_200_OK, response_model=ViewUserSubReturnData)
def get_single_user_subscription(
    subscription_id: str,
    current_user: User = Depends(user_service.get_current_user),
    db: Session = Depends(get_db),
):
    """
    Endpoint to retrieve a single user subscription detail by
    ``superadmin`` OR ``user who owns the subscription``.
    """
    # get the user sub object
    user_sub = user_sub_service.fetch(db, subscription_id)

    # check that current user is superadmin OR owns the subscription 
    user_service.check_superadmin_or_user_in_object(current_user, user_sub)

    # return success and data
    return success_response(
        status_code=status.HTTP_200_OK,
        message="User subscription fetched successfully",
        data=user_sub_service.dynamic_user_subscription_dict(user_sub)
    )
