import os
from uuid import uuid4
import assemblyai as aai
from fastapi import HTTPException, status
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.pagesizes import letter
from pathlib import Path
import json
import yt_dlp
from concurrent.futures import ThreadPoolExecutor
from api.v1.services.ai_tools.summary import summary_service

from api.utils.logger import logging
from api.utils.settings import settings
from api.utils.pagination import format_timestamp

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent


class YoutubeSummary:

    def download_video(self, link):

        # video_dir = BASE_DIR / "videos"
        video_dir = settings.TEMP_DIR
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
                raise HTTPException(
                    status_code=500, detail=f"Error downloading video: {e}"
                )
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

    def pdf_transform(self, request):
        # Save file using BASE_DIR

        if request.video_title:
            video_title = request.video_title
        else:
            video_title = "video.mp4"
        pdf_filename = f"{uuid4()}.pdf"
        video_dir = settings.TEMP_DIR
        os.makedirs(video_dir, exist_ok=True)
        file_location = os.path.join(video_dir, f"{uuid4()}.pdf")

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

        if request.summary:
            # Add the Summary heading and text
            summary_heading = Paragraph("Summary", subheading_style)
            elements.append(summary_heading)
            elements.append(Paragraph(request.summary, body_style))

        if request.transcript:
            transcript_heading = Paragraph("Transcript", subheading_style)
            elements.append(transcript_heading)
            for transcript in json.loads(request.transcript):
                elements.append(
                    Paragraph(
                        f"{format_timestamp(transcript['start_time'])}: {transcript['paragraph']}",
                        body_style,
                    )
                )

        # Build the PDF
        pdf.build(elements)

        logging.info(f"PDF saved as {pdf_filename}")
        return file_location

    def summarize_video(self, video_pth):
        """Summarize a youtube video"""

        transcript = self.transcribe(video_pth)
        full_summary = summary_service.summarize_pdf(pdf_file)
        pdf_file = self.pdf_transform(transcript, full_summary)
        return {"summary": full_summary, "transcript": transcript}


yts_service = YoutubeSummary()
