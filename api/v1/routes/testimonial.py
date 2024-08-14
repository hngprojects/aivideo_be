from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.success_response import success_response
from api.v1.models.user import User
from api.v1.services.user import user_service
from api.v1.services.testimonial import testimonial_service
from api.v1.schemas.testimonial import CreateTestimonialSchema, UpdateTestimonialSchema, TestimonialBase
import logging

testimonial = APIRouter(prefix="/testimonials", tags=["Testimonial"])


@testimonial.post("", response_model=success_response, status_code=201)
async def create_testimonial(
    schema: CreateTestimonialSchema,
    db: Session = Depends(get_db),
    current_admin: User = Depends(user_service.get_current_super_admin),
):
    """Endpoint to create a new testimonial. Only accessible to superadmins

    Args:
        schema (CreateTestimonialSchema): Request Body for creating testimonial
        db (Session, optional): The db session object. Defaults to Depends(get_db).
        current_admin (User, optional): Admin User. Defaults to Depends(user_service.get_current_super_admin).

    Returns:
        success_response
    """
    testimonial = testimonial_service.create(db, schema=schema)

    if schema.content.strip() == '' or schema.client_name.strip() == '':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request body")
    
    logging.info(f'Created new Testimonial. ID: {testimonial.id}.')
    return success_response(
        data=jsonable_encoder(TestimonialBase.model_validate(testimonial)),
        message="Successfully created Testimonial",
        status_code=status.HTTP_201_CREATED,
    )

@testimonial.get("", response_model=success_response, status_code=200)
async def get_all_testimonials(db: Session = Depends(get_db),):
    """Endpoint to get all testimonials

    Args:
        db (Session, optional): The db session object. Defaults to Depends(get_db).
    """    
    
    testimonials = testimonial_service.fetch_all(db=db)
    testimonials_filtered = list(
        map(lambda x: TestimonialBase.model_validate(x), testimonials)
    )
    if len(testimonials_filtered) == 0:
        testimonials_filtered = None

    return success_response(
        status_code=200,
        message="Testimonials retrieved successfully",
        data=jsonable_encoder(testimonials_filtered),
    )

@testimonial.get("/{id}", response_model=success_response, status_code=200)
async def get_single_testimonial(id: str, db: Session = Depends(get_db)):
    """Endpoint to get a single Testimonial

    Args:
        id (str): Testimonial ID
        db (Session, optional): Defaults to Depends(get_db).

    Raises:
        HTTPException: 404 NOT FOUND (Testimonial to be retrieved cannot be found)
    """
    testimonial = testimonial_service.fetch(db, testimonial_id=id)

    if testimonial == None:
        raise HTTPException(status_code=404, detail="Testimonial not found")

    return success_response(
        data=jsonable_encoder(TestimonialBase.model_validate(testimonial)),
        message="Testimonial retrieved successfully",
        status_code=status.HTTP_200_OK,
    )

@testimonial.patch("/{id}", response_model=success_response, status_code=200)
async def update_testimonial(
    id: str,
    schema: UpdateTestimonialSchema,
    db: Session = Depends(get_db),
    current_admin: User = Depends(user_service.get_current_super_admin),
):
    """Endpoint to update a testimonial. Only accessible to superadmins
    Args:
        id (str)
        schema (UpdateTestimonialSchema)
        db (Session, optional). Defaults to Depends(get_db).
        current_admin (User, optional). Defaults to Depends(user_service.get_current_super_admin).

    Raises:
        HTTPException: 404 NOT FOUND (Testimonial to be retrieved cannot be found)
    """
    testimonial = testimonial_service.update(db, testimonial_id=id, schema=schema)

    if testimonial == None:
        raise HTTPException(status_code=404, detail="Testimonial not found")

    logging.info(f'Updating Testimonial. ID: {testimonial.id}')
    return success_response(
        data=jsonable_encoder(TestimonialBase.model_validate(testimonial)),
        message="Testimonial updated successfully",
        status_code=status.HTTP_200_OK,
    )


@testimonial.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_testimonial(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(user_service.get_current_super_admin),
):
    """Endpoint to delete a testimonial. Only accessible to superadmins

    Args:
        id (str)
        db (Session, optional): Defaults to Depends(get_db).
        current_user (User, optional): Defaults to Depends(user_service.get_current_super_admin).

    Raises:
        HTTPException: 404 NOT FOUND (Testimonial to be deleted cannot be found)
    """
    status = testimonial_service.delete(db, testimonial_id=id)

    if status == False:
        raise HTTPException(status_code=404, detail="Testimonial not found")
    
    logging.info(f'Deleted testimonial. ID: {id}.')