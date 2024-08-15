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
    assert (
        "Failed to open PDF file" in data["message"]
        or "The uploaded PDF file is empty" in data["message"]
    )
