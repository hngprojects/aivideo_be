from pydantic import BaseModel
from typing import Optional

class JobResponse(BaseModel):
    job_id: str
    project_id: str
    status: str
    result: Optional[str] = None

    class Config:
        orm_mode = True
