from typing import Optional
from fastapi import (
    Depends,
    APIRouter,
    HTTPException,
    Request
)
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.success_response import success_response
from api.v1.models.project import ProjectToolsEnum
from api.v1.schemas.tools.article_translator import TranslateArticle
from api.v1.services.job import tifi_job_service
from api.v1.services.user import user_service
from api.utils.tool_limiter import track_tool_usage
from api.v1.models.user import User

article_router = APIRouter(prefix="/tools", tags=["Tools"])

@article_router.post("/article-translator", response_model=success_response)
# @track_tool_usage(ProjectToolsEnum.article_translator)
async def generate_article_translations(
    request: Request,
    schema: TranslateArticle,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(user_service.get_current_user_optional)
):
    '''Endpoint to generate translations of a single article'''

    
    if len(schema.languages) != len(schema.names):
        raise HTTPException(
            status_code=400, 
            detail=f'Languages ({len(schema.languages)}) and names ({len(schema.names)}) must ne of the same length'
        )

    job = tifi_job_service.create(
        db=db,
        tool_name=ProjectToolsEnum.article_translator.value,
        payload={
            'article': schema.article, 
            'languages': schema.languages,
            'names': schema.names,
        },
        user_id=user.id if user else None,
        is_parallel=True
    )

    return success_response(
        status_code=202,
        message=f"{ProjectToolsEnum.article_translator.value} task initiated successfully",
        data={"job_id": job.id,}
    )
