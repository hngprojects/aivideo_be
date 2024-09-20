import csv
import os
from io import BytesIO
import assemblyai as aai
import yt_dlp
from pytubefix import YouTube
from uuid import uuid4
from langchain_community.document_loaders import AssemblyAIAudioTranscriptLoader
from langchain_community.document_loaders.assemblyai import TranscriptFormat

from api.utils.settings import settings
from api.utils.pdf_builder import PDFBuilder
from api.v1.services.ffmpeg_tools import ffmpeg_service
from api.v1.services.ai_tools.pdf_summarizer import pdf_summary_service


class YtVidSummarizerService:
    '''Youtube and video summarizer service'''

    def __init__(self):
        aai.settings.api_key = settings.ASSEMBLYAI_API_KEY
        self.transcriber = aai.Transcriber()

    
    # TODO: Fix inconsistency with download of youtube videos
    def download_youtube_video(self, youtube_url: str):
        '''This function downloads a youtube video(s) and saves it to a temporary storage'''

        output_path = os.path.join(settings.TEMP_DIR, f'ytvid-{uuid4()}.mp4')

        try:
            # Create YouTube object
            yt = YouTube(youtube_url)
            
            # Get the stream with the worst (lowest) quality
            worst_quality_stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').first()
            
            # Download the worst quality video
            file = worst_quality_stream.download(
                output_path=settings.TEMP_DIR,
                filename=f'ytvid-{uuid4()}.mp4'
            )

            return file

        except Exception as e:
            raise e

    
    # def download_youtube_video(self, youtube_url: str):
    #     '''This function downloads a youtube video(s) and saves it to a temporary storage'''

    #     output_path = os.path.join(settings.TEMP_DIR, f'ytvid-{uuid4()}.mp4')
    #     ydl_opts = {
    #         'format': 'worst',  # Select the worst quality
    #         'outtmpl': output_path,
    #         'nocheckcertificate': True,
    #     }

    #     try:
    #         with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    #             ydl.download([youtube_url])
    #             return output_path
            
    #     except Exception as e:
    #         raise e 
        
    
    def extract_audio_from_video(self, video_path: str):
        '''This function extracts audio from a video and returns the audio file'''

        output_path = os.path.join(settings.TEMP_DIR, f'ytaud-{uuid4()}')
        # Use ffmpeg to extract the audio from the video
        ffmpeg_service.extract_audio_from_video(
            input_video=video_path,
            output_path=output_path
        )
        return output_path

    
    def transcribe_audio(self, audio_path_or_url: str):
        '''This function transcribes audio into text'''

        transcript = self.transcriber.transcribe(audio_path_or_url)
        if transcript.error:
            raise Exception(f'Error transcribing audio: {transcript.error}')
        
        return transcript.text
    

    def summarize_transcript(self, transcript: str, detail_level: str = 'short'):
        '''This function summarizes the transcript'''

        return pdf_summary_service.summarize_text(
            text=transcript, 
            detail_level=detail_level
        )

    
    def generate_transcript_with_timestamp(self, audio_path_or_url: str, as_srt: bool = False):
        '''This function generates a transcript with timestamps'''

        loader = AssemblyAIAudioTranscriptLoader(
            file_path=audio_path_or_url,
            api_key=settings.ASSEMBLYAI_API_KEY,
            transcript_format=TranscriptFormat.SUBTITLES_VTT if not as_srt else TranscriptFormat.SUBTITLES_SRT
        )
        docs = loader.load()

        return docs[0].page_content
    

    def save_transcript_and_summary_to_pdf(
        self, 
        transcript: str, 
        summary: str, 
        transcript_with_timestamp: str
    ):
        '''This function saves the transcript and summary of the transcript to a pdf file'''

        pdf_buffer = BytesIO()
        pdf_builder = PDFBuilder(pdf_buffer)

        file_path = os.path.join(settings.TEMP_DIR, f"ytvidsum-{uuid4()}.pdf")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Add transcript to pdf file
        pdf_builder.add_section(title='Transcript', text=transcript)

        # Add summary to pdf file
        pdf_builder.add_section(title='Summary', text=summary)

        # Add transcript with timestamp to pdf file
        pdf_builder.add_section(title='Transcript with Timestamp', text=transcript_with_timestamp)

        # Build pdf
        pdf_builder.build()

        # Save the PDF content to a file
        pdf_buffer.seek(0)
        with open(file_path, "wb") as f:
            f.write(pdf_buffer.read())

        pdf_buffer.close()

        return file_path
    

    def save_transcript_and_summary_to_csv(
        self, 
        transcript: str, 
        summary: str, 
        transcript_with_timestamp: str,
        save_path: str
    ):
        '''This function saves the transcript and summary of the transcript to a csv file'''

        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        # Check if the file already exists
        file_exists = os.path.isfile(save_path)

        with open(save_path, "a", newline='') as f:
            writer = csv.writer(f)

            if not file_exists:
                writer.writerow(['Transcript', 'Summary', 'Transcript with Timestamp'])

            writer.writerow([transcript, summary, transcript_with_timestamp])


ytvid_service = YtVidSummarizerService()
