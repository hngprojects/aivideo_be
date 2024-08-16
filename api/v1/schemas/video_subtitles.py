from pydantic import BaseModel
from typing import List, Optional

class TranscriptionRequest(BaseModel):
    video_url: str
    language: Optional[str] = "en-US"

class TranslationRequest(BaseModel):
    transcription: str
    target_language: str

class SubtitleRequest(BaseModel):
    video_id: str
    transcription: str
    timestamps: List[str]

