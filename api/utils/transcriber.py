import assemblyai as aai
from decouple import config


async def transcribe(filepth: str) -> str:
    """utilise the assembly assemblyai transcribe video files"""

    try:
        aai.settings.api_key = config("ASSEMBLY_AI_API_KEY")
        transcriber = aai.Transcriber()

        transcript = transcriber.transcribe(filepth)

        return transcript.text
    except:
        return None
