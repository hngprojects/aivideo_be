from fastapi import APIRouter, Depends, status, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from typing import Annotated, Optional, Literal
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.success_response import success_response
from api.v1.models.user import User
from api.v1.services.user import user_service
from api.v1.services.resource import resource_service
from api.v1.schemas.resource import (
    CreateResource,
    UpdateResource,
    ResourceBase,
    AllResourcesResponse,
)
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


@resource.get("", status_code=status.HTTP_200_OK, response_model=AllResourcesResponse)
async def get_resources(
    current_user: Annotated[User, Depends(user_service.get_current_super_admin)],
    db: Annotated[Session, Depends(get_db)],
    page: int = 1,
    per_page: int = 10,
    is_published: Optional[bool] = Query(None),
    is_deleted: Optional[bool] = Query(None),
):
    """
    Retrieves all resources.
    Args:
        current_user: The current user(admin) making the request
        db: database Session object
        page: the page number
        per_page: the maximum size of resources for each page
        is_published: boolean to filter published resources
        is_deleted: boolean to filter deleted resources
    Returns:
        ResourceData
    """
    query_params = {
        "is_published": is_published,
        "is_deleted": is_deleted,
    }
    return resource_service.fetch_all(db, page, per_page, **query_params)


@resource.get(
    "/public", status_code=status.HTTP_200_OK, response_model=AllResourcesResponse
)
async def get_public_resources(
    db: Annotated[Session, Depends(get_db)], page: int = 1, per_page: int = 10
):
    """
    Retrieves all public resources.
    Args:
        db: database Session object
        page: the page number
        per_page: the maximum size of resources for each page
    Returns:
        ResourceData
    """

    return resource_service.fetch_all_public(db, page, per_page)

