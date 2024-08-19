from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.pagesizes import letter
from pathlib import Path
from secrets import token_hex
from api.utils.logger import logging

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def pdf_transform(transcript: str, summary: str, video_title: str = "video.mp4"):
    # Save file using BASE_DIR
    pdf_filename = f"{token_hex()}.pdf"
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
