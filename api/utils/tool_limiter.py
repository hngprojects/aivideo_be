from datetime import datetime, timedelta

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.client_helpers import get_ip_address
from api.v1.models.usage_store import UsageStore
from api.v1.services.user import user_service
from api.v1.models.user import User

ACCESS_LIMIT = 3
TIME_WINDOW = timedelta(days=1)


# Middleware to track and enforce access limits
def track_tool_usage(
    current_tool: 'str',
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(user_service.get_current_user_optional),
):
    if user:
        return user
    
    client_ip = get_ip_address(request)
    now = datetime.utcnow()

    # Retrieve user tracking record by IP
    tracking_record = db.query(UsageStore).filter_by(ip_address=client_ip).first()
    if tracking_record:
        tracking_record.last_accessed = now
        tracking_record.tool_access_count += 1


        if tracking_record.tools_accessed.count(current_tool) == ACCESS_LIMIT:
            raise HTTPException(
                status_code=429,
                detail="Too many requests, please log in to continue using this tool.",
            )
        else:
            tracking_record.tools_accessed = tracking_record.tools_accessed + [current_tool]                

    else:
        # Create a new record for the IP
        tracking_record = UsageStore(
            ip_address=client_ip,
            tool_access_count=1,
            last_accessed=now,
            tools_accessed=[current_tool]
        )

        db.add(tracking_record)

    db.commit()
    return None
   
class TrackToolUsage:
    """Class based dependency to allow passing current_tool parameter to dependencies
    """
    def __init__(self, current_tool: str):
        self.current_tool = current_tool
    
    def __call__(self, req: Request, db: Session = Depends(get_db),
                 user=Depends(user_service.get_current_user_optional)):
        user = track_tool_usage(self.current_tool, request=req, db=db, user=user)
        return user