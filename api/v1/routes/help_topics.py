from typing import Annotated
from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from api.db.database import get_db
from api.utils.success_response import success_response
from api.v1.models.user import User
from api.v1.schemas.help_topics import HelpCenterCreate
from api.v1.services.help_topics import HelpTopicsService
from api.v1.services.user import user_service
from sqlalchemy.orm import Session

help_topics = APIRouter(prefix="/help-topics", tags=["Help Topics"])


@help_topics.get("", status_code=200)
async def get_topics(db: Annotated[Session, Depends(get_db)]):
    topics = HelpTopicsService.fetch_all(db)

    return success_response(
        message="Help Topics fetched successfully",
        data=topics,
        status_code=200,
    )

@help_topics.post("", status_code=201)
async def create_topic(
    schema: HelpCenterCreate,
    db: Annotated[Session, Depends(get_db)], 
    current_user: User = Depends(user_service.get_current_super_admin)
):
    topic = HelpTopicsService.create(db, schema)

    return success_response(
        message="Help Topic created successfully",
        data=jsonable_encoder(topic),
        status_code=201,
   )


@help_topics.delete("", status_code=201)
async def delete_all_topics(
    db: Annotated[Session, Depends(get_db)], 
    current_user: User = Depends(user_service.get_current_super_admin)
):
    HelpTopicsService.delete_all(db)

    return success_response(
        message="Help Topics deleted successfully",
        status_code=201,
   )