import os
from decouple import config
from fastapi import HTTPException, status
from deep_translator import GoogleTranslator
from api.v1.services.ai_tools.summary_audio import SummaryService


def __init__(self):
    super().__init__()
    self.translator = GoogleTranslator()

def process_audio_summary(file_path: str, target_lang: str = 'es') -> dict:
    """Transcribes, summarizes, translates, and handles audio files."""

    # Initialize the SummaryService
    summary_service = SummaryService()

    try:
        # Step 1: Transcribe, summarize, translate, and export the audio file
        result = summary_service.process_audio(file_path, target_lang)

        # Delete the audio file after processing
        os.remove(file_path)

        return result

    except Exception as e:
        # Handle any errors that occur during processing
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process the audio file: {str(e)}",
        )