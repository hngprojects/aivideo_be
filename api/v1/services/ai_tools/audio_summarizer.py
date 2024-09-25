import os
from io import BytesIO
import assemblyai as aai
from uuid import uuid4
from langchain_community.document_loaders import AssemblyAIAudioTranscriptLoader
from langchain_community.document_loaders.assemblyai import TranscriptFormat

from api.utils.settings import settings
from api.utils.pdf_builder import PDFBuilder
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
        result = docs[0].page_content

        if not as_srt:
            result = result.replace('WEBVTT\n\n', '')

        return result


    def summarize_transcript(self, transcript: str, detail_level: str = 'short'):
        '''This function summarizes the transcript'''

        return pdf_summary_service.summarize_text(
            text=transcript, 
            detail_level=detail_level
        )


    def save_to_pdf(self, summary: str, transcript: str, prefix_file_name: str = 'audsum'):
        '''This saves the generated summary and transcript to a file as a pdf'''

        pdf_buffer = BytesIO()
        pdf_builder = PDFBuilder(pdf_buffer)

        file_path = os.path.join(settings.TEMP_DIR, f"{prefix_file_name}-{uuid4()}.pdf")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Add summary to pdf file
        pdf_builder.add_section(title='Summary', text=summary)

        # Add transcript to pdf file
        pdf_builder.add_section(title='Transcript', text=transcript)

        # Build pdf
        pdf_builder.build()

        # Save the PDF content to a file
        pdf_buffer.seek(0)
        with open(file_path, "wb") as f:
            f.write(pdf_buffer.read())

        pdf_buffer.close()

        return file_path


audio_summary_service = AudioSummaryService()
   