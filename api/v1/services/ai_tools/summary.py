from api.utils.settings import settings
import pytesseract
from PIL import Image
from io import BytesIO
from openai import ChatCompletion
from tenacity import retry, stop_after_attempt, wait_random_exponential
from langchain_community.document_loaders.pdf import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.chains.llm import LLMChain
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
import fitz  # PyMuPDF for handling PDFs with images

class SummaryService():  
    def __init__(self):
        super().__init__()
    
    def init_chain(self):
        prompt_template = """Write a detailed summary of the following:
        "{text}"
        DETAILED SUMMARY:"""
        prompt = PromptTemplate.from_template(prompt_template)
        llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-16k",
                         openai_api_key=settings.OPENAI_API_KEY)
        llm_chain = LLMChain(llm=llm, prompt=prompt)
        return llm_chain
  
    def get_chat_completion_client(self):
        return ChatCompletion(api_key=self.openai_api_key)

    @retry(wait=wait_random_exponential(min=1, max=60),
           stop=stop_after_attempt(6))
    def completion_with_backoff(self, **kwargs):
        client = self.get_chat_completion_client()
        return client.create(**kwargs)


    def apply_ocr_to_images(self, doc):
        """Extract text from images in the PDF using OCR."""
        text = ""
        for page in doc:
            image_list = page.get_images(full=True)
            for img in image_list:
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image = Image.open(BytesIO(image_bytes))
                text += pytesseract.image_to_string(image)
        return text

    def summarize_pdf(self, pdf_file_path: str):
        """Returns a summarized version of the PDF file located at pdf_file_path."""
        try:
            doc = fitz.open(pdf_file_path)
        except Exception as e:
            raise ValueError(f"Failed to open PDF file at path {pdf_file_path}: {str(e)}")

        text = ""
        for page in doc:
            text += page.get_text()

        # If no text is found, apply OCR to extract text from images
        if not text.strip():
            text = self.apply_ocr_to_images(doc)

        if not text.strip():
            return "The PDF contains images but no text could be extracted."

        # Summarize Text
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=100)
        documents = text_splitter.create_documents([text])

        llm_chain = self.init_chain()
        stuff_chain = StuffDocumentsChain(llm_chain=llm_chain, document_variable_name="text")

        summaries = []
        for doc in documents:
            inputs = {"input_documents": [doc]}
            result = stuff_chain.invoke(inputs)
            summary = result.get("output_text", "")
            summaries.append(summary)

        final_summary = " ".join(summaries)
        final_summary = final_summary.replace('\n', ' ').replace('\r', ' ').strip()
        return final_summary
    
summary_service = SummaryService()