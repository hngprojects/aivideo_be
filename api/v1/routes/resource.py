from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.success_response import success_response
from api.v1.models.user import User
from api.v1.services.user import user_service
from api.v1.services.resource import resource_service
from api.v1.schemas.resource import CreateResource, UpdateResource, ResourceBase
import logging


resource = APIRouter(prefix="/resources", tags=["Resources"])


@resource.post("", response_model=success_response, status_code=201)
async def create_resource(
    schema: CreateResource,
    db: Session = Depends(get_db),
    current_admin: User = Depends(user_service.get_current_super_admin),
):
    """Endpoint to create a new Resource. Only accessible to superadmins

    Args:
        schema (CreateResource): Request Body for creating resource
        db (Session, optional): The db session object. Defaults to Depends(get_db).
        current_admin (User, optional): Admin User. Defaults to Depends(user_service.get_current_super_admin).

    Returns:
        success_response
    """
    resource = resource_service.create(db, schema=schema)

    logging.info(f"Creating new Resource. ID: {resource.id}.")
    return success_response(
        data=jsonable_encoder(ResourceBase.model_validate(resource)),
        message="Successfully created Resource",
        status_code=status.HTTP_201_CREATED,
    )
