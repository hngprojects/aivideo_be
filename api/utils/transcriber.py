import os

import assemblyai as aai
from decouple import config
from fastapi import HTTPException, status

from api.utils.logger import logging


def transcribe(filepth: str) -> str:
    """utilise the assembly assemblyai transcribe video files"""

    try:
        aai.settings.api_key = config("ASEMBLYAI_API_KEY")
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(filepth)

        # Delete the file after transcription
        os.remove(filepth)

        logging.info("video transcript completed")
        return f"NOTE THIS IS A VIDEO: {transcript.text}"
    except Exception as e:
        os.remove(filepth)
        logging.error("Error processing assemblyai transcript")
        raise HTTPException(
            status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
            detail=f"An Error occurred: {e}",
        )
