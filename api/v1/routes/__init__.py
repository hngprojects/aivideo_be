from fastapi import APIRouter
from api.v1.routes.auth import auth
from api.v1.routes.user import user_router
from api.v1.routes.payment import payments
from api.v1.routes.billing_plan import billing_plan
from api.v1.routes.ai_tools.summary import summary
from api.v1.routes.ai_tools.save_summary import save_summary
from api.v1.routes.faq import faq
from api.v1.routes.presets import preset_router
from api.v1.routes.ai_tools.save_summary import save_summary
from api.v1.routes.project import project_router
from api.v1.routes.google_auth import google_auth
from api.v1.routes.websocket import websocket_router
from tests.run_all_test import test_rout
from api.v1.routes.google_auth import google_auth
from api.v1.routes.request_password import pwd_reset
from api.v1.routes.profile import profile
from api.v1.routes.job import job_router

api_version_one = APIRouter(prefix="/api/v1")

api_version_one.include_router(auth)
api_version_one.include_router(google_auth)
api_version_one.include_router(user_router)
api_version_one.include_router(summary)
api_version_one.include_router(profile)
api_version_one.include_router(payments)
api_version_one.include_router(billing_plan)
api_version_one.include_router(faq)
api_version_one.include_router(google_auth)
api_version_one.include_router(pwd_reset)
api_version_one.include_router(preset_router)
api_version_one.include_router(websocket_router)
api_version_one.include_router(test_rout)
api_version_one.include_router(save_summary)
api_version_one.include_router(project_router)
api_version_one.include_router(job_router)
