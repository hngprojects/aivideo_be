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