from pydantic import BaseModel
from typing import Any, Dict, Optional

class JobResponse(BaseModel):
    job_id: str
    project_id: str
    status: str
    result: Optional[str] = None

    class Config:
        from_attributes = True


class UpdateJob(BaseModel):
    
    job_name: str
    job_thumbnail_url: Optional[str] = None
    

class UpdateJobPayload(BaseModel):
    
    payload: Dict[str, Any]
    