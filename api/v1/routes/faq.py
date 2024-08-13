from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.success_response import success_response
from api.v1.models.user import User
from api.v1.services.user import user_service
from api.v1.services.faq import faq_service
from api.v1.schemas.faq import CreateFAQ, UpdateFAQ, FAQBase
import logging

faq = APIRouter(prefix="/faqs", tags=["FAQs"])

@faq.post("", response_model=success_response, status_code=201)
async def create_faq(
    schema: CreateFAQ,
    db: Session = Depends(get_db),
    current_admin: User = Depends(user_service.get_current_super_admin),
):
    """Endpoint to create a new FAQ. Only accessible to superadmins

    Args:
        schema (CreateFAQ): Request Body for creating faq
        db (Session, optional): The db session object. Defaults to Depends(get_db).
        current_admin (User, optional): Admin User. Defaults to Depends(user_service.get_current_super_admin).

    Returns:
        success_response
    """
    faq = faq_service.create(db, schema=schema)

    if schema.answer.strip() == '' or schema.category.strip() == '' or schema.question.strip() == '':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request body")
    
    logging.info(f'Creating new FAQ. ID: {faq.id}.')
    return success_response(
        data=jsonable_encoder(FAQBase.model_validate(faq)),
        message="Successfully created FAQ",
        status_code=status.HTTP_201_CREATED,
    )

@faq.get("", response_model=success_response, status_code=200)
async def get_all_faqs(db: Session = Depends(get_db),):
    """Endpoint to get all FAQs

    Args:
        db (Session, optional): The db session object. Defaults to Depends(get_db).
    """    
    
    faqs = faq_service.fetch_all(db=db)
    faqs_filtered = list(
        map(lambda x: FAQBase.model_validate(x), faqs)
    )
    if len(faqs_filtered) == 0:
        faqs_filtered = None

    return success_response(
        status_code=200,
        message="FAQs retrieved successfully",
        data=jsonable_encoder(faqs_filtered),
    )

@faq.get("/{id}", response_model=success_response, status_code=200)
async def get_single_faq(id: str, db: Session = Depends(get_db)):
    """Endpoint to get a single FAQ

    Args:
        id (str): Faq ID
        db (Session, optional): Defaults to Depends(get_db).

    Raises:
        HTTPException: 404 NOT FOUND (Faq to be retrieved cannot be found)
    """
    faq = faq_service.fetch(db, faq_id=id)

    if faq == None:
        raise HTTPException(status_code=404, detail="FAQ not found")

    return success_response(
        data=jsonable_encoder(FAQBase.model_validate(faq)),
        message="Successfully fetched FAQ",
        status_code=status.HTTP_200_OK,
    )


@faq.patch("/{id}", response_model=success_response, status_code=200)
async def update_faq(
    id: str,
    schema: UpdateFAQ,
    db: Session = Depends(get_db),
    current_admin: User = Depends(user_service.get_current_super_admin),
):
    """Endpoint to update an FAQ. Only accessible to superadmins
    Args:
        id (str)
        schema (UpdateFAQ)
        db (Session, optional). Defaults to Depends(get_db).
        current_admin (User, optional). Defaults to Depends(user_service.get_current_super_admin).

    Raises:
        HTTPException: 404 NOT FOUND (Faq to be retrieved cannot be found)
    """
    faq = faq_service.update(db, faq_id=id, schema=schema)

    if faq == None:
        raise HTTPException(status_code=404, detail="FAQ not found")

    logging.info(f'Updating FAQ. ID: {faq.id}')
    return success_response(
        data=jsonable_encoder(FAQBase.model_validate(faq)),
        message="FAQ updated successfully",
        status_code=status.HTTP_200_OK,

    )