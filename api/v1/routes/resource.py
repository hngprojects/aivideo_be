from fastapi import APIRouter, Depends, status, Query
from fastapi.encoders import jsonable_encoder
from typing import Annotated, Optional
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.success_response import success_response
from api.v1.models.user import User
from api.v1.services.user import user_service
from api.v1.services.resource import resource_service
from api.v1.schemas.resource import (
    CreateResource,
    ResourceBase,
    AllResourcesResponse,
    UpdateResource,
)
import logging


resource = APIRouter(prefix="/resources", tags=["Resources"])


@resource.post(
    "",
    response_model=CreateResourceResponse,
    status_code=201,
    summary="Create new Resource",
    description="Admin endpoint to create a resource",
)
async def create_resource(
    schema: CreateResource,
    publish: bool = Query(True),
    db: Session = Depends(get_db),
    current_admin: User = Depends(user_service.get_current_super_admin),
):
    """Endpoint to create a new Resource. Only accessible to superadmins

    Args:
        schema (CreateResource): Request Body for creating resource
        publish (bool): query parameter to decide whether or not to publish after creating
        db (Session, optional): The db session object. Defaults to Depends(get_db).
        current_admin (User, optional): Admin User. Defaults to Depends(user_service.get_current_super_admin).

    Returns:
        success_response
    """
    resource = resource_service.create(db, schema=schema, publish=publish)

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
    search: Optional[str] = Query(None),
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
    return resource_service.fetch_all(db, page, per_page, search, **query_params)


@resource.get(
    "/public", status_code=status.HTTP_200_OK, response_model=AllResourcesResponse
)
async def get_public_resources(
    db: Annotated[Session, Depends(get_db)],
    page: int = 1,
    per_page: int = 10,
    search: Optional[str] = Query(None),
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


@resource.get(
    "/search", status_code=status.HTTP_200_OK, response_model=AllResourcesResponse
)
async def search_resources(
    keywords: str,
    db: Session = Depends(get_db),
    page: int = 1,
    per_page: int = 10,
):
    """
    Search for resources by keywords.

    Args:
        keywords: Search terms provided by the user.
        db: Database session object.
        page: Page number for pagination.
        per_page: Max number of resources per page.

    Returns:
        Search results in a paginated format.
    """
    search_results = resource_service.search_resources(db, keywords, page, per_page)
    return search_results


@resource.patch(
    "/{resource_id}", response_model=success_response, status_code=status.HTTP_200_OK
)
async def update_resources(
    schema: UpdateResource,
    resource_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(user_service.get_current_super_admin)],
):
    """
    Route to Update resources

    Args:
        schema (UpdateResource): Schema for the resource model
        resource_id (str): id for the resource about to be updated
        db (Annotated[Session, Depends): database dependency
        current_user: dependency to verify whether the supposed user is an admin. Defaults to Annotated[User, Depends(user_service.get_current_super_admin)].

    Returns:
        dict: {"status":200,
               "message":Resource Updated Successfully,
               "data" : {}
               }
    """
    resource = resource_service.update(db=db, resource_id=resource_id, schema=schema)
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Resource updated Succesfully",
        data=jsonable_encoder(ResourceBase.model_validate(resource)),
    )


@resource.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resources(
    resource_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(user_service.get_current_super_admin)],
):
    """
    Route to soft  delete Resources

    Args:
        resource_id (str): used as an identifier for the resource
        db (Annotated[Session, Depends): database dependency
        current_user (Annotated[User, Depends): Admin User dependency
    """
    return resource_service.delete(db=db, Resource_id=resource_id)


@resource.get(
    "/{resource_id}", status_code=status.HTTP_200_OK, response_model=success_response
)
async def get_resource_by_id(resource_id: str, db: Annotated[Session, Depends(get_db)]):
    """
    Route to get resource by its id

    Args:
        resource_id (str):the identifier of the resource to query
        db (Annotated[Session, Depends): database dependency
    """

    resource = resource_service.fetch(db=db, id=resource_id)

    resource = resource_service.fetch(db=db, id=resource_id)
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Resource fetched successfully",
        data=jsonable_encoder(resource),
    )


@resource.put(
    "/{resource_id}/publish",
    status_code=status.HTTP_200_OK,
    summary="Publish a resource",
)
async def publish_resource(
    resource_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[User, Depends(user_service.get_current_super_admin)],
):
    resource_service.publish(db=db, Resource_id=resource_id)

    return success_response(
        status_code=status.HTTP_200_OK, message="Resource successfully published!"
    )
