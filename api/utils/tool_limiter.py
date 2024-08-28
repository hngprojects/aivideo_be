from typing import Callable
from fastapi import Request, HTTPException, Depends
from sqlalchemy.orm import Session
from functools import wraps
from datetime import timedelta

from api.db.database import get_db
from api.utils.client_helpers import get_ip_address
from api.v1.models.usage_store import UsageStore
from api.v1.services.user import user_service
from api.v1.services.usage import usage_store_service
from api.v1.services.user_usage import user_usage_store_service
from api.v1.models.user import User

ACCESS_LIMIT = 3
TIME_WINDOW = timedelta(days=1)


# Usage
# add decorator on top of function not route
# @track_tool_usage(current_tool="example_tool")
# then add these arguments into the route function
# request: Request,
# db: Session = Depends(get_db),
# user: User = Depends(user_service.get_current_user_optional)


def track_tool_usage(current_tool: str):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get('request')
            db: Session = kwargs.get('db', Depends(get_db))
            user: User | None = kwargs.get('user', Depends(user_service.get_current_user_optional))
            print(user)
            if user:
                tracking_record = user_usage_store_service.fetch_by_user(db, user.id)
                if tracking_record:
                    tracking_record.tool_access_count += 1
                    tool_count = user_usage_store_service.get_or_create_tool_value(
                        db,
                        tracking_record.id,
                        current_tool
                    )
                    if tool_count > 20:
                        raise HTTPException(
                            status_code=429,
                            detail="Please upgrade your plan to get more access",
                        )
                    else:
                        user_usage_store_service.update_tool_usage(
                            db,
                            tracking_record.id,
                            current_tool,
                            tool_count + 1
                        )
                else:
                    tracking_record = user_usage_store_service.create_usage_store_and_assign_tool(
                        db,
                        get_ip_address(request),
                        current_tool,
                        1,
                        1
                    )
                return await func(*args, **kwargs)

            client_ip = get_ip_address(request)
            tracking_record = db.query(UsageStore).filter_by(ip_address=client_ip).first()
            if tracking_record:
                tracking_record.tool_access_count += 1
                if tracking_record.tools_accessed.count(current_tool) == ACCESS_LIMIT:
                    raise HTTPException(
                        status_code=429,
                        detail="Too many requests, please log in to continue using this tool.",
                    )
                else:
                    usage_store_service.create_usage_store_and_assign_tool(
                        db,
                        client_ip,
                        current_tool,
                        1,
                        1
                    )
            else:
                usage_store_service.create_usage_store_and_assign_tool(
                    db,
                    client_ip,
                    current_tool,
                    1,
                    1
                )

            return await func(*args, **kwargs)

        return wrapper
    return decorator
