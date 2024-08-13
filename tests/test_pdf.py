from fastapi.testclient import TestClient
from main import app

from api.v1.services.ai_tools.summary import summary_service
import pytest
from langchain.chains.llm import LLMChain
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import Runnable
from unittest.mock import patch, MagicMock
from pypdf import PdfReader

client = TestClient(app)


class MockChatOpenAI(Runnable):
    def __call__(self, *args, **kwargs):
        return self

    def invoke(self, input, config=None, **kwargs):
        return "This is a mocked summary."


@pytest.fixture
def mock_pdf_reader():
    mock_pdf = MagicMock(spec=PdfReader)
    mock_pdf.pages = [MagicMock(), MagicMock(), MagicMock()]
    return mock_pdf


@pytest.fixture
def mock_upload_file(mocker):
    mocker.patch("api.utils.files.upload_file", return_value="test_files/sample.pdf")


@pytest.fixture
def mock_summary_service(mocker):
    mocker.patch.object(
        summary_service,
        "summarize_pdf",
        return_value="This is a mock summary of the PDF.",
    )


@patch("api.v1.services.ai_tools.summary.ChatOpenAI", new_callable=MockChatOpenAI)
@patch("api.utils.files.upload_file")
@patch("pypdf.PdfReader")
def test_summarize_pdf_success(mock_pdf_reader, mock_upload_file, mock_chat_openai):
    # Mocking file upload and PdfReader
    mock_upload_file.return_value = (
        "mocked_sample.pdf"  # Mock the file upload to return a path
    )
    mock_pdf_reader.return_value.pages = [
        MagicMock(),
        MagicMock(),
        MagicMock(),
    ]  # Mock PDF pages

    for page in mock_pdf_reader.return_value.pages:
        page.extract_text.return_value = (
            "This is a mocked page content"  # Mocking the text extraction from pages
        )

    # Minimal valid PDF content
    valid_pdf_content = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
        b"2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n"
        b"3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n"
        b"/Contents 4 0 R\n/Resources <<\n/Font << /F1 5 0 R >>\n"
        b"/ProcSet [/PDF /Text]\n>>\n>>\nendobj\n"
        b"4 0 obj\n<<\n/Length 55\n>>\nstream\n"
        b"BT\n/F1 24 Tf\n100 100 Td\n(Hello, PDF!) Tj\nET\n"
        b"endstream\nendobj\n"
        b"5 0 obj\n<<\n/Type /Font\n/Subtype /Type1\n"
        b"/BaseFont /Helvetica\n>>\nendobj\n"
        b"xref\n0 6\n0000000000 65535 f\n"
        b"0000000010 00000 n\n0000000067 00000 n\n"
        b"0000000114 00000 n\n0000000311 00000 n\n"
        b"0000000383 00000 n\n"
        b"trailer\n<<\n/Root 1 0 R\n>>\nstartxref\n490\n%%EOF"
    )

    response = client.post(
        "/api/v1/tools/summary/pdf-summarizer",
        files={"file": ("sample.pdf", valid_pdf_content, "application/pdf")},
    )

    assert response.status_code == 202
    data = response.json()
    assert "success" in data, "Expected 'success' key in the response"
    assert data["success"] is True
    assert "file_name" in data["data"]
    assert "number_of_pages" in data["data"]
    assert "estimated_read_time" in data["data"]
    assert "summary" in data["data"]
    assert "task_id" in data["data"]

def test_summarize_pdf_invalid_file_type():
    response = client.post(
        "/api/v1/tools/summary/pdf-summarizer",
        files={"file": ("sample.txt", b"Sample text file", "text/plain")},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == False  # Changed from "FAILED" to False
    assert data["message"] == "Invalid file format"
    



def test_summarize_pdf_empty_file():
    response = client.post(
        "/api/v1/tools/summary/pdf-summarizer",
        files={"file": ("empty.pdf", b"", "application/pdf")},
    )

    assert response.status_code == 400  # Check if the status code is 400 (Bad Request)
    data = response.json()

    assert "message" in data  # Check if 'message' key exists
    assert "Failed to open PDF file" in data["message"] or "The uploaded PDF file is empty" in data["message"]

