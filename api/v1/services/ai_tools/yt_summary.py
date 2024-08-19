import os
from uuid import uuid4
import assemblyai as aai
from fastapi import HTTPException, status
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.pagesizes import letter
from pathlib import Path

import yt_dlp
from concurrent.futures import ThreadPoolExecutor
from api.v1.services.ai_tools.summary import summary_service

from api.utils.logger import logging
from api.utils.settings import settings


BASE_DIR = Path(__file__).resolve().parent.parent.parent

class YoutubeSummary:

    def download_video(self, link):
        
        # video_dir = BASE_DIR / "videos"
        video_dir = os.path.join(BASE_DIR, 'media', 'downloads', 'video')
        os.makedirs(video_dir, exist_ok=True)
        filepth = os.path.join(video_dir, f"{uuid4()}.mp4")

        ydl_opts = {
            "outtmpl": filepth,  # Specify the output path and filename as a string
            "format": "worst",  # Download the worst quality format available
        }

        def download_video():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([link])

        # Run the download in a separate thread to avoid blocking
        with ThreadPoolExecutor() as executor:
            future = executor.submit(download_video)
            try:
                future.result()
            except yt_dlp.utils.DownloadError as e:
                raise HTTPException(status_code=500, detail=f"Error downloading video: {e}")
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"An unexpected error occurred: {e}"
                )

        return filepth
    

    def transcribe(self, filepth: str) -> str:
        """utilise the assembly assemblyai transcribe video files"""

        try:
            aai.settings.api_key = settings.ASSEMBLYAI_API_KEY
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
        
    
    def pdf_transform(self, transcript: str, summary: str, video_title: str = "video.mp4"):
        # Save file using BASE_DIR
        pdf_filename = f"{uuid4()}.pdf"
        video_dir = BASE_DIR / "yt_pdf"
        video_dir.mkdir(
            parents=True, exist_ok=True
        )  # Create the directory if it doesn't exist
        file_location = video_dir / pdf_filename

        # Create a SimpleDocTemplate for the PDF
        pdf = SimpleDocTemplate(str(file_location), pagesize=letter)

        # Get the default stylesheet
        styles = getSampleStyleSheet()
        heading_style = styles["Heading1"]
        subheading_style = styles["Heading2"]
        body_style = styles["BodyText"]

        # Create a list to hold the PDF elements
        elements = []

        # Add the main heading
        main_heading = Paragraph(
            f"Summary and Transcription of {video_title}", heading_style
        )
        elements.append(main_heading)

        # Add the Transcript heading and text
        transcript_heading = Paragraph("Transcript", subheading_style)
        elements.append(transcript_heading)
        elements.append(Paragraph(transcript, body_style))

        # Add the Summary heading and text
        summary_heading = Paragraph("Summary", subheading_style)
        elements.append(summary_heading)
        elements.append(Paragraph(summary, body_style))

        # Build the PDF
        pdf.build(elements)

        logging.info(f"PDF saved as {pdf_filename}")
        return file_location


    def summarize_video(self, video_pth):
        """Summarize a youtube video"""

        transcript = self.transcribe(video_pth)
        pdf_file = self.pdf_transform(transcript)
        full_summary = summary_service.summarize_pdf(pdf_file)
        return {"summary": full_summary, "transcript": transcript}


yts_service = YoutubeSummary()
