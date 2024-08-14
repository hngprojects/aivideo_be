from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak
from reportlab.lib.pagesizes import letter
from pathlib import Path
from secrets import token_hex

BASE_DIR = Path(__file__).resolve().parent.parent.parent


async def pdf_transform(yttext: str):
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

    # Create a list to hold the PDF elements
    elements = []

    # Add the full transcription to the elements list with proper wrapping
    text = yttext
    paragraphs = yttext.split(
        "\n\n"
    )  # Assuming paragraphs are separated by double newlines

    for para in paragraphs:
        elements.append(Paragraph(para, styles["BodyText"]))
        elements.append(
            PageBreak()
        )  # Add a page break if you want each paragraph on a new page

    # Build the PDF
    pdf.build(elements)

    print(f"PDF saved as {pdf_filename}")

    return str(file_location)
