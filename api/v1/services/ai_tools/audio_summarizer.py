import assemblyai as aai
from uuid import uuid4
from langchain_community.document_loaders import AssemblyAIAudioTranscriptLoader
from langchain_community.document_loaders.assemblyai import TranscriptFormat

from api.utils.settings import settings
from api.utils.pdf_builder import PDFBuilder
from api.v1.services.ffmpeg_tools import ffmpeg_service
from api.v1.services.ai_tools.pdf_summarizer import pdf_summary_service


class AudioSummaryService:

    def __init__(self):
        aai.settings.api_key = settings.ASSEMBLYAI_API_KEY
        self.transcriber = aai.Transcriber()

    