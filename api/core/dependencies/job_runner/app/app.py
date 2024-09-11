import sys
import os
from pathlib import Path

# BASE_DIR should point to the directory that contains the 'api' package
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent.parent

# Add BASE_DIR to sys.path
sys.path.insert(0, str(BASE_DIR))


import uvicorn
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from api.utils.logger import logger
from api.utils.success_response import success_response
from api.core.dependencies.job_runner.app.routes import job_running_router


job_app = FastAPI(title='Tifi Job Runner')

job_app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

job_app.include_router(job_running_router)

@job_app.get("/", tags=["Home"])
async def get_root(request: Request) -> dict:
    return success_response(
        message="Welcome to Job running API", 
        status_code=status.HTTP_200_OK, 
        data={"URL": ""}
    )


# REGISTER EXCEPTION HANDLERS
@job_app.exception_handler(HTTPException)
async def http_exception(request: Request, exc: HTTPException):
    """HTTP exception handler"""

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": False,
            "status_code": exc.status_code,
            "message": exc.detail,
        },
    )


@job_app.exception_handler(RequestValidationError)
async def validation_exception(request: Request, exc: RequestValidationError):
    """Validation exception handler"""

    errors = [
        {"loc": error["loc"], "msg": error["msg"], "type": error["type"]}
        for error in exc.errors()
    ]

    return JSONResponse(
        status_code=422,
        content={
            "status": False,
            "status_code": 422,
            "message": "Invalid input",
            "errors": errors,
        },
    )


@job_app.exception_handler(IntegrityError)
async def integrity_exception(request: Request, exc: IntegrityError):
    """Integrity error exception handlers"""

    logger.exception(f"Exception occured; {exc}")

    return JSONResponse(
        status_code=400,
        content={
            "status": False,
            "status_code": 400,
            "message": f"An unexpected error occurred: {exc}",
        },
    )


@job_app.exception_handler(Exception)
async def exception(request: Request, exc: Exception):
    """Other exception handlers"""

    logger.exception(f"Exception occured; {exc}")

    return JSONResponse(
        status_code=500,
        content={
            "status": False,
            "status_code": 500,
            "message": f"An unexpected error occurred: {exc}",
        },
    )


if __name__ == "__main__":
    uvicorn.run(
        "app:job_app", 
        port=7002, 
        reload=True,
        workers=4,
    )
