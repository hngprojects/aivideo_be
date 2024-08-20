from pydantic import BaseModel
from typing import Optional

class TranscriptionRequest(BaseModel):
    language: Optional[str] = "en-US"

class SubtitleRequest(BaseModel):
    interval_seconds: Optional[int] = 10

class TranslationRequest(BaseModel):
    transcription: str
    target_language: str
