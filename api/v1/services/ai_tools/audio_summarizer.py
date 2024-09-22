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

    
    def transcribe_audio(self, audio_path_or_url: str):
        '''This function transcribes audio into text'''

        transcript = self.transcriber.transcribe(audio_path_or_url)
        if transcript.error:
            raise Exception(f'Error transcribing audio: {transcript.error}')
        
        return transcript.text

    
    def generate_transcript_with_timestamp(self, audio_path_or_url: str, as_srt: bool = False):
        '''This function generates a transcript with timestamps'''

        loader = AssemblyAIAudioTranscriptLoader(
            file_path=audio_path_or_url,
            api_key=settings.ASSEMBLYAI_API_KEY,
            transcript_format=TranscriptFormat.SUBTITLES_VTT if not as_srt else TranscriptFormat.SUBTITLES_SRT
        )
        docs = loader.load()

        return docs[0].page_content


audio_summary_service = AudioSummaryService()
    