from pydantic import BaseModel
from typing import List, Optional
from fastapi import File, UploadFile

class TranscriptionRequest(BaseModel):
    language: Optional[str] = "en-US"

class SubtitleRequest(BaseModel):
    timestamps: List[str]

class TranslationRequest(BaseModel):
    transcription: str
    target_language: str
