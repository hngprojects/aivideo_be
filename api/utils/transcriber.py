import assemblyai as aai
from decouple import config
import os
from fastapi import HTTPException, status


async def transcribe(filepth: str) -> str:
    """utilise the assembly assemblyai transcribe video files"""

    try:
        aai.settings.api_key = config("ASSEMBLY_AI_API_KEY")
        transcriber = aai.Transcriber()

        transcript = transcriber.transcribe(filepth)

        # Delete the file after transcription
        os.remove(filepth)

        return f"NOTE THIS IS A VIDEO: {transcript.text}"
    except:
        raise HTTPException(
            status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
            detail="Failed to transcribe video",
        )
