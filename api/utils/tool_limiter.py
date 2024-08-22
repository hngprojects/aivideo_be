from datetime import datetime, timedelta

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.client_helpers import get_ip_address
from api.v1.models.usage_store import UsageStore
from api.v1.services.user import user_service

ACCESS_LIMIT = 15
TIME_WINDOW = timedelta(days=1)


# Middleware to track and enforce access limits
async def track_tool_usage(
    request: Request,
    db: Session = Depends(get_db),
    authorization: str = Header(None),
):
    # Check if user is logged in
    if request.cookies.get("refresh_token"):
        aut = authorization.split()[1] if authorization else None
        # if user is logged in logout user
        if aut and user_service.get_current_user_optional(aut, db):
            return

    client_ip = get_ip_address(request)
    now = datetime.utcnow()

    # Retrieve user tracking record by IP
    tracking_record = await db.query(UsageStore).filter_by(ip_address=client_ip).first()
    if tracking_record:
        time_since_last_access = now - tracking_record.last_accessed
        if time_since_last_access > TIME_WINDOW:
            # Reset access count if outside time window
            tracking_record.tool_access_count = 0
            tracking_record.last_accessed = now
        else:
            tracking_record.tool_access_count += 1

        if tracking_record.tool_access_count >= ACCESS_LIMIT:
            raise HTTPException(
                status_code=429,
                detail="Too many requests, please log in to continue using this tool.",
            )
    else:
        # Create a new record for the IP
        tracking_record = UsageStore(
            ip_address=client_ip, tool_access_count=1, last_accessed=now
        )

        db.add(tracking_record)

    db.commit()
