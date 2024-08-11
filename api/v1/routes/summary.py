from datetime import timedelta
from fastapi import BackgroundTasks, Depends, status, APIRouter, Response, Request, File, UploadFile
import io
from typing import Optional

from api.utils.success_response import success_response
from api.utils.file_upload import upload_file
from api.db.database import get_db
from api.v1.services.summary import summary_service

summary = APIRouter(prefix="/summary", tags=["Summary"])

@summary.post('/summarize-pdf', status_code=status.HTTP_200_OK)
async def summarize_pdf_endpoint(file: UploadFile = File(...)):
    try:
        pdf_file = await upload_file(file, allowed_extensions=['pdf'], upload_folder='pdf', save_extension='pdf')
        summary = summary_service.summarize_pdf(pdf_file)
        return success_response(
            status_code=200,
            message="File summarized successfully",
            data={
                "summary": summary
            }
        )
    except Exception as e:
        return {"error": str(e)}
