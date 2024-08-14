from fastapi import FastAPI, UploadFile, File, HTTPException, APIRouter
from api.v1.schemas.audio_transcriber import TranslationRequest
import os
from api.v1.services.audio_transcriber import transcribe_audio, translate_text


AUDIOFILE = "audio.mp3"  
audio = APIRouter(prefix="/tools/audio-transcribe", tags=["Tools"])

@audio.post("/upload/")
async def upload_audio(file: UploadFile = File(...)):
    """Upload and transcribe audio file."""
    try:
        with open(AUDIOFILE, "wb") as buffer:
            buffer.write(await file.read())
        transcription = transcribe_audio(AUDIOFILE)
        with open("transcription_with_timestamps.txt", "w", encoding="utf-8") as file:
            file.write(transcription)
        return {"message": "Audio transcribed successfully", "transcription": transcription}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@audio.post("/translate/")
async def translate_text_endpoint(request: TranslationRequest):
    """Translate text to the specified language."""
    try:
        translation = translate_text(request.text, request.target_language)
        with open("translation.txt", "w", encoding="utf-8") as file:
            file.write(translation)
        return {"message": "Text translated successfully", "translation": translation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
