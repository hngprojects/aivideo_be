from fastapi import APIRouter, Depends, Request, Query, BackgroundTasks
from sqlalchemy.orm import Session
from api.v1.schemas.request_password_reset import RequestEmail, ResetPassword
from api.db.database import get_db as get_session
from api.v1.services.request_pwd import reset_service
import logging
from api.utils.success_response import success_response
<<<<<<< HEAD
from api.v1.services.user import user_service
from api.v1.models.user import User
=======
>>>>>>> cfec116 (feat: implemented magic link, password reset and refactored google auth)

pwd_reset = APIRouter(prefix="/auth", tags=["Authentication"])


# generate password reset link
<<<<<<< HEAD
@pwd_reset.post("/request-forget-password")
async def request_forget_password(
=======
@pwd_reset.post("/request-password-reset")
async def request_reset_link(
>>>>>>> cfec116 (feat: implemented magic link, password reset and refactored google auth)
    reset_schema: RequestEmail,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_session),
):
<<<<<<< HEAD
    url = "api/v1/auth/forget-password"
=======
    url = "api/v1/auth/reset-password"
>>>>>>> cfec116 (feat: implemented magic link, password reset and refactored google auth)
    template_file = "reset_password.html"
    subject = "HNG11 PASSWORD RESET"
    data =  await reset_service.create(reset_schema, request, db, background_tasks,
                                           subject=subject, template_file=template_file, url=url)
    return success_response(**data)

# process password link
<<<<<<< HEAD
@pwd_reset.get("/forget-password")
async def process_forget_password_link(
=======
@pwd_reset.get("/reset-password")
async def process_reset_link(
>>>>>>> cfec116 (feat: implemented magic link, password reset and refactored google auth)
    token: str = Query(...), db: Session = Depends(get_session)
):
    return reset_service.process_reset_link(token, db)


# change the password
<<<<<<< HEAD
@pwd_reset.post("/forget-password")
async def forget_password(
=======
@pwd_reset.post("/reset-password")
async def reset_password(
>>>>>>> cfec116 (feat: implemented magic link, password reset and refactored google auth)
    data: ResetPassword,
    token: str = Query(...),
    session: Session = Depends(get_session),
):
    return reset_service.reset_password(data, token, session)
<<<<<<< HEAD

# change the password
@pwd_reset.post("/reset-password")
async def reset_password(
    data: ResetPassword,
    session: Session = Depends(get_session),
    current_user: User = Depends(user_service.get_current_user)
):
    return reset_service.reset_user_password(data, session, current_user)
=======
>>>>>>> cfec116 (feat: implemented magic link, password reset and refactored google auth)
