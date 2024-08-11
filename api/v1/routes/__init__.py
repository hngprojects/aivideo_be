
from fastapi import APIRouter
from api.v1.routes.auth import auth
from api.v1.routes.user import user_router
from api.v1.routes.summary import summary
from tests.run_all_test import test_rout

api_version_one = APIRouter(prefix="/api/v1")

api_version_one.include_router(auth)
api_version_one.include_router(user_router)
api_version_one.include_router(test_rout)
api_version_one.include_router(summary)
