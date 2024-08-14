from fastapi import APIRouter
from api.v1.routes.auth import auth
from api.v1.routes.user import user_router
# from api.v1.routes.ai_tools.summary import summary
from api.v1.routes.faq import faq
# from api.v1.routes.ai_tools.background_task import background_router
from tests.run_all_test import test_rout

api_version_one = APIRouter(prefix="/api/v1")

api_version_one.include_router(auth)
api_version_one.include_router(user_router)
api_version_one.include_router(test_rout)
# api_version_one.include_router(summary)
api_version_one.include_router(faq)
# api_version_one.include_router(background_router)